import Link from "next/link";
import type { QueryFilter } from "mongoose";
import {
  ButtonLink,
  EmptyState,
  Input,
  PageHeader,
  Select,
  Table,
  Td,
  Th,
} from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { connectDb } from "@/lib/db";
import { Payment, type PaymentDoc } from "@/lib/models/Payment";
import { formatMonthKey } from "@/lib/dues";
import {
  KIND_LABEL,
  METHOD_LABEL,
  PAYMENT_KINDS,
  type PaymentKind,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";

const PAGE_SIZE = 25;

const dateFormat: Intl.DateTimeFormatOptions = {
  day: "2-digit",
  month: "short",
  year: "numeric",
};

type PopulatedMember = {
  _id: unknown;
  membershipNumber: string;
  firstName: string;
  lastName: string;
};

export default async function PaymentsPage({
  searchParams,
}: {
  searchParams: Promise<{
    kind?: string;
    from?: string;
    to?: string;
    page?: string;
  }>;
}) {
  const session = await requirePermission("payments:read");
  const params = await searchParams;

  const kind = PAYMENT_KINDS.includes(params.kind as PaymentKind)
    ? (params.kind as PaymentKind)
    : "";
  const from = isDate(params.from) ? params.from : "";
  const to = isDate(params.to) ? params.to : "";
  const page = Math.max(1, Number(params.page) || 1);

  await connectDb();

  const filter: QueryFilter<PaymentDoc> = {};
  if (kind) filter.kind = kind;

  if (from || to) {
    const range: Record<string, Date> = {};
    if (from) range.$gte = new Date(`${from}T00:00:00.000Z`);
    if (to) range.$lte = new Date(`${to}T23:59:59.999Z`);
    filter.receivedOn = range;
  }

  const [payments, total, totals] = await Promise.all([
    Payment.find(filter)
      .sort({ receivedOn: -1, createdAt: -1 })
      .skip((page - 1) * PAGE_SIZE)
      .limit(PAGE_SIZE)
      .populate<{ member: PopulatedMember | null }>(
        "member",
        "membershipNumber firstName lastName",
      )
      .lean(),
    Payment.countDocuments(filter),
    Payment.aggregate<{ total: number }>([
      { $match: filter },
      { $group: { _id: null, total: { $sum: "$amountKobo" } } },
    ]),
  ]);

  const filteredTotalKobo = totals[0]?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const queryFor = (overrides: Record<string, string>) => {
    const next = new URLSearchParams();
    if (kind) next.set("kind", kind);
    if (from) next.set("from", from);
    if (to) next.set("to", to);
    for (const [key, value] of Object.entries(overrides)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    const string = next.toString();
    return string ? `/admin/payments?${string}` : "/admin/payments";
  };

  return (
    <>
      <PageHeader
        title="Payments"
        description={`${total} receipt${total === 1 ? "" : "s"} totalling ${formatNaira(filteredTotalKobo)}${
          kind || from || to ? " in this view" : ""
        }.`}
        action={
          can(session.role, "payments:write") ? (
            <ButtonLink href="/admin/payments/new" variant="gold">
              Record Payment
            </ButtonLink>
          ) : undefined
        }
      />

      <form
        method="GET"
        action="/admin/payments"
        className="mb-8 grid gap-4 border-b border-rule pb-8 sm:grid-cols-2 lg:grid-cols-[1.5fr_1fr_1fr_auto]"
      >
        <div>
          <label htmlFor="kind" className="label-sm block text-ink-soft">
            Type
          </label>
          <Select id="kind" name="kind" defaultValue={kind} className="mt-2">
            <option value="">All types</option>
            {PAYMENT_KINDS.map((value) => (
              <option key={value} value={value}>
                {KIND_LABEL[value]}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="from" className="label-sm block text-ink-soft">
            From
          </label>
          <Input
            id="from"
            name="from"
            type="date"
            defaultValue={from}
            className="mt-2"
          />
        </div>

        <div>
          <label htmlFor="to" className="label-sm block text-ink-soft">
            To
          </label>
          <Input id="to" name="to" type="date" defaultValue={to} className="mt-2" />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            className="label border border-forest-900/25 px-5 py-3 text-forest-900 transition-colors hover:bg-forest-900/5"
          >
            Apply
          </button>
        </div>
      </form>

      {payments.length === 0 ? (
        <EmptyState
          title={kind || from || to ? "No matching receipts" : "No payments recorded"}
          body={
            kind || from || to
              ? "Nothing was received in this period under this filter."
              : "Recorded receipts appear here, newest first."
          }
          action={
            can(session.role, "payments:write") ? (
              <ButtonLink href="/admin/payments/new" variant="ghost">
                Record a payment
              </ButtonLink>
            ) : undefined
          }
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Member</Th>
                <Th>Type</Th>
                <Th>Method</Th>
                <Th>Recorded by</Th>
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
                  </Td>
                  <Td>
                    {payment.member ? (
                      <>
                        <Link
                          href={`/admin/members/${String(payment.member._id)}`}
                          className="text-forest-900 underline-offset-4 hover:underline"
                        >
                          {payment.member.firstName} {payment.member.lastName}
                        </Link>
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
                    {payment.duesPeriod ? (
                      <span className="label-sm mt-1 block text-ink-faint">
                        {formatMonthKey(payment.duesPeriod)}
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
                    <span className="text-[0.875rem]">
                      {payment.recordedByName}
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

          {pageCount > 1 ? (
            <nav
              aria-label="Pagination"
              className="mt-8 flex items-center justify-between gap-4"
            >
              <span className="label-sm text-ink-faint">
                Page {page} of {pageCount}
              </span>
              <div className="flex gap-3">
                {page > 1 ? (
                  <Link
                    href={queryFor({ page: String(page - 1) })}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Previous
                  </Link>
                ) : null}
                {page < pageCount ? (
                  <Link
                    href={queryFor({ page: String(page + 1) })}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Next
                  </Link>
                ) : null}
              </div>
            </nav>
          ) : null}
        </>
      )}
    </>
  );
}

function isDate(value: string | undefined): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
}
