import Link from "next/link";
import {
  Badge,
  ButtonLink,
  EmptyState,
  PageHeader,
  StatTile,
  Table,
  Td,
  Th,
} from "@/components/admin/ui";
import { requireSession } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { Payment } from "@/lib/models/Payment";
import { Enquiry } from "@/lib/models/Enquiry";
import { computeDues, formatMonthKey } from "@/lib/dues";
import { duesPaidByMember, getOverview } from "@/lib/reporting";
import {
  KIND_LABEL,
  MEMBERSHIP_TARGET,
  TOTAL_SLOT_POOL,
} from "@/lib/constants";
import { formatNaira, formatNairaCompact, formatNumber } from "@/lib/money";

export default async function AdminOverviewPage() {
  const session = await requireSession();
  await connectDb();

  const overview = await getOverview();

  const newEnquiries = can(session.role, "enquiries:read")
    ? await Enquiry.countDocuments({ status: "new" })
    : 0;

  const [recentPayments, accruingMembers] = await Promise.all([
    Payment.find()
      .sort({ receivedOn: -1, createdAt: -1 })
      .limit(8)
      .populate<{ member: { membershipNumber: string; firstName: string; lastName: string } }>(
        "member",
        "membershipNumber firstName lastName",
      )
      .lean(),
    Member.find({ status: { $in: ["active", "suspended"] } })
      .select("membershipNumber firstName lastName tier status joinedOn")
      .lean(),
  ]);

  const duesPaid = await duesPaidByMember();

  const inArrears = accruingMembers
    .map((member) => ({
      member,
      position: computeDues(
        { tier: member.tier, status: member.status, joinedOn: member.joinedOn },
        duesPaid.get(String(member._id)) ?? 0,
      ),
    }))
    .filter((row) => row.position.arrearsKobo > 0)
    .sort((a, b) => b.position.arrearsKobo - a.position.arrearsKobo)
    .slice(0, 8);

  return (
    <>
      <PageHeader
        title={`Good day, ${session.name.split(" ")[0]}`}
        description="Position of the Society's register and collections as at today."
        action={
          can(session.role, "payments:write") ? (
            <ButtonLink href="/admin/payments/new" variant="gold">
              Record Payment
            </ButtonLink>
          ) : undefined
        }
      />

      <section aria-label="Key figures">
        <div className="grid gap-x-10 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile
            label="Active members"
            value={formatNumber(overview.activeMembers)}
            progress={overview.membershipPercent}
            detail={`${overview.membershipPercent.toFixed(0)}% of the ${MEMBERSHIP_TARGET}-member target`}
          />
          <StatTile
            label="Slots allocated"
            value={formatNumber(overview.slotsAllocated)}
            progress={overview.slotPoolPercent}
            detail={`of ${formatNumber(TOTAL_SLOT_POOL)} in the pool`}
          />
          <StatTile
            label="Slot value allocated"
            value={formatNairaCompact(overview.slotValueKobo)}
            progress={overview.capitalPercent}
            detail={`${overview.capitalPercent.toFixed(1)}% of the ₦5.0bn target`}
          />
          <StatTile
            label="Total received"
            value={formatNairaCompact(overview.receivedTotalKobo)}
            detail="All payments recorded to date"
          />
        </div>

        <div className="mt-4 grid gap-x-10 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile
            label="Registration fees"
            value={formatNairaCompact(overview.registrationReceivedKobo)}
            detail="Received to date"
          />
          <StatTile
            label="Dues this month"
            value={formatNairaCompact(overview.duesThisMonthKobo)}
            detail={formatMonthKey(currentMonth())}
          />
          <StatTile
            label="Outstanding dues"
            value={formatNairaCompact(overview.totalArrearsKobo)}
            detail={`${overview.membersInArrears} member${overview.membersInArrears === 1 ? "" : "s"} in arrears`}
          />
          <StatTile
            label="New enquiries"
            value={formatNumber(newEnquiries)}
            detail={
              newEnquiries > 0
                ? "Awaiting review in Enquiries"
                : `${formatNumber(overview.totalMembers)} on the register`
            }
          />
        </div>
      </section>

      <div className="mt-16 grid gap-12 xl:grid-cols-2 xl:gap-10">
        <section aria-labelledby="arrears-heading">
          <div className="mb-5 flex items-baseline justify-between gap-4">
            <h2
              id="arrears-heading"
              className="font-display text-[1.25rem] text-forest-900"
            >
              Members in arrears
            </h2>
            <Link
              href="/admin/members?arrears=1"
              className="label-sm text-gold-700 underline-offset-4 hover:underline"
            >
              View all
            </Link>
          </div>

          {inArrears.length === 0 ? (
            <EmptyState
              title="No arrears"
              body="Every accruing member is up to date on monthly dues."
            />
          ) : (
            <Table>
              <thead>
                <tr>
                  <Th>Member</Th>
                  <Th>Months</Th>
                  <Th align="right">Outstanding</Th>
                </tr>
              </thead>
              <tbody>
                {inArrears.map(({ member, position }) => (
                  <tr key={String(member._id)}>
                    <Td>
                      <Link
                        href={`/admin/members/${String(member._id)}`}
                        className="text-forest-900 underline-offset-4 hover:underline"
                      >
                        {member.firstName} {member.lastName}
                      </Link>
                      <span className="label-sm mt-1 block text-ink-faint">
                        {member.membershipNumber}
                      </span>
                    </Td>
                    <Td>
                      <span className="tnum">{position.monthsBilled}</span>
                      {member.status === "suspended" ? (
                        <span className="mt-1 block">
                          <Badge tone="alert">Suspended</Badge>
                        </span>
                      ) : null}
                    </Td>
                    <Td align="right">
                      <span className="tnum text-alert">
                        {formatNaira(position.arrearsKobo)}
                      </span>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </section>

        <section aria-labelledby="recent-heading">
          <div className="mb-5 flex items-baseline justify-between gap-4">
            <h2
              id="recent-heading"
              className="font-display text-[1.25rem] text-forest-900"
            >
              Recent payments
            </h2>
            <Link
              href="/admin/payments"
              className="label-sm text-gold-700 underline-offset-4 hover:underline"
            >
              View ledger
            </Link>
          </div>

          {recentPayments.length === 0 ? (
            <EmptyState
              title="No payments yet"
              body="Recorded receipts will appear here as they are entered."
              action={
                can(session.role, "payments:write") ? (
                  <ButtonLink href="/admin/payments/new" variant="ghost">
                    Record the first payment
                  </ButtonLink>
                ) : undefined
              }
            />
          ) : (
            <Table>
              <thead>
                <tr>
                  <Th>Member</Th>
                  <Th>Type</Th>
                  <Th align="right">Amount</Th>
                </tr>
              </thead>
              <tbody>
                {recentPayments.map((payment) => (
                  <tr key={String(payment._id)}>
                    <Td>
                      {payment.member ? (
                        <>
                          {payment.member.firstName} {payment.member.lastName}
                          <span className="label-sm mt-1 block text-ink-faint">
                            {payment.member.membershipNumber}
                          </span>
                        </>
                      ) : (
                        <span className="text-ink-faint">Member removed</span>
                      )}
                    </Td>
                    <Td>
                      {KIND_LABEL[payment.kind]}
                      <span className="label-sm mt-1 block text-ink-faint">
                        {payment.receivedOn.toLocaleDateString("en-NG", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </span>
                    </Td>
                    <Td align="right">
                      <span className="tnum">
                        {formatNaira(payment.amountKobo)}
                      </span>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </section>
      </div>
    </>
  );
}

function currentMonth(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}
