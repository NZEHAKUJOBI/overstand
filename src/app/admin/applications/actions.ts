"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Application } from "@/lib/models/Application";
import { Member } from "@/lib/models/Member";
import { nextMembershipNumber } from "@/lib/models/Counter";
import { recordAudit } from "@/lib/models/AuditLog";
import { applicationReviewSchema, fieldErrorsOf } from "@/lib/validation";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";

export type ReviewState = {
  error?: string;
  success?: string;
  fieldErrors?: Record<string, string>;
};

export async function reviewApplication(
  _previous: ReviewState,
  formData: FormData,
): Promise<ReviewState> {
  const guard = await checkPermission("applications:write");
  if ("error" in guard) return { error: guard.error };

  const parsed = applicationReviewSchema.safeParse({
    applicationId: formData.get("applicationId"),
    decision: formData.get("decision"),
    reviewNote: formData.get("reviewNote"),
  });

  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const { applicationId, decision, reviewNote } = parsed.data;
  if (!isValidObjectId(applicationId)) return { error: "Unknown application." };

  let createdMemberId: string | null = null;

  try {
    await connectDb();

    const application = await Application.findById(applicationId);
    if (!application) return { error: "That application no longer exists." };

    if (decision === "approved") {
      if (application.member) {
        return { error: "This application has already produced a member record." };
      }

      // Approving seeds the register; it does not admit anybody. The member
      // lands as "pending" so an officer still completes admission, collects
      // the application fee and issues the Membership/Entrance Form.
      const member = await Member.create({
        membershipNumber: await nextMembershipNumber(new Date().getUTCFullYear()),
        firstName: application.firstName,
        lastName: application.lastName,
        otherNames: application.otherNames,
        email: application.email,
        phone: application.phone,
        address: application.address,
        dateOfBirth: application.dateOfBirth,
        occupation: application.occupation,
        nextOfKin: application.nextOfKin,
        tier: application.tierInterest,
        customContributionKobo: application.customContributionKobo ?? null,
        status: "pending",
        joinedOn: new Date(),
        notes: `Created from application ${application.reference}.`,
        createdBy: actorId(guard.session),
        updatedBy: actorId(guard.session),
      });

      createdMemberId = String(member._id);
      application.member = member._id;
    }

    application.status = decision;
    application.reviewNote = reviewNote || undefined;
    application.reviewedBy = actorId(guard.session);
    application.reviewedByName = guard.session.name;
    application.reviewedAt = new Date();
    await application.save();

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: `application.${decision}`,
      entity: "member",
      entityId: createdMemberId ?? undefined,
      summary:
        decision === "approved"
          ? `Approved application ${application.reference} from ${application.firstName} ${application.lastName} and seeded a pending member record.`
          : `Marked application ${application.reference} from ${application.firstName} ${application.lastName} as ${decision}.`,
    });
  } catch (error) {
    if (duplicateKeyField(error) === "email") {
      return {
        error:
          "A member with this email is already on the register. Link or update that record instead of approving this application.",
      };
    }

    console.error("[application] review failed", error);
    return { error: `Could not save the decision. ${messageOf(error)}` };
  }

  revalidatePath("/admin");
  revalidatePath("/admin/applications");
  revalidatePath(`/admin/applications/${applicationId}`);

  if (createdMemberId) {
    revalidatePath("/admin/members");
    redirect(`/admin/members/${createdMemberId}?saved=1`);
  }

  return { success: `Application marked as ${decision}.` };
}
