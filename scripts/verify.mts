/* Temporary end-to-end check of the admin data layer against a real mongod. */
import assert from "node:assert/strict";
import { MongoMemoryServer } from "mongodb-memory-server";

let passed = 0;
async function check(name: string, fn: () => void | Promise<void>) {
  try {
    await fn();
    passed += 1;
    console.log(`  ok   ${name}`);
  } catch (error) {
    console.error(`  FAIL ${name}`);
    console.error(`       ${error instanceof Error ? error.message : error}`);
    process.exitCode = 1;
  }
}

const mongo = await MongoMemoryServer.create();
process.env.MONGODB_URI = mongo.getUri("anchor_test");
process.env.SESSION_SECRET = "test-secret-that-is-long-enough-000000";

const mongoose = (await import("mongoose")).default;
const { connectDb } = await import("../src/lib/db");
const { Member } = await import("../src/lib/models/Member");
const { Payment } = await import("../src/lib/models/Payment");
const { AdminUser } = await import("../src/lib/models/AdminUser");
const { nextMembershipNumber } = await import("../src/lib/models/Counter");
const { computeDues, monthsBilledBetween } = await import("../src/lib/dues");
const { getOverview, slotsAllocatedExcluding } = await import("../src/lib/reporting");
const { memberSchema, paymentSchema } = await import("../src/lib/validation");
const { parseNairaToKobo, formatNaira } = await import("../src/lib/money");
const { signSession, verifySession } = await import("../src/lib/session");
const { can } = await import("../src/lib/rbac");

await connectDb();
await Member.syncIndexes();
await Payment.syncIndexes();
await AdminUser.syncIndexes();

console.log("\nmoney");
await check("parses plain naira", () => assert.equal(parseNairaToKobo("20,000"), 2_000_000));
await check("parses kobo fraction", () => assert.equal(parseNairaToKobo("₦10,000.50"), 1_000_050));
await check("rejects junk", () => assert.equal(parseNairaToKobo("abc"), null));
await check("rejects negative", () => assert.equal(parseNairaToKobo("-5"), null));
await check("rejects three decimal places", () => assert.equal(parseNairaToKobo("1.005"), null));
await check("formats whole naira", () => assert.equal(formatNaira(2_000_000), "₦20,000"));
await check("formats stray kobo", () => assert.equal(formatNaira(1_000_050), "₦10,000.50"));

console.log("\nvalidation");
const baseMember = {
  firstName: "Ada",
  lastName: "Okoro",
  otherNames: "",
  email: "ada@example.org",
  phone: "+234 802 000 0000",
  address: "",
  status: "active",
  joinedOn: "2026-06-15",
  notes: "",
};
await check("rejects investor below the 100-slot floor", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "investor", slots: "50" });
  assert.equal(result.success, false);
});
await check("rejects non-investor holding slots", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "non_investor", slots: "100" });
  assert.equal(result.success, false);
});
await check("rejects a holding above the 1% ceiling", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "investor", slots: "10001" });
  assert.equal(result.success, false);
});
await check("accepts a valid investor", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "investor", slots: "100" });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
});
await check("requires a dues month on dues payments", () => {
  const result = paymentSchema.safeParse({
    memberId: "x", kind: "dues", amount: "10000", duesPeriod: "",
    method: "cash", bank: "", reference: "", receivedOn: "2026-09-01", note: "",
  });
  assert.equal(result.success, false);
});

console.log("\nmembership numbers");
await check("allocates 20 concurrent numbers with no collision", async () => {
  const numbers = await Promise.all(
    Array.from({ length: 20 }, () => nextMembershipNumber(2026)),
  );
  assert.equal(new Set(numbers).size, 20);
  assert.match(numbers[0], /^ARG-2026-\d{4}$/);
});

console.log("\nregister and ledger");
const memberOne = await Member.create({
  membershipNumber: await nextMembershipNumber(2026),
  firstName: "Ada", lastName: "Okoro", email: "ada@example.org",
  phone: "+2348020000000", tier: "investor", slots: 200,
  status: "active", joinedOn: new Date("2026-06-15T00:00:00Z"),
});
const memberTwo = await Member.create({
  membershipNumber: await nextMembershipNumber(2026),
  firstName: "Bode", lastName: "Ade", email: "bode@example.org",
  phone: "+2348030000000", tier: "non_investor", slots: 0,
  status: "active", joinedOn: new Date("2026-08-01T00:00:00Z"),
});

await check("rejects a duplicate member email", async () => {
  await assert.rejects(() =>
    Member.create({
      membershipNumber: "ARG-2026-9999", firstName: "Dup", lastName: "Licate",
      email: "ada@example.org", phone: "+2348040000000", tier: "investor",
      slots: 100, status: "active", joinedOn: new Date(),
    }),
  );
});

await Payment.create({
  member: memberOne._id, kind: "registration", amountKobo: 2_000_000,
  method: "bank_transfer", bank: "GTBank", receivedOn: new Date("2026-06-20T00:00:00Z"),
  recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
});
await Payment.create({
  member: memberOne._id, kind: "dues", amountKobo: 1_000_000, duesPeriod: "2026-06",
  method: "cash", receivedOn: new Date("2026-06-20T00:00:00Z"),
  recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
});

await check("blocks a duplicate dues month for the same member", async () => {
  await assert.rejects(
    () =>
      Payment.create({
        member: memberOne._id, kind: "dues", amountKobo: 1_000_000, duesPeriod: "2026-06",
        method: "cash", receivedOn: new Date(),
        recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
      }),
    /E11000|duplicate/i,
  );
});

await check("allows the same dues month for a different member", async () => {
  await Payment.create({
    member: memberTwo._id, kind: "dues", amountKobo: 5_000_000, duesPeriod: "2026-06",
    method: "cash", receivedOn: new Date(),
    recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
  });
});

await check("allows several non-dues payments with no period", async () => {
  await Payment.create({
    member: memberOne._id, kind: "other", amountKobo: 500_000, method: "cash",
    receivedOn: new Date(), recordedBy: new mongoose.Types.ObjectId(), recordedByName: "T",
  });
  await Payment.create({
    member: memberOne._id, kind: "other", amountKobo: 700_000, method: "cash",
    receivedOn: new Date(), recordedBy: new mongoose.Types.ObjectId(), recordedByName: "T",
  });
});

console.log("\ndues");
await check("counts both endpoint months", () => {
  assert.equal(
    monthsBilledBetween(new Date("2026-06-15T00:00:00Z"), new Date("2026-09-07T00:00:00Z")),
    4,
  );
});
await check("computes arrears for an investor", () => {
  const position = computeDues(
    { tier: "investor", status: "active", joinedOn: new Date("2026-06-15T00:00:00Z") },
    1_000_000,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.monthsBilled, 4);
  assert.equal(position.expectedKobo, 4_000_000);
  assert.equal(position.arrearsKobo, 3_000_000);
  assert.equal(position.creditKobo, 0);
});
await check("shows overpayment as credit, never negative arrears", () => {
  const position = computeDues(
    { tier: "investor", status: "active", joinedOn: new Date("2026-09-01T00:00:00Z") },
    5_000_000,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.arrearsKobo, 0);
  assert.equal(position.creditKobo, 4_000_000);
});
await check("does not accrue for pending members", () => {
  const position = computeDues(
    { tier: "investor", status: "pending", joinedOn: new Date("2026-01-01T00:00:00Z") },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.expectedKobo, 0);
  assert.equal(position.accruing, false);
});
await check("keeps accruing while suspended", () => {
  const position = computeDues(
    { tier: "non_investor", status: "suspended", joinedOn: new Date("2026-08-01T00:00:00Z") },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.monthsBilled, 2);
  assert.equal(position.expectedKobo, 10_000_000);
});

console.log("\npool and overview");
await check("counts allocated slots and can exclude one member", async () => {
  assert.equal(await slotsAllocatedExcluding(), 200);
  assert.equal(await slotsAllocatedExcluding(String(memberOne._id)), 0);
});
await check("aggregates the overview", async () => {
  const overview = await getOverview();
  assert.equal(overview.totalMembers, 2);
  assert.equal(overview.activeMembers, 2);
  assert.equal(overview.slotsAllocated, 200);
  assert.equal(overview.slotValueKobo, 200 * 500_000);
  assert.equal(overview.registrationReceivedKobo, 2_000_000);
  assert.equal(
    overview.receivedTotalKobo,
    2_000_000 + 1_000_000 + 5_000_000 + 500_000 + 700_000,
  );
  assert.ok(overview.totalArrearsKobo > 0, "expected some arrears");
});

console.log("\nsessions and rbac");
await check("round-trips a signed session", async () => {
  const token = await signSession({
    sub: "abc", name: "Ada", email: "a@b.c", role: "treasurer",
  });
  const back = await verifySession(token);
  assert.equal(back?.role, "treasurer");
});
await check("rejects a tampered token", async () => {
  const token = await signSession({
    sub: "abc", name: "Ada", email: "a@b.c", role: "viewer",
  });
  assert.equal(await verifySession(`${token.slice(0, -3)}aaa`), null);
});
await check("enforces the role matrix", () => {
  assert.equal(can("viewer", "payments:write"), false);
  assert.equal(can("financial_secretary", "payments:write"), true);
  assert.equal(can("financial_secretary", "members:write"), false);
  assert.equal(can("secretary", "members:write"), true);
  assert.equal(can("secretary", "payments:write"), false);
  assert.equal(can("treasurer", "users:manage"), false);
  assert.equal(can("admin", "users:manage"), true);
});

console.log("\nenquiries");
const { Enquiry, nextEnquiryReference } = await import("../src/lib/models/Enquiry");
const { enquirySchema } = await import("../src/lib/validation");
await Enquiry.syncIndexes();

await check("rejects a slot figure below the band", () => {
  const result = enquirySchema.safeParse({
    firstName: "Ada", lastName: "Okoro", email: "a@b.co", phone: "+2348020000000",
    address: "", occupation: "", tierInterest: "investor", slotsInterest: "10",
    heardFrom: "", message: "",
  });
  assert.equal(result.success, false);
});
await check("accepts an enquiry with no slot figure", () => {
  const result = enquirySchema.safeParse({
    firstName: "Ada", lastName: "Okoro", email: "a@b.co", phone: "+2348020000000",
    address: "", occupation: "", tierInterest: "undecided", slotsInterest: "",
    heardFrom: "", message: "",
  });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
});
await check("allocates sequential enquiry references", async () => {
  const refs = await Promise.all(
    Array.from({ length: 5 }, () => nextEnquiryReference(2026)),
  );
  assert.equal(new Set(refs).size, 5);
  assert.match(refs[0], /^ARG-INT-2026-\d{4}$/);
});

console.log("\noutbound mail (real SMTP)");
const { SMTPServer } = await import("smtp-server");
const { sendEnquiryMail, resetMailTransport, applicantReceipt, escapeHtml } =
  await import("../src/lib/mail");

type Captured = { from: string; to: string[]; body: string };
const captured: Captured[] = [];

const smtp = new SMTPServer({
  authOptional: true,
  disabledCommands: ["STARTTLS", "AUTH"],
  onData(stream, session, callback) {
    const chunks: Buffer[] = [];
    stream.on("data", (chunk: Buffer) => chunks.push(chunk));
    stream.on("end", () => {
      captured.push({
        from: session.envelope.mailFrom ? session.envelope.mailFrom.address : "",
        to: session.envelope.rcptTo.map((r) => r.address),
        body: Buffer.concat(chunks).toString("utf8"),
      });
      callback();
    });
  },
});

// Port 0 asks the OS for a free one, so this never collides with a dev sink
// that happens to be running.
await new Promise<void>((resolve) => smtp.listen(0, "127.0.0.1", resolve));
const address = smtp.server.address();
const smtpPort =
  typeof address === "object" && address !== null ? address.port : 0;
assert.ok(smtpPort > 0, "SMTP test server did not bind a port");

process.env.SMTP_HOST = "127.0.0.1";
process.env.SMTP_PORT = String(smtpPort);
process.env.SMTP_SECURE = "false";
delete process.env.SMTP_USER;
process.env.MAIL_FROM = "Anchor Secretariat <secretariat@anchor.test>";
process.env.SECRETARIAT_EMAIL = "office@anchor.test";
process.env.NEXT_PUBLIC_SITE_URL = "https://anchor.test";
resetMailTransport();

const enquiryDoc = await Enquiry.create({
  reference: await nextEnquiryReference(2026),
  firstName: "Chidi", lastName: "Eze", email: "chidi@applicant.test",
  phone: "+2348090000000", tierInterest: "investor", slotsInterest: 400,
  occupation: "Architect", status: "new",
});

const outcome = await sendEnquiryMail(enquiryDoc.toObject());

await check("reports both messages sent", () => {
  assert.equal(outcome.applicant, "sent", outcome.error);
  assert.equal(outcome.secretariat, "sent", outcome.error);
});
await check("delivers exactly two messages", () => {
  assert.equal(captured.length, 2);
});
await check("addresses the applicant receipt correctly", () => {
  const mail = captured.find((m) => m.to.includes("chidi@applicant.test"));
  assert.ok(mail, "no message addressed to the applicant");
  assert.equal(mail.from, "secretariat@anchor.test");
  assert.match(mail.body, /Subject: .*ARG-INT-2026/);
  assert.match(mail.body, /Chidi/);
});
await check("notifies the Secretariat with a review link", () => {
  const mail = captured.find((m) => m.to.includes("office@anchor.test"));
  assert.ok(mail, "no message addressed to the Secretariat");
  assert.match(mail.body, /Chidi/);
  assert.match(mail.body, /anchor\.test/);
});
await check("quotes the slot holding in naira", () => {
  const body = captured.map((m) => m.body).join("");
  // 400 slots x ₦5,000 = ₦2,000,000; quoted-printable may split long lines.
  assert.match(body.replace(/=\r?\n/g, ""), /2,000,000/);
});
await check("escapes applicant-supplied HTML", () => {
  const mail = applicantReceipt({
    ...enquiryDoc.toObject(),
    firstName: '<script>alert(1)</script>',
  });
  assert.ok(!mail.html.includes("<script>"), "raw script tag reached the HTML body");
  assert.equal(escapeHtml('<b>&"'), "&lt;b&gt;&amp;&quot;");
});
await check("skips sending when SMTP is not configured", async () => {
  const host = process.env.SMTP_HOST;
  delete process.env.SMTP_HOST;
  resetMailTransport();
  const skipped = await sendEnquiryMail(enquiryDoc.toObject());
  assert.equal(skipped.applicant, "skipped");
  assert.equal(skipped.secretariat, "skipped");
  process.env.SMTP_HOST = host;
  resetMailTransport();
});

await new Promise<void>((resolve) => smtp.close(() => resolve()));

console.log(
  `\n${passed} checks passed${process.exitCode ? " (with failures above)" : ""}\n`,
);

await mongoose.disconnect();
await mongo.stop();
process.exit(process.exitCode ?? 0);
