import { z, type ZodError } from "zod";
import {
  BANKS,
  MAX_INVESTOR_SLOTS,
  MEMBER_STATUSES,
  MEMBER_TIERS,
  MIN_INVESTOR_SLOTS,
  PAYMENT_KINDS,
  PAYMENT_METHODS,
  TIER_INTERESTS,
} from "./constants";
import { ROLES } from "./rbac";

import { parseNairaToKobo } from "./money";

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

/** Accepts "20,000" or "₦20,000.50" and yields integer kobo. */
const nairaAmount = trimmed
  .min(1, "Enter an amount.")
  .transform((value, ctx) => {
    const kobo = parseNairaToKobo(value);

    if (kobo === null) {
      ctx.addIssue({
        code: "custom",
        message: "Enter a valid amount, e.g. 10,000",
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

export const loginSchema = z.object({
  email: trimmed.min(1, "Enter your email or username."),
  password: z.string().min(1, "Enter your password."),
});

export const memberSchema = z
  .object({
    firstName: trimmed.min(1, "Enter a first name.").max(80),
    lastName: trimmed.min(1, "Enter a surname.").max(80),
    otherNames: trimmed.max(80).optional().or(z.literal("")),
    email: trimmed.min(1, "Enter an email.").pipe(z.email("Enter a valid email.")),
    phone: trimmed
      .min(7, "Enter a phone number.")
      .max(24)
      .regex(/^[+\d][\d\s-]*$/, "Enter a valid phone number."),
    address: trimmed.max(300).optional().or(z.literal("")),
    tier: z.enum(MEMBER_TIERS),
    slots: z.coerce
      .number()
      .int("Slots must be a whole number.")
      .min(0)
      .max(MAX_INVESTOR_SLOTS, `A member may hold at most ${MAX_INVESTOR_SLOTS} slots.`),
    status: z.enum(MEMBER_STATUSES),
    joinedOn: dateOnly,
    notes: trimmed.max(2000).optional().or(z.literal("")),
  })
  .superRefine((value, ctx) => {
    // The slot band only applies to investing members; the non-investor tier
    // is defined by holding none at all.
    if (value.tier === "investor") {
      if (value.slots < MIN_INVESTOR_SLOTS) {
        ctx.addIssue({
          code: "custom",
          path: ["slots"],
          message: `An investing member must hold at least ${MIN_INVESTOR_SLOTS} slots.`,
        });
      }
    } else if (value.slots !== 0) {
      ctx.addIssue({
        code: "custom",
        path: ["slots"],
        message: "A non-investor member holds no slots.",
      });
    }
  });

export const paymentSchema = z
  .object({
    memberId: trimmed.min(1, "Choose a member."),
    kind: z.enum(PAYMENT_KINDS),
    amount: nairaAmount,
    duesPeriod: trimmed
      .regex(/^\d{4}-(0[1-9]|1[0-2])$/, "Choose the month the dues cover.")
      .optional()
      .or(z.literal("")),
    method: z.enum(PAYMENT_METHODS),
    bank: z.enum(BANKS).optional().or(z.literal("")),
    reference: trimmed.max(80).optional().or(z.literal("")),
    receivedOn: dateOnly,
    note: trimmed.max(500).optional().or(z.literal("")),
  })
  .superRefine((value, ctx) => {
    if (value.kind === "dues" && !value.duesPeriod) {
      ctx.addIssue({
        code: "custom",
        path: ["duesPeriod"],
        message: "Choose the month these dues cover.",
      });
    }
  });

export const enquirySchema = z
  .object({
    firstName: trimmed.min(1, "Enter your first name.").max(80),
    lastName: trimmed.min(1, "Enter your surname.").max(80),
    email: trimmed
      .min(1, "Enter your email.")
      .pipe(z.email("Enter a valid email address.")),
    phone: trimmed
      .min(7, "Enter your phone number.")
      .max(24)
      .regex(/^[+\d][\d\s-]*$/, "Enter a valid phone number."),
    address: trimmed.max(300).optional().or(z.literal("")),
    occupation: trimmed.max(120).optional().or(z.literal("")),
    tierInterest: z.enum(TIER_INTERESTS),
    slotsInterest: trimmed.optional().or(z.literal("")),
    heardFrom: trimmed.max(120).optional().or(z.literal("")),
    message: trimmed.max(2000).optional().or(z.literal("")),
  })
  .superRefine((value, ctx) => {
    if (!value.slotsInterest) return;

    const slots = Number(value.slotsInterest);

    if (!Number.isInteger(slots)) {
      ctx.addIssue({
        code: "custom",
        path: ["slotsInterest"],
        message: "Enter a whole number of slots.",
      });
      return;
    }

    // An enquiry is not a commitment, but quoting a figure outside the band
    // would set the wrong expectation, so it is caught here.
    if (slots < MIN_INVESTOR_SLOTS || slots > MAX_INVESTOR_SLOTS) {
      ctx.addIssue({
        code: "custom",
        path: ["slotsInterest"],
        message: `Holdings run from ${MIN_INVESTOR_SLOTS.toLocaleString()} to ${MAX_INVESTOR_SLOTS.toLocaleString()} slots.`,
      });
    }
  });

export const enquiryReviewSchema = z.object({
  enquiryId: trimmed.min(1),
  decision: z.enum(["reviewing", "approved", "declined"]),
  reviewNote: trimmed.max(1000).optional().or(z.literal("")),
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
export type AdminUserInput = z.infer<typeof adminUserSchema>;
