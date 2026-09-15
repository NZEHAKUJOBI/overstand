/**
 * Society-wide figures, held in one place so the admin tools and the public
 * page can never drift apart. All money is in KOBO (₦1 = 100 kobo) and stored
 * as integers — never floats, which cannot represent money exactly.
 */

export const SLOT_PRICE_KOBO = 500_000; // ₦5,000
export const TOTAL_SLOT_POOL = 1_000_000;

export const MIN_INVESTOR_SLOTS = 100; // ₦500,000
export const MAX_INVESTOR_SLOTS = 10_000; // ₦50,000,000 — 1% of the pool

export const REGISTRATION_FEE_KOBO = 2_000_000; // ₦20,000
export const DUES_INVESTOR_KOBO = 1_000_000; // ₦10,000 / month
export const DUES_NON_INVESTOR_KOBO = 5_000_000; // ₦50,000 / month

/** 1,000,000 slots × ₦5,000 — the ₦5bn mobilization target. */
export const CAPITAL_TARGET_KOBO = TOTAL_SLOT_POOL * SLOT_PRICE_KOBO;
export const MEMBERSHIP_TARGET = 200;

export const BANKS = ["FCMB", "FMBN", "GTBank", "Other"] as const;
export type Bank = (typeof BANKS)[number];

export const MEMBER_TIERS = ["investor", "non_investor"] as const;
export type MemberTier = (typeof MEMBER_TIERS)[number];

export const MEMBER_STATUSES = [
  "pending",
  "active",
  "suspended",
  "exited",
] as const;
export type MemberStatus = (typeof MEMBER_STATUSES)[number];

export const PAYMENT_KINDS = [
  "registration",
  "dues",
  "slot_purchase",
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

/* Registration-of-interest vocabulary. Kept here, not on the Mongoose model,
   so the public form can import it without pulling the driver into the
   browser bundle. */
export const TIER_INTERESTS = ["investor", "non_investor", "undecided"] as const;
export type TierInterest = (typeof TIER_INTERESTS)[number];

export const ENQUIRY_STATUSES = [
  "new",
  "reviewing",
  "approved",
  "declined",
] as const;
export type EnquiryStatus = (typeof ENQUIRY_STATUSES)[number];

export const TIER_INTEREST_LABEL: Record<TierInterest, string> = {
  investor: "Investing member — I want to hold ownership slots",
  non_investor: "Non-investor member — services without slots",
  undecided: "I am not sure yet — please advise me",
};

export const ENQUIRY_STATUS_LABEL: Record<EnquiryStatus, string> = {
  new: "New",
  reviewing: "Reviewing",
  approved: "Approved",
  declined: "Declined",
};

export const TIER_LABEL: Record<MemberTier, string> = {
  investor: "Investing member",
  non_investor: "Non-investor member",
};

export const STATUS_LABEL: Record<MemberStatus, string> = {
  pending: "Pending",
  active: "Active",
  suspended: "Suspended",
  exited: "Exited",
};

export const KIND_LABEL: Record<PaymentKind, string> = {
  registration: "Registration fee",
  dues: "Monthly dues",
  slot_purchase: "Slot purchase",
  other: "Other",
};

export const METHOD_LABEL: Record<PaymentMethod, string> = {
  bank_transfer: "Bank transfer",
  cash: "Cash",
  pos: "POS",
  cheque: "Cheque",
};

/** Monthly dues owed by a member on the given tier. */
export function duesRateKobo(tier: MemberTier): number {
  return tier === "investor" ? DUES_INVESTOR_KOBO : DUES_NON_INVESTOR_KOBO;
}
