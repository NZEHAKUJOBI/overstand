import { z, type ZodError } from "zod";
import {
  BANKS,
  CUSTOM_CONTRIBUTION_MIN_KOBO,
  MAX_CONTRIBUTION_KOBO,
  MEMBER_STATUSES,
  MEMBER_TIERS,
  MIN_MEMBER_AGE,
  PAYMENT_KINDS,
  PAYMENT_METHODS,
  TIER_INTERESTS,
} from "./constants";
import { ROLES } from "./rbac";

import { formatNaira, parseNairaToKobo } from "./money";

/** Flattens a ZodError into one message per field, for rendering beside inputs. */
export function fieldErrorsOf(error: ZodError): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const issue of error.issues) {
    const key = issue.path.join(".") || "form";
    errors[key] ??= issue.message;
  }

  return errors;
}

const trimmed = z.string().trim();
const optional = (max: number) => trimmed.max(max).optional().or(z.literal(""));

const phoneField = trimmed
  .min(7, "Enter a phone number.")
  .max(24)
  .regex(/^[+\d][\d\s-]*$/, "Enter a valid phone number.");

/** Accepts "20,000" or "₦20,000.50" and yields integer kobo. */
const nairaAmount = trimmed
  .min(1, "Enter an amount.")
  .transform((value, ctx) => {
    const kobo = parseNairaToKobo(value);

    if (kobo === null) {
      ctx.addIssue({
        code: "custom",
        message: "Enter a valid amount, e.g. 25,000",
      });
      return z.NEVER;
    }

    if (kobo <= 0) {
      ctx.addIssue({ code: "custom", message: "Amount must be more than zero." });
      return z.NEVER;
    }

    return kobo;
  });

const dateOnly = trimmed
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Choose a date.")
  .transform((value, ctx) => {
    const date = new Date(`${value}T00:00:00.000Z`);

    if (Number.isNaN(date.getTime())) {
      ctx.addIssue({ code: "custom", message: "Choose a valid date." });
      return z.NEVER;
    }

    return date;
  });

/** Completed years between a date of birth and today, in UTC. */
export function ageOn(dateOfBirth: Date, asOf: Date = new Date()): number {
  let age = asOf.getUTCFullYear() - dateOfBirth.getUTCFullYear();
  const monthDelta = asOf.getUTCMonth() - dateOfBirth.getUTCMonth();

  if (monthDelta < 0 || (monthDelta === 0 && asOf.getUTCDate() < dateOfBirth.getUTCDate())) {
    age -= 1;
  }

  return age;
}

/**
 * Shared next-of-kin block. The Membership Application Form requires it, so
 * name, relationship and phone are all mandatory — a next of kin who cannot
 * be reached is not one.
 */
const nextOfKinSchema = z.object({
  name: trimmed.min(1, "Enter your next of kin's name.").max(80),
  relationship: trimmed.min(1, "State the relationship.").max(40),
  phone: phoneField,
  email: optional(160),
  address: optional(300),
});

/**
 * The contribution tier rule, shared by the member record and the public
 * application so both sides enforce it identically: the standard tiers carry
 * no custom figure, and a tailored figure must sit above Tier 2 — otherwise
 * it is a standard tier under another name.
 */
function checkCustomContribution(
  tier: string,
  raw: string | undefined,
  ctx: z.RefinementCtx,
  path: string,
) {
  if (tier !== "custom") return;

  const kobo = parseNairaToKobo(raw ?? "");

  if (kobo === null) {
    ctx.addIssue({
      code: "custom",
      path: [path],
      message: "Enter the monthly amount you intend to contribute.",
    });
    return;
  }

  if (kobo <= CUSTOM_CONTRIBUTION_MIN_KOBO) {
    ctx.addIssue({
      code: "custom",
      path: [path],
      message: `A tailored contribution must be above ${formatNaira(CUSTOM_CONTRIBUTION_MIN_KOBO)}. Choose Tier 1 or Tier 2 otherwise.`,
    });
    return;
  }

  if (kobo > MAX_CONTRIBUTION_KOBO) {
    ctx.addIssue({
      code: "custom",
      path: [path],
      message: `That is above ${formatNaira(MAX_CONTRIBUTION_KOBO)} a month — speak to the Secretariat directly.`,
    });
  }
}

export const loginSchema = z.object({
  email: trimmed.min(1, "Enter your email or username."),
  password: z.string().min(1, "Enter your password."),
});

export const memberSchema = z
  .object({
    firstName: trimmed.min(1, "Enter a first name.").max(80),
    lastName: trimmed.min(1, "Enter a surname.").max(80),
    otherNames: optional(80),
    email: trimmed.min(1, "Enter an email.").pipe(z.email("Enter a valid email.")),
    phone: phoneField,
    address: optional(300),
    dateOfBirth: trimmed
      .regex(/^\d{4}-\d{2}-\d{2}$/, "Choose a date of birth.")
      .optional()
      .or(z.literal("")),
    occupation: optional(120),
    tier: z.enum(MEMBER_TIERS),
    customContribution: optional(24),
    nextOfKin: nextOfKinSchema,
    status: z.enum(MEMBER_STATUSES),
    joinedOn: dateOnly,
    notes: optional(2000),
  })
  .superRefine((value, ctx) => {
    checkCustomContribution(value.tier, value.customContribution, ctx, "customContribution");

    if (value.dateOfBirth) {
      const born = new Date(`${value.dateOfBirth}T00:00:00.000Z`);

      if (Number.isNaN(born.getTime())) {
        ctx.addIssue({
          code: "custom",
          path: ["dateOfBirth"],
          message: "Choose a valid date of birth.",
        });
      } else if (ageOn(born) < MIN_MEMBER_AGE) {
        ctx.addIssue({
          code: "custom",
          path: ["dateOfBirth"],
          message: `Members must be at least ${MIN_MEMBER_AGE} years old.`,
        });
      }
    }
  })
  .transform((value) => ({
    ...value,
    dateOfBirth: value.dateOfBirth
      ? new Date(`${value.dateOfBirth}T00:00:00.000Z`)
      : null,
    customContributionKobo:
      value.tier === "custom" ? parseNairaToKobo(value.customContribution ?? "") : null,
  }));

export const paymentSchema = z
  .object({
    memberId: trimmed.min(1, "Choose a member."),
    kind: z.enum(PAYMENT_KINDS),
    amount: nairaAmount,
    contributionPeriod: trimmed
      .regex(/^\d{4}-(0[1-9]|1[0-2])$/, "Choose the month the contribution covers.")
      .optional()
      .or(z.literal("")),
    method: z.enum(PAYMENT_METHODS),
    bank: z.enum(BANKS).optional().or(z.literal("")),
    reference: optional(80),
    receivedOn: dateOnly,
    note: optional(500),
  })
  .superRefine((value, ctx) => {
    if (value.kind === "contribution" && !value.contributionPeriod) {
      ctx.addIssue({
        code: "custom",
        path: ["contributionPeriod"],
        message: "Choose the month this contribution covers.",
      });
    }
  });

export const applicationSchema = z
  .object({
    firstName: trimmed.min(1, "Enter your first name.").max(80),
    lastName: trimmed.min(1, "Enter your surname.").max(80),
    otherNames: optional(80),
    email: trimmed
      .min(1, "Enter your email.")
      .pipe(z.email("Enter a valid email address.")),
    phone: phoneField,
    address: optional(300),
    dateOfBirth: trimmed.regex(/^\d{4}-\d{2}-\d{2}$/, "Enter your date of birth."),
    occupation: optional(120),
    nextOfKin: nextOfKinSchema,
    tierInterest: z.enum(TIER_INTERESTS),
    customContribution: optional(24),
    eligibilityConfirmed: z
      .unknown()
      .transform((value) => value === "on" || value === "true" || value === true)
      .refine((value) => value, {
        message: `Confirm that you are ${MIN_MEMBER_AGE} or over, of good character and of sound mind.`,
      }),
    heardFrom: optional(120),
    message: optional(2000),
  })
  .superRefine((value, ctx) => {
    checkCustomContribution(
      value.tierInterest,
      value.customContribution,
      ctx,
      "customContribution",
    );

    const born = new Date(`${value.dateOfBirth}T00:00:00.000Z`);

    if (Number.isNaN(born.getTime())) {
      ctx.addIssue({
        code: "custom",
        path: ["dateOfBirth"],
        message: "Enter a valid date of birth.",
      });
      return;
    }

    // Age is an eligibility criterion, so it is enforced here rather than
    // left to the Secretariat to catch on the paper form.
    if (ageOn(born) < MIN_MEMBER_AGE) {
      ctx.addIssue({
        code: "custom",
        path: ["dateOfBirth"],
        message: `Membership is open to applicants aged ${MIN_MEMBER_AGE} and over.`,
      });
    }
  })
  .transform((value) => ({
    ...value,
    dateOfBirth: new Date(`${value.dateOfBirth}T00:00:00.000Z`),
    customContributionKobo:
      value.tierInterest === "custom"
        ? parseNairaToKobo(value.customContribution ?? "")
        : null,
  }));

export const applicationReviewSchema = z.object({
  applicationId: trimmed.min(1),
  // Every status except "new", which is the state an application arrives in.
  decision: z.enum(["reviewing", "approved", "declined"]),
  reviewNote: optional(1000),
});

export const adminUserSchema = z.object({
  name: trimmed.min(1, "Enter a name.").max(80),
  email: trimmed.min(1, "Enter an email.").pipe(z.email("Enter a valid email.")),
  password: z
    .string()
    .min(6, "Use at least 6 characters.")
    .max(200, "That password is too long."),
  role: z.enum(ROLES),
});

export type MemberInput = z.infer<typeof memberSchema>;
export type PaymentInput = z.infer<typeof paymentSchema>;
export type ApplicationInput = z.infer<typeof applicationSchema>;
export type AdminUserInput = z.infer<typeof adminUserSchema>;
