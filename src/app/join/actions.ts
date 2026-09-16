"use server";

import { headers } from "next/headers";
import { connectDb } from "@/lib/db";
import { Application, nextApplicationReference } from "@/lib/models/Application";
import { sendApplicationMail } from "@/lib/mail";
import { applicationSchema, fieldErrorsOf } from "@/lib/validation";
import { duplicateKeyField } from "@/lib/mongoErrors";

export type ApplicationFormState = {
  error?: string;
  fieldErrors?: Record<string, string>;
  reference?: string;
  /** True when the application was stored but the receipt could not be sent. */
  mailDelayed?: boolean;
};

/** Same address may only apply this often. */
const DUPLICATE_WINDOW_MS = 10 * 60 * 1000;
/** Per-IP ceiling within the same window, to blunt scripted submissions. */
const IP_LIMIT = 5;

async function clientIp(): Promise<string | undefined> {
  const store = await headers();
  const forwarded = store.get("x-forwarded-for");
  // Render sits behind a proxy; the client is the first entry.
  return forwarded?.split(",")[0]?.trim() || undefined;
}

export async function submitApplication(
  _previous: ApplicationFormState,
  formData: FormData,
): Promise<ApplicationFormState> {
  // Honeypot: a real person never fills a field they cannot see. Answer as if
  // it succeeded so a bot learns nothing from the response.
  if (formData.get("website")) {
    return { reference: "OMCS-APP-0000-0000" };
  }

  const parsed = applicationSchema.safeParse({
    firstName: formData.get("firstName"),
    lastName: formData.get("lastName"),
    otherNames: formData.get("otherNames"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    dateOfBirth: formData.get("dateOfBirth"),
    occupation: formData.get("occupation"),
    nextOfKin: {
      name: formData.get("nextOfKin.name"),
      relationship: formData.get("nextOfKin.relationship"),
      phone: formData.get("nextOfKin.phone"),
      email: formData.get("nextOfKin.email"),
      address: formData.get("nextOfKin.address"),
    },
    tierInterest: formData.get("tierInterest"),
    customContribution: formData.get("customContribution"),
    eligibilityConfirmed: formData.get("eligibilityConfirmed"),
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

    const recentFromEmail = await Application.countDocuments({
      email: input.email.toLowerCase(),
      createdAt: { $gte: since },
    });

    if (recentFromEmail > 0) {
      return {
        error:
          "We already have a recent application from this email address. The Secretariat will be in touch — there is no need to submit again.",
      };
    }

    if (ip) {
      const recentFromIp = await Application.countDocuments({
        submittedIp: ip,
        createdAt: { $gte: since },
      });

      if (recentFromIp >= IP_LIMIT) {
        return {
          error: "Too many applications from this connection. Please try again later.",
        };
      }
    }

    const application = await Application.create({
      reference: await nextApplicationReference(new Date().getUTCFullYear()),
      firstName: input.firstName,
      lastName: input.lastName,
      otherNames: input.otherNames || undefined,
      email: input.email.toLowerCase(),
      phone: input.phone,
      address: input.address || undefined,
      dateOfBirth: input.dateOfBirth,
      occupation: input.occupation || undefined,
      nextOfKin: {
        ...input.nextOfKin,
        email: input.nextOfKin.email || undefined,
        address: input.nextOfKin.address || undefined,
      },
      tierInterest: input.tierInterest,
      customContributionKobo: input.customContributionKobo,
      eligibilityConfirmed: input.eligibilityConfirmed,
      heardFrom: input.heardFrom || undefined,
      message: input.message || undefined,
      submittedIp: ip,
      status: "new",
    });

    // The application is already safe in the database. Mail is attempted after,
    // and its outcome is recorded rather than thrown, so a mail outage can
    // never cost the Society an application.
    const outcome = await sendApplicationMail(application.toObject());

    await Application.updateOne(
      { _id: application._id },
      {
        $set: {
          applicantMail: outcome.applicant,
          secretariatMail: outcome.secretariat,
          mailError: outcome.error,
        },
      },
    );

    return {
      reference: application.reference,
      mailDelayed: outcome.applicant !== "sent",
    };
  } catch (error) {
    if (duplicateKeyField(error) === "reference") {
      return { error: "Please submit again — a reference collision occurred." };
    }

    console.error("[application] submission failed", error);
    return {
      error:
        "We could not record your application just now. Please try again, or visit the Society's office to collect a Membership/Entrance Form.",
    };
  }
}
