import Link from "next/link";
import { notFound } from "next/navigation";
import { isValidObjectId } from "mongoose";
import {
  Badge,
  ButtonLink,
  DescriptionItem,
  DescriptionList,
  EmptyState,
  Notice,
  PageHeader,
  StatTile,
  Table,
  Td,
  Th,
} from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { Payment } from "@/lib/models/Payment";
import { computeContribution, formatMonthKey } from "@/lib/contributions";
import {
  KIND_LABEL,
  METHOD_LABEL,
  STATUS_LABEL,
  TIER_LABEL,
  type MemberStatus,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";

const STATUS_TONE: Record<MemberStatus, "ok" | "warn" | "alert" | "neutral"> = {
  active: "ok",
  pending: "warn",
  suspended: "alert",
  exited: "neutral",
};

const dateFormat: Intl.DateTimeFormatOptions = {
  day: "2-digit",
  month: "short",
  year: "numeric",
};

export default async function MemberDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ saved?: string }>;
}) {
  const session = await requirePermission("members:read");
  const { id } = await params;
  const { saved } = await searchParams;

  if (!isValidObjectId(id)) notFound();

  await connectDb();

  const member = await Member.findById(id).lean();
  if (!member) notFound();

  const payments = await Payment.find({ member: id })
    .sort({ receivedOn: -1, createdAt: -1 })
    .lean();

  const contributionPaidKobo = payments
    .filter((payment) => payment.kind === "contribution")
    .reduce((sum, payment) => sum + payment.amountKobo, 0);

  const position = computeContribution(member, contributionPaidKobo);

  const totalReceived = payments.reduce(
    (sum, payment) => sum + payment.amountKobo,
    0,
  );
  const registrationPaid = payments.some(
    (payment) => payment.kind === "registration",
  );

  return (
    <>
      <PageHeader
        title={`${member.firstName} ${member.lastName}`}
        description={`${member.membershipNumber} · ${TIER_LABEL[member.tier]}`}
        action={
          <div className="flex flex-wrap gap-3">
            {can(session.role, "payments:write") ? (
              <ButtonLink
                href={`/admin/payments/new?member=${id}`}
                variant="gold"
              >
                Record Payment
              </ButtonLink>
            ) : null}
            {can(session.role, "members:write") ? (
              <ButtonLink href={`/admin/members/${id}/edit`} variant="ghost">
                Edit
              </ButtonLink>
            ) : null}
          </div>
        }
      />

      {saved ? (
        <div className="mb-8">
          <Notice tone="success">Changes saved.</Notice>
        </div>
      ) : null}

      {!registrationPaid ? (
        <div className="mb-8">
          <Notice tone="info">
            No registration fee has been recorded for this member.
          </Notice>
        </div>
      ) : null}

      <section aria-label="Position" className="mb-12">
        <div className="grid gap-x-10 sm:grid-cols-2 lg:grid-cols-4">
          <StatTile
            label="Monthly contribution"
            value={formatNaira(position.rateKobo)}
            detail={`${TIER_LABEL[member.tier]} tier`}
          />
          <StatTile
            label="Total received"
            value={formatNaira(totalReceived)}
            detail={`${payments.length} payment${payments.length === 1 ? "" : "s"} recorded`}
          />
          <StatTile
            label="Contribution billed"
            value={formatNaira(position.expectedKobo)}
            detail={
              position.accruing
                ? `${position.monthsBilled} month${position.monthsBilled === 1 ? "" : "s"} at ${formatNaira(position.rateKobo)}`
                : "Not accruing at this status"
            }
          />
          <StatTile
            label={position.creditKobo > 0 ? "Contribution credit" : "Contribution outstanding"}
            value={formatNaira(
              position.creditKobo > 0 ? position.creditKobo : position.arrearsKobo,
            )}
            detail={
              position.arrearsKobo > 0
                ? "Arrears on monthly contribution"
                : position.creditKobo > 0
                  ? "Paid ahead of schedule"
                  : "Up to date"
            }
          />
        </div>
      </section>

      <section aria-labelledby="details-heading" className="mb-12">
        <h2
          id="details-heading"
          className="font-display mb-5 text-[1.25rem] text-navy-900"
        >
          Record
        </h2>

        <DescriptionList>
          <DescriptionItem term="Status">
            <Badge tone={STATUS_TONE[member.status]}>
              {STATUS_LABEL[member.status]}
            </Badge>
          </DescriptionItem>
          <DescriptionItem term="Tier">
            {TIER_LABEL[member.tier]}
          </DescriptionItem>
          <DescriptionItem term="Email">
            <a
              href={`mailto:${member.email}`}
              className="break-all underline-offset-4 hover:underline"
            >
              {member.email}
            </a>
          </DescriptionItem>
          <DescriptionItem term="Phone">
            <a
              href={`tel:${member.phone.replace(/\s/g, "")}`}
              className="tnum underline-offset-4 hover:underline"
            >
              {member.phone}
            </a>
          </DescriptionItem>
          <DescriptionItem term="Contribution start">
            {member.joinedOn.toLocaleDateString("en-NG", dateFormat)}
          </DescriptionItem>
          <DescriptionItem term="Registered">
            {member.createdAt.toLocaleDateString("en-NG", dateFormat)}
          </DescriptionItem>
          {member.otherNames ? (
            <DescriptionItem term="Other names">
              {member.otherNames}
            </DescriptionItem>
          ) : null}
          {member.dateOfBirth ? (
            <DescriptionItem term="Date of birth">
              {member.dateOfBirth.toLocaleDateString("en-NG", dateFormat)}
            </DescriptionItem>
          ) : null}
          {member.occupation ? (
            <DescriptionItem term="Occupation">
              {member.occupation}
            </DescriptionItem>
          ) : null}
          {member.address ? (
            <DescriptionItem term="Address">{member.address}</DescriptionItem>
          ) : null}
          {member.notes ? (
            <DescriptionItem term="Notes">{member.notes}</DescriptionItem>
          ) : null}
        </DescriptionList>
      </section>

      {member.nextOfKin ? (
        <section aria-labelledby="kin-heading" className="mb-12">
          <h2
            id="kin-heading"
            className="font-display mb-5 text-[1.25rem] text-navy-900"
          >
            Next of kin
          </h2>

          <DescriptionList>
            <DescriptionItem term="Name">{member.nextOfKin.name}</DescriptionItem>
            <DescriptionItem term="Relationship">
              {member.nextOfKin.relationship}
            </DescriptionItem>
            <DescriptionItem term="Phone">
              <a
                href={`tel:${member.nextOfKin.phone.replace(/\s/g, "")}`}
                className="tnum underline-offset-4 hover:underline"
              >
                {member.nextOfKin.phone}
              </a>
            </DescriptionItem>
            {member.nextOfKin.email ? (
              <DescriptionItem term="Email">
                <a
                  href={`mailto:${member.nextOfKin.email}`}
                  className="break-all underline-offset-4 hover:underline"
                >
                  {member.nextOfKin.email}
                </a>
              </DescriptionItem>
            ) : null}
            {member.nextOfKin.address ? (
              <DescriptionItem term="Address">
                {member.nextOfKin.address}
              </DescriptionItem>
            ) : null}
          </DescriptionList>
        </section>
      ) : null}

      <section aria-labelledby="payments-heading">
        <h2
          id="payments-heading"
          className="font-display mb-5 text-[1.25rem] text-navy-900"
        >
          Payment history
        </h2>

        {payments.length === 0 ? (
          <EmptyState
            title="No payments recorded"
            body="Receipts entered for this member will be listed here."
            action={
              can(session.role, "payments:write") ? (
                <ButtonLink
                  href={`/admin/payments/new?member=${id}`}
                  variant="ghost"
                >
                  Record a payment
                </ButtonLink>
              ) : undefined
            }
          />
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Type</Th>
                <Th>Method</Th>
                <Th>Reference</Th>
                <Th align="right">Amount</Th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={String(payment._id)}>
                  <Td>
                    <span className="tnum">
                      {payment.receivedOn.toLocaleDateString("en-NG", dateFormat)}
                    </span>
                    <span className="label-sm mt-1 block text-ink-faint">
                      by {payment.recordedByName}
                    </span>
                  </Td>
                  <Td>
                    {KIND_LABEL[payment.kind]}
                    {payment.contributionPeriod ? (
                      <span className="label-sm mt-1 block text-ink-faint">
                        {formatMonthKey(payment.contributionPeriod)}
                      </span>
                    ) : null}
                  </Td>
                  <Td>
                    {METHOD_LABEL[payment.method]}
                    {payment.bank ? (
                      <span className="label-sm mt-1 block text-ink-faint">
                        {payment.bank}
                      </span>
                    ) : null}
                  </Td>
                  <Td>
                    {payment.reference ? (
                      <span className="font-mono text-[0.8125rem]">
                        {payment.reference}
                      </span>
                    ) : (
                      <span className="text-ink-faint">—</span>
                    )}
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

      <p className="mt-10">
        <Link
          href="/admin/members"
          className="label-sm text-ink-soft underline-offset-4 hover:underline"
        >
          ← Back to members
        </Link>
      </p>
    </>
  );
}
