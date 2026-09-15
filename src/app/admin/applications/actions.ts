"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Enquiry } from "@/lib/models/Enquiry";
import { Member } from "@/lib/models/Member";
import { nextMembershipNumber } from "@/lib/models/Counter";
import { recordAudit } from "@/lib/models/AuditLog";
import { enquiryReviewSchema, fieldErrorsOf } from "@/lib/validation";
import { MIN_INVESTOR_SLOTS, TOTAL_SLOT_POOL } from "@/lib/constants";
import { slotsAllocatedExcluding } from "@/lib/reporting";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";
import { formatNumber } from "@/lib/money";

export type ReviewState = {
  error?: string;
  success?: string;
  fieldErrors?: Record<string, string>;
};

export async function reviewEnquiry(
  _previous: ReviewState,
  formData: FormData,
): Promise<ReviewState> {
  const guard = await checkPermission("enquiries:write");
  if ("error" in guard) return { error: guard.error };

  const parsed = enquiryReviewSchema.safeParse({
    enquiryId: formData.get("enquiryId"),
    decision: formData.get("decision"),
    reviewNote: formData.get("reviewNote"),
  });

  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const { enquiryId, decision, reviewNote } = parsed.data;
  if (!isValidObjectId(enquiryId)) return { error: "Unknown enquiry." };

  let createdMemberId: string | null = null;

  try {
    await connectDb();

    const enquiry = await Enquiry.findById(enquiryId);
    if (!enquiry) return { error: "That enquiry no longer exists." };

    if (decision === "approved") {
      if (enquiry.member) {
        return { error: "This enquiry has already produced a member record." };
      }

      // Approving seeds the register; it does not admit anybody. The member
      // lands as "pending" so an officer still completes admission.
      const tier =
        enquiry.tierInterest === "non_investor" ? "non_investor" : "investor";

      const slots =
        tier === "investor"
          ? Math.max(enquiry.slotsInterest ?? MIN_INVESTOR_SLOTS, MIN_INVESTOR_SLOTS)
          : 0;

      // A pending member does not consume the pool, but flag an overflow now
      // rather than at admission time.
      const allocated = await slotsAllocatedExcluding();
      if (slots > TOTAL_SLOT_POOL - allocated) {
        return {
          error: `Only ${formatNumber(TOTAL_SLOT_POOL - allocated)} slots remain unallocated; this enquiry asks for ${formatNumber(slots)}.`,
        };
      }

      const member = await Member.create({
        membershipNumber: await nextMembershipNumber(new Date().getUTCFullYear()),
        firstName: enquiry.firstName,
        lastName: enquiry.lastName,
        email: enquiry.email,
        phone: enquiry.phone,
        address: enquiry.address,
        tier,
        slots,
        status: "pending",
        joinedOn: new Date(),
        notes: `Created from enquiry ${enquiry.reference}.`,
        createdBy: actorId(guard.session),
        updatedBy: actorId(guard.session),
      });

      createdMemberId = String(member._id);
      enquiry.member = member._id;
    }

    enquiry.status = decision;
    enquiry.reviewNote = reviewNote || undefined;
    enquiry.reviewedBy = actorId(guard.session);
    enquiry.reviewedByName = guard.session.name;
    enquiry.reviewedAt = new Date();
    await enquiry.save();

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: `enquiry.${decision}`,
      entity: "member",
      entityId: createdMemberId ?? undefined,
      summary:
        decision === "approved"
          ? `Approved enquiry ${enquiry.reference} from ${enquiry.firstName} ${enquiry.lastName} and seeded a pending member record.`
          : `Marked enquiry ${enquiry.reference} from ${enquiry.firstName} ${enquiry.lastName} as ${decision}.`,
    });
  } catch (error) {
    if (duplicateKeyField(error) === "email") {
      return {
        error:
          "A member with this email is already on the register. Link or update that record instead of approving this enquiry.",
      };
    }

    console.error("[enquiry] review failed", error);
    return { error: `Could not save the decision. ${messageOf(error)}` };
  }

  revalidatePath("/admin");
  revalidatePath("/admin/applications");
  revalidatePath(`/admin/applications/${enquiryId}`);

  if (createdMemberId) {
    revalidatePath("/admin/members");
    redirect(`/admin/members/${createdMemberId}?saved=1`);
  }

  return { success: `Enquiry marked as ${decision}.` };
}
