import {
  contributionRateKobo,
  type MemberStatus,
  type MemberTier,
} from "./constants";

/**
 * Monthly contribution accrual.
 *
 * Business rule: contributions accrue from the member's `joinedOn` month
 * inclusive, for as long as the member is `active` or `suspended`. `pending`
 * members have not been admitted yet and `exited` members have left, so
 * neither accrues — suspension deliberately keeps accruing, since it is
 * usually a consequence of arrears and zeroing the balance would erase the
 * debt.
 */

export type ContributionPosition = {
  monthsBilled: number;
  /** The member's own monthly rate, tailored members included. */
  rateKobo: number;
  expectedKobo: number;
  paidKobo: number;
  /** Never negative — an overpayment shows as credit, not negative arrears. */
  arrearsKobo: number;
  creditKobo: number;
  accruing: boolean;
};

/** The subset of a member this module needs, so callers can pass a lean doc. */
export type ContributingMember = {
  tier: MemberTier;
  status: MemberStatus;
  joinedOn: Date;
  customContributionKobo?: number | null;
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

export function computeContribution(
  member: ContributingMember,
  contributionPaidKobo: number,
  asOf: Date = new Date(),
): ContributionPosition {
  const accruing = ACCRUING_STATUSES.includes(member.status);

  const monthsBilled = accruing
    ? monthsBilledBetween(member.joinedOn, asOf)
    : 0;

  const rateKobo = contributionRateKobo(
    member.tier,
    member.customContributionKobo,
  );

  const expectedKobo = monthsBilled * rateKobo;
  const balance = expectedKobo - contributionPaidKobo;

  return {
    monthsBilled,
    rateKobo,
    expectedKobo,
    paidKobo: contributionPaidKobo,
    arrearsKobo: Math.max(0, balance),
    creditKobo: Math.max(0, -balance),
    accruing,
  };
}

/** Every contribution month from joining to now, newest first. */
export function contributionPeriodsSince(
  joinedOn: Date,
  asOf: Date = new Date(),
): string[] {
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
