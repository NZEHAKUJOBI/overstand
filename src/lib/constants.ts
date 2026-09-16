/**
 * Society-wide figures, held in one place so the admin tools and the public
 * page can never drift apart. All money is in KOBO (₦1 = 100 kobo) and stored
 * as integers — never floats, which cannot represent money exactly.
 *
 * Every figure here is taken from the Society's Official Update. Where that
 * document names a fee without stating its amount, the amount is `null` and
 * the page says "confirm at the office" rather than inventing a number.
 */

/* ── Fees ─────────────────────────────────────────────────────────── */

/** Non-refundable, paid on submission. Covers the form, ID card and processing. */
export const APPLICATION_FEE_KOBO = 2_000_000; // ₦20,000

/**
 * The Official Update names a one-time registration fee and an annual
 * membership fee but states neither amount. Fill these in when the Society
 * confirms them — the public page and the admin both read from here, and both
 * handle `null` by saying the amount is confirmed at the office.
 */
export const REGISTRATION_FEE_KOBO: number | null = null;
export const ANNUAL_MEMBERSHIP_FEE_KOBO: number | null = null;

/* ── Monthly contributions ────────────────────────────────────────── */

export const CONTRIBUTION_TIER_1_KOBO = 2_500_000; // ₦25,000 / month
export const CONTRIBUTION_TIER_2_KOBO = 5_000_000; // ₦50,000 / month

/**
 * Members contributing above Tier 2 agree a tailored structure with the
 * Society, so a custom rate must exceed Tier 2 — otherwise it is just Tier 1
 * or Tier 2 under another name. The ceiling is a typo guard, not a policy.
 */
export const CUSTOM_CONTRIBUTION_MIN_KOBO = CONTRIBUTION_TIER_2_KOBO;
export const MAX_CONTRIBUTION_KOBO = 1_000_000_000; // ₦10,000,000 / month

/** Minimum age for membership. */
export const MIN_MEMBER_AGE = 18;

export const MEMBER_TIERS = ["tier_1", "tier_2", "custom"] as const;
export type MemberTier = (typeof MEMBER_TIERS)[number];

export const MEMBER_STATUSES = [
  "pending",
  "active",
  "suspended",
  "exited",
] as const;
export type MemberStatus = (typeof MEMBER_STATUSES)[number];

export const PAYMENT_KINDS = [
  "application",
  "registration",
  "annual",
  "contribution",
  "other",
] as const;
export type PaymentKind = (typeof PAYMENT_KINDS)[number];

export const PAYMENT_METHODS = [
  "bank_transfer",
  "cash",
  "pos",
  "cheque",
] as const;
export type PaymentMethod = (typeof PAYMENT_METHODS)[number];

/** Banks the Society receives through. Confirm against the Society's mandate. */
export const BANKS = [
  "Access Bank",
  "First Bank",
  "GTBank",
  "UBA",
  "Zenith Bank",
  "Other",
] as const;
export type Bank = (typeof BANKS)[number];

/* Application vocabulary. Kept here, not on the Mongoose model, so the public
   form can import it without pulling the driver into the browser bundle. */

export const TIER_INTERESTS = ["tier_1", "tier_2", "custom"] as const;
export type TierInterest = (typeof TIER_INTERESTS)[number];

export const APPLICATION_STATUSES = [
  "new",
  "reviewing",
  "approved",
  "declined",
] as const;
export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

/* ── Labels ───────────────────────────────────────────────────────── */

export const TIER_LABEL: Record<MemberTier, string> = {
  tier_1: "Tier 1",
  tier_2: "Tier 2",
  custom: "Tailored",
};

export const TIER_INTEREST_LABEL: Record<TierInterest, string> = {
  tier_1: "Tier 1 — ₦25,000 per month",
  tier_2: "Tier 2 — ₦50,000 per month",
  custom: "Above ₦50,000 — I would like to discuss a tailored structure",
};

export const APPLICATION_STATUS_LABEL: Record<ApplicationStatus, string> = {
  new: "New",
  reviewing: "Reviewing",
  approved: "Approved",
  declined: "Declined",
};

export const STATUS_LABEL: Record<MemberStatus, string> = {
  pending: "Pending",
  active: "Active",
  suspended: "Suspended",
  exited: "Exited",
};

export const KIND_LABEL: Record<PaymentKind, string> = {
  application: "Application fee",
  registration: "Registration fee",
  annual: "Annual membership fee",
  contribution: "Monthly contribution",
  other: "Other",
};

export const METHOD_LABEL: Record<PaymentMethod, string> = {
  bank_transfer: "Bank transfer",
  cash: "Cash",
  pos: "POS",
  cheque: "Cheque",
};

/**
 * Monthly contribution owed by a member.
 *
 * A `custom` member carries their own agreed rate, so it is passed in rather
 * than derived; falling back to the Tier 2 floor means a custom member can
 * never accrue less than the tier they sit above.
 */
export function contributionRateKobo(
  tier: MemberTier,
  customRateKobo?: number | null,
): number {
  if (tier === "custom") {
    return customRateKobo && customRateKobo > 0
      ? customRateKobo
      : CUSTOM_CONTRIBUTION_MIN_KOBO;
  }

  return tier === "tier_1" ? CONTRIBUTION_TIER_1_KOBO : CONTRIBUTION_TIER_2_KOBO;
}
