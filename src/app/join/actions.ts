"use server";

import { headers } from "next/headers";
import { connectDb } from "@/lib/db";
import { Enquiry, nextEnquiryReference } from "@/lib/models/Enquiry";
import { sendEnquiryMail } from "@/lib/mail";
import { enquirySchema, fieldErrorsOf } from "@/lib/validation";
import { duplicateKeyField } from "@/lib/mongoErrors";

export type EnquiryFormState = {
  error?: string;
  fieldErrors?: Record<string, string>;
  reference?: string;
  /** True when the enquiry was stored but the receipt could not be sent. */
  mailDelayed?: boolean;
};

/** Same address may only enquire this often. */
const DUPLICATE_WINDOW_MS = 10 * 60 * 1000;
/** Per-IP ceiling within the same window, to blunt scripted submissions. */
const IP_LIMIT = 5;

async function clientIp(): Promise<string | undefined> {
  const store = await headers();
  const forwarded = store.get("x-forwarded-for");
  // Render sits behind a proxy; the client is the first entry.
  return forwarded?.split(",")[0]?.trim() || undefined;
}

export async function submitEnquiry(
  _previous: EnquiryFormState,
  formData: FormData,
): Promise<EnquiryFormState> {
  // Honeypot: a real person never fills a field they cannot see. Answer as if
  // it succeeded so a bot learns nothing from the response.
  if (formData.get("website")) {
    return { reference: "ARG-INT-0000-0000" };
  }

  const parsed = enquirySchema.safeParse({
    firstName: formData.get("firstName"),
    lastName: formData.get("lastName"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    occupation: formData.get("occupation"),
    tierInterest: formData.get("tierInterest"),
    slotsInterest: formData.get("slotsInterest"),
    heardFrom: formData.get("heardFrom"),
    message: formData.get("message"),
  });

  if (!parsed.success) {
    return { fieldErrors: fieldErrorsOf(parsed.error) };
  }

  const input = parsed.data;

  try {
    await connectDb();

    const since = new Date(Date.now() - DUPLICATE_WINDOW_MS);
    const ip = await clientIp();

    const recentFromEmail = await Enquiry.countDocuments({
      email: input.email.toLowerCase(),
      createdAt: { $gte: since },
    });

    if (recentFromEmail > 0) {
      return {
        error:
          "We already have a recent enquiry from this email address. The Secretariat will be in touch — there is no need to submit again.",
      };
    }

    if (ip) {
      const recentFromIp = await Enquiry.countDocuments({
        submittedIp: ip,
        createdAt: { $gte: since },
      });

      if (recentFromIp >= IP_LIMIT) {
        return {
          error: "Too many enquiries from this connection. Please try again later.",
        };
      }
    }

    const enquiry = await Enquiry.create({
      reference: await nextEnquiryReference(new Date().getUTCFullYear()),
      firstName: input.firstName,
      lastName: input.lastName,
      email: input.email.toLowerCase(),
      phone: input.phone,
      address: input.address || undefined,
      occupation: input.occupation || undefined,
      tierInterest: input.tierInterest,
      slotsInterest: input.slotsInterest ? Number(input.slotsInterest) : undefined,
      heardFrom: input.heardFrom || undefined,
      message: input.message || undefined,
      submittedIp: ip,
      status: "new",
    });

    // The enquiry is already safe in the database. Mail is attempted after,
    // and its outcome is recorded rather than thrown, so a mail outage can
    // never cost the Society an enquiry.
    const outcome = await sendEnquiryMail(enquiry.toObject());

    await Enquiry.updateOne(
      { _id: enquiry._id },
      {
        $set: {
          applicantMail: outcome.applicant,
          secretariatMail: outcome.secretariat,
          mailError: outcome.error,
        },
      },
    );

    return {
      reference: enquiry.reference,
      mailDelayed: outcome.applicant !== "sent",
    };
  } catch (error) {
    if (duplicateKeyField(error) === "reference") {
      return { error: "Please submit again — a reference collision occurred." };
    }

    console.error("[enquiry] submission failed", error);
    return {
      error:
        "We could not record your enquiry just now. Please try again, or call the Secretariat on +234 902 525 0026.",
    };
  }
}
