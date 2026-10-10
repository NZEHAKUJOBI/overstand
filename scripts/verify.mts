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
process.env.MONGODB_URI = mongo.getUri("overstand_test");
process.env.SESSION_SECRET = "test-secret-that-is-long-enough-000000";

const mongoose = (await import("mongoose")).default;
const { connectDb } = await import("../src/lib/db");
const { Member } = await import("../src/lib/models/Member");
const { Payment } = await import("../src/lib/models/Payment");
const { AdminUser } = await import("../src/lib/models/AdminUser");
const { nextMembershipNumber } = await import("../src/lib/models/Counter");
const { computeContribution, monthsBilledBetween } = await import("../src/lib/contributions");
const { getOverview } = await import("../src/lib/reporting");
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
  dateOfBirth: "1990-04-02",
  occupation: "",
  nextOfKin: {
    name: "Ngozi Okoro",
    relationship: "Sister",
    phone: "+234 805 000 0000",
    email: "",
    address: "",
  },
  status: "active",
  joinedOn: "2026-06-15",
  notes: "",
};
await check("accepts a Tier 1 member", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "tier_1" });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
});
await check("accepts a Tier 2 member", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "tier_2" });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
});
await check("requires an amount on the tailored tier", () => {
  const result = memberSchema.safeParse({ ...baseMember, tier: "custom" });
  assert.equal(result.success, false);
});
await check("rejects a tailored amount at or below Tier 2", () => {
  const result = memberSchema.safeParse({
    ...baseMember,
    tier: "custom",
    customContribution: "50,000",
  });
  assert.equal(result.success, false);
});
await check("accepts a tailored amount above Tier 2", () => {
  const result = memberSchema.safeParse({
    ...baseMember,
    tier: "custom",
    customContribution: "75,000",
  });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
  assert.equal(result.data?.customContributionKobo, 7_500_000);
});
await check("rejects an applicant under 18", () => {
  const result = memberSchema.safeParse({
    ...baseMember,
    tier: "tier_1",
    dateOfBirth: new Date().toISOString().slice(0, 10),
  });
  assert.equal(result.success, false);
});
await check("requires next-of-kin contact details", () => {
  const result = memberSchema.safeParse({
    ...baseMember,
    tier: "tier_1",
    nextOfKin: { name: "", relationship: "", phone: "", email: "", address: "" },
  });
  assert.equal(result.success, false);
});
await check("requires a contribution month on contribution payments", () => {
  const result = paymentSchema.safeParse({
    memberId: "x", kind: "contribution", amount: "10000", contributionPeriod: "",
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
  assert.match(numbers[0], /^OMCS-2026-\d{4}$/);
});

console.log("\nregister and ledger");
const kin = {
  name: "Ngozi Okoro", relationship: "Sister", phone: "+2348050000000",
};
const memberOne = await Member.create({
  membershipNumber: await nextMembershipNumber(2026),
  firstName: "Ada", lastName: "Okoro", email: "ada@example.org",
  phone: "+2348020000000", tier: "tier_1", nextOfKin: kin,
  status: "active", joinedOn: new Date("2026-06-15T00:00:00Z"),
});
const memberTwo = await Member.create({
  membershipNumber: await nextMembershipNumber(2026),
  firstName: "Bode", lastName: "Ade", email: "bode@example.org",
  phone: "+2348030000000", tier: "tier_2", nextOfKin: kin,
  status: "active", joinedOn: new Date("2026-08-01T00:00:00Z"),
});

await check("rejects a member with no next of kin", async () => {
  await assert.rejects(() =>
    Member.create({
      membershipNumber: "OMCS-2026-9998", firstName: "No", lastName: "Kin",
      email: "nokin@example.org", phone: "+2348060000000", tier: "tier_1",
      status: "active", joinedOn: new Date(),
    }),
  );
});

await check("rejects a duplicate member email", async () => {
  await assert.rejects(() =>
    Member.create({
      membershipNumber: "OMCS-2026-9999", firstName: "Dup", lastName: "Licate",
      email: "ada@example.org", phone: "+2348040000000", tier: "tier_1",
      nextOfKin: kin, status: "active", joinedOn: new Date(),
    }),
  );
});

await Payment.create({
  member: memberOne._id, kind: "application", amountKobo: 2_000_000,
  method: "bank_transfer", bank: "GTBank", receivedOn: new Date("2026-06-20T00:00:00Z"),
  recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
});
await Payment.create({
  member: memberOne._id, kind: "contribution", amountKobo: 2_500_000, contributionPeriod: "2026-06",
  method: "cash", receivedOn: new Date("2026-06-20T00:00:00Z"),
  recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
});

await check("blocks a duplicate contribution month for the same member", async () => {
  await assert.rejects(
    () =>
      Payment.create({
        member: memberOne._id, kind: "contribution", amountKobo: 2_500_000, contributionPeriod: "2026-06",
        method: "cash", receivedOn: new Date(),
        recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
      }),
    /E11000|duplicate/i,
  );
});

await check("allows the same contribution month for a different member", async () => {
  await Payment.create({
    member: memberTwo._id, kind: "contribution", amountKobo: 5_000_000, contributionPeriod: "2026-06",
    method: "cash", receivedOn: new Date(),
    recordedBy: new mongoose.Types.ObjectId(), recordedByName: "Treasurer",
  });
});

await check("allows several non-contribution payments with no period", async () => {
  await Payment.create({
    member: memberOne._id, kind: "other", amountKobo: 500_000, method: "cash",
    receivedOn: new Date(), recordedBy: new mongoose.Types.ObjectId(), recordedByName: "T",
  });
  await Payment.create({
    member: memberOne._id, kind: "other", amountKobo: 700_000, method: "cash",
    receivedOn: new Date(), recordedBy: new mongoose.Types.ObjectId(), recordedByName: "T",
  });
});

console.log("\ncontribution");
await check("counts both endpoint months", () => {
  assert.equal(
    monthsBilledBetween(new Date("2026-06-15T00:00:00Z"), new Date("2026-09-07T00:00:00Z")),
    4,
  );
});
await check("computes arrears on Tier 1", () => {
  const position = computeContribution(
    { tier: "tier_1", status: "active", joinedOn: new Date("2026-06-15T00:00:00Z") },
    2_500_000,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.monthsBilled, 4);
  assert.equal(position.rateKobo, 2_500_000);
  assert.equal(position.expectedKobo, 10_000_000);
  assert.equal(position.arrearsKobo, 7_500_000);
  assert.equal(position.creditKobo, 0);
});
await check("accrues a tailored member at their own agreed rate", () => {
  const position = computeContribution(
    {
      tier: "custom",
      status: "active",
      joinedOn: new Date("2026-08-01T00:00:00Z"),
      customContributionKobo: 7_500_000,
    },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.rateKobo, 7_500_000);
  assert.equal(position.expectedKobo, 15_000_000);
});
await check("falls back to the Tier 2 floor when a tailored rate is missing", () => {
  const position = computeContribution(
    { tier: "custom", status: "active", joinedOn: new Date("2026-09-01T00:00:00Z") },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.rateKobo, 5_000_000);
});
await check("shows overpayment as credit, never negative arrears", () => {
  const position = computeContribution(
    { tier: "tier_1", status: "active", joinedOn: new Date("2026-09-01T00:00:00Z") },
    5_000_000,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.arrearsKobo, 0);
  assert.equal(position.creditKobo, 2_500_000);
});
await check("does not accrue for pending members", () => {
  const position = computeContribution(
    { tier: "tier_1", status: "pending", joinedOn: new Date("2026-01-01T00:00:00Z") },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.expectedKobo, 0);
  assert.equal(position.accruing, false);
});
await check("keeps accruing while suspended", () => {
  const position = computeContribution(
    { tier: "tier_2", status: "suspended", joinedOn: new Date("2026-08-01T00:00:00Z") },
    0,
    new Date("2026-09-07T00:00:00Z"),
  );
  assert.equal(position.monthsBilled, 2);
  assert.equal(position.expectedKobo, 10_000_000);
});

console.log("\noverview");
await check("aggregates the overview", async () => {
  const overview = await getOverview();
  assert.equal(overview.totalMembers, 2);
  assert.equal(overview.activeMembers, 2);
  assert.equal(overview.membersByTier.tier_1, 1);
  assert.equal(overview.membersByTier.tier_2, 1);
  // One Tier 1 member at ₦25,000 plus one Tier 2 at ₦50,000.
  assert.equal(overview.monthlyCommitmentKobo, 7_500_000);
  assert.equal(overview.applicationReceivedKobo, 2_000_000);
  assert.equal(
    overview.receivedTotalKobo,
    2_000_000 + 2_500_000 + 5_000_000 + 500_000 + 700_000,
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

console.log("\napplications");
const { Application, nextApplicationReference } = await import("../src/lib/models/Application");
const { applicationSchema } = await import("../src/lib/validation");
await Application.syncIndexes();

const baseApplication = {
  firstName: "Ada", lastName: "Okoro", otherNames: "",
  email: "a@b.co", phone: "+2348020000000",
  address: "", dateOfBirth: "1990-04-02", occupation: "",
  nextOfKin: {
    name: "Ngozi Okoro", relationship: "Sister", phone: "+2348050000000",
    email: "", address: "",
  },
  eligibilityConfirmed: "on",
  heardFrom: "", message: "",
};

await check("accepts a Tier 1 application", () => {
  const result = applicationSchema.safeParse({
    ...baseApplication, tierInterest: "tier_1", customContribution: "",
  });
  assert.equal(result.success, true, JSON.stringify(result.error?.issues));
});
await check("rejects a tailored application at or below Tier 2", () => {
  const result = applicationSchema.safeParse({
    ...baseApplication, tierInterest: "custom", customContribution: "40,000",
  });
  assert.equal(result.success, false);
});
await check("rejects an application from someone under 18", () => {
  const result = applicationSchema.safeParse({
    ...baseApplication,
    tierInterest: "tier_1",
    customContribution: "",
    dateOfBirth: new Date().toISOString().slice(0, 10),
  });
  assert.equal(result.success, false);
});
await check("rejects an application with the declaration unticked", () => {
  const result = applicationSchema.safeParse({
    ...baseApplication,
    tierInterest: "tier_1",
    customContribution: "",
    eligibilityConfirmed: null,
  });
  assert.equal(result.success, false);
});
await check("rejects an application with no next of kin", () => {
  const result = applicationSchema.safeParse({
    ...baseApplication,
    tierInterest: "tier_1",
    customContribution: "",
    nextOfKin: { name: "", relationship: "", phone: "", email: "", address: "" },
  });
  assert.equal(result.success, false);
});
await check("allocates sequential application references", async () => {
  const refs = await Promise.all(
    Array.from({ length: 5 }, () => nextApplicationReference(2026)),
  );
  assert.equal(new Set(refs).size, 5);
  assert.match(refs[0], /^OMCS-APP-2026-\d{4}$/);
});

console.log("\noutbound mail (real SMTP)");
const { SMTPServer } = await import("smtp-server");
const { sendApplicationMail, resetMailTransport, applicantReceipt, escapeHtml } =
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
process.env.MAIL_FROM = "Overstand Secretariat <secretariat@overstand.test>";
process.env.SECRETARIAT_EMAIL = "office@overstand.test";
process.env.NEXT_PUBLIC_SITE_URL = "https://overstand.test";
resetMailTransport();

const applicationDoc = await Application.create({
  reference: await nextApplicationReference(2026),
  firstName: "Chidi", lastName: "Eze", email: "chidi@applicant.test",
  phone: "+2348090000000", tierInterest: "custom", customContributionKobo: 7_500_000,
  dateOfBirth: new Date("1992-03-11T00:00:00Z"),
  nextOfKin: {
    name: "Ijeoma Eze", relationship: "Spouse", phone: "+2348091111111",
  },
  eligibilityConfirmed: true,
  occupation: "Architect", status: "new",
});

const outcome = await sendApplicationMail(applicationDoc.toObject());

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
  assert.equal(mail.from, "secretariat@overstand.test");
  assert.match(mail.body, /Subject: .*OMCS-APP-2026/);
  assert.match(mail.body, /Chidi/);
});
await check("notifies the Secretariat with a review link", () => {
  const mail = captured.find((m) => m.to.includes("office@overstand.test"));
  assert.ok(mail, "no message addressed to the Secretariat");
  assert.match(mail.body, /Chidi/);
  assert.match(mail.body, /overstand.test/);
});
await check("quotes the agreed monthly contribution in naira", () => {
  const body = captured.map((m) => m.body).join("");
  // Quoted-printable may split long lines, so unfold before matching.
  assert.match(body.replace(/=\r?\n/g, ""), /75,000/);
});
await check("carries the next of kin into the Secretariat notice", () => {
  const mail = captured.find((m) => m.to.includes("office@overstand.test"));
  assert.ok(mail, "no message addressed to the Secretariat");
  assert.match(mail.body.replace(/=\r?\n/g, ""), /Ijeoma Eze/);
});
await check("escapes applicant-supplied HTML", () => {
  const mail = applicantReceipt({
    ...applicationDoc.toObject(),
    firstName: '<script>alert(1)</script>',
  });
  assert.ok(!mail.html.includes("<script>"), "raw script tag reached the HTML body");
  assert.equal(escapeHtml('<b>&"'), "&lt;b&gt;&amp;&quot;");
});
await check("skips sending when SMTP is not configured", async () => {
  const host = process.env.SMTP_HOST;
  delete process.env.SMTP_HOST;
  resetMailTransport();
  const skipped = await sendApplicationMail(applicationDoc.toObject());
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
