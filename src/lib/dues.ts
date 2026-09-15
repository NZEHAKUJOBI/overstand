import { duesRateKobo, type MemberStatus, type MemberTier } from "./constants";

/**
 * Monthly dues accrual.
 *
 * Business rule: dues accrue from the member's `joinedOn` month inclusive, for
 * as long as the member is `active` or `suspended`. `pending` members have not
 * been admitted yet and `exited` members have left, so neither accrues —
 * suspension deliberately keeps accruing, since it is usually a consequence of
 * arrears and zeroing the balance would erase the debt.
 */

export type DuesPosition = {
  monthsBilled: number;
  expectedKobo: number;
  paidKobo: number;
  /** Never negative — an overpayment shows as credit, not negative arrears. */
  arrearsKobo: number;
  creditKobo: number;
  accruing: boolean;
};

const ACCRUING_STATUSES: readonly MemberStatus[] = ["active", "suspended"];

/** "2026-09" for September 2026. */
export function monthKey(date: Date): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}

export function formatMonthKey(key: string): string {
  const [year, month] = key.split("-").map(Number);
  if (!year || !month) return key;

  return new Date(Date.UTC(year, month - 1, 1)).toLocaleDateString("en-NG", {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

/** Whole months from `from` to `to` inclusive of both endpoint months. */
export function monthsBilledBetween(from: Date, to: Date): number {
  const months =
    (to.getUTCFullYear() - from.getUTCFullYear()) * 12 +
    (to.getUTCMonth() - from.getUTCMonth()) +
    1;

  return Math.max(0, months);
}

export function computeDues(
  member: { tier: MemberTier; status: MemberStatus; joinedOn: Date },
  duesPaidKobo: number,
  asOf: Date = new Date(),
): DuesPosition {
  const accruing = ACCRUING_STATUSES.includes(member.status);

  const monthsBilled = accruing
    ? monthsBilledBetween(member.joinedOn, asOf)
    : 0;

  const expectedKobo = monthsBilled * duesRateKobo(member.tier);
  const balance = expectedKobo - duesPaidKobo;

  return {
    monthsBilled,
    expectedKobo,
    paidKobo: duesPaidKobo,
    arrearsKobo: Math.max(0, balance),
    creditKobo: Math.max(0, -balance),
    accruing,
  };
}

/** Every dues month from joining to now, newest first. */
export function duesPeriodsSince(joinedOn: Date, asOf: Date = new Date()): string[] {
  const periods: string[] = [];
  const cursor = new Date(
    Date.UTC(joinedOn.getUTCFullYear(), joinedOn.getUTCMonth(), 1),
  );
  const end = new Date(Date.UTC(asOf.getUTCFullYear(), asOf.getUTCMonth(), 1));

  while (cursor <= end) {
    periods.push(monthKey(cursor));
    cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  }

  return periods.reverse();
}
