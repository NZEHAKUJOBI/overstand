"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { nextMembershipNumber } from "@/lib/models/Counter";
import { recordAudit } from "@/lib/models/AuditLog";
import { fieldErrorsOf, memberSchema, type MemberInput } from "@/lib/validation";
import { contributionRateKobo, TIER_LABEL } from "@/lib/constants";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";
import { formatNaira } from "@/lib/money";

export type MemberFormState = {
  error?: string;
  fieldErrors?: Record<string, string>;
};

function readForm(formData: FormData) {
  return {
    firstName: formData.get("firstName"),
    lastName: formData.get("lastName"),
    otherNames: formData.get("otherNames"),
    email: formData.get("email"),
    phone: formData.get("phone"),
    address: formData.get("address"),
    dateOfBirth: formData.get("dateOfBirth"),
    occupation: formData.get("occupation"),
    tier: formData.get("tier"),
    customContribution: formData.get("customContribution"),
    nextOfKin: {
      name: formData.get("nextOfKin.name"),
      relationship: formData.get("nextOfKin.relationship"),
      phone: formData.get("nextOfKin.phone"),
      email: formData.get("nextOfKin.email"),
      address: formData.get("nextOfKin.address"),
    },
    status: formData.get("status"),
    joinedOn: formData.get("joinedOn"),
    notes: formData.get("notes"),
  };
}

/**
 * The shape written to Mongo. `customContribution` is the raw form string and
 * exists only to be validated, so it is dropped here rather than relying on
 * Mongoose's strict mode to discard it silently.
 */
function toDocument(input: MemberInput) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { customContribution, dateOfBirth, ...rest } = input;

  return {
    ...rest,
    // Mongoose's update typing rejects an explicit null here, and a cleared
    // date is removed with $unset rather than written as one.
    ...(dateOfBirth ? { dateOfBirth } : {}),
    otherNames: rest.otherNames || undefined,
    address: rest.address || undefined,
    occupation: rest.occupation || undefined,
    notes: rest.notes || undefined,
    nextOfKin: {
      ...rest.nextOfKin,
      email: rest.nextOfKin.email || undefined,
      address: rest.nextOfKin.address || undefined,
    },
  };
}

/** "Tier 1 (₦25,000/month)" — used in the audit trail. */
function describeTier(input: MemberInput): string {
  const rate = contributionRateKobo(input.tier, input.customContributionKobo);
  return `${TIER_LABEL[input.tier]} (${formatNaira(rate)}/month)`;
}

export async function createMember(
  _previous: MemberFormState,
  formData: FormData,
): Promise<MemberFormState> {
  const guard = await checkPermission("members:write");
  if ("error" in guard) return { error: guard.error };

  const parsed = memberSchema.safeParse(readForm(formData));
  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const input = parsed.data;
  let memberId: string;

  try {
    await connectDb();

    const membershipNumber = await nextMembershipNumber(
      input.joinedOn.getUTCFullYear(),
    );

    const member = await Member.create({
      ...toDocument(input),
      membershipNumber,
      createdBy: actorId(guard.session),
      updatedBy: actorId(guard.session),
    });

    memberId = String(member._id);

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: "member.create",
      entity: "member",
      entityId: memberId,
      summary: `Registered ${input.firstName} ${input.lastName} (${membershipNumber}) on ${describeTier(input)}.`,
    });
  } catch (error) {
    const duplicate = duplicateKeyField(error);

    if (duplicate === "email") {
      return { fieldErrors: { email: "A member with this email already exists." } };
    }
    if (duplicate === "membershipNumber") {
      return { error: "Membership number collision — please submit again." };
    }

    console.error("[members] create failed", error);
    return { error: `Could not save the member. ${messageOf(error)}` };
  }

  revalidatePath("/admin");
  revalidatePath("/admin/members");
  redirect(`/admin/members/${memberId}`);
}

export async function updateMember(
  _previous: MemberFormState,
  formData: FormData,
): Promise<MemberFormState> {
  const guard = await checkPermission("members:write");
  if ("error" in guard) return { error: guard.error };

  const memberId = formData.get("memberId");
  if (typeof memberId !== "string" || !isValidObjectId(memberId)) {
    return { error: "That member could not be identified." };
  }

  const parsed = memberSchema.safeParse(readForm(formData));
  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const input = parsed.data;

  try {
    await connectDb();

    const before = await Member.findById(memberId).lean();
    if (!before) return { error: "That member no longer exists." };

    await Member.updateOne(
      { _id: memberId },
      {
        $set: {
          ...toDocument(input),
          updatedBy: actorId(guard.session),
        },
        ...(input.dateOfBirth ? {} : { $unset: { dateOfBirth: "" } }),
      },
      { runValidators: true },
    );

    const changes: string[] = [];
    if (before.status !== input.status) {
      changes.push(`status ${before.status} → ${input.status}`);
    }
    if (
      before.tier !== input.tier ||
      (before.customContributionKobo ?? null) !== input.customContributionKobo
    ) {
      const wasKobo = contributionRateKobo(
        before.tier,
        before.customContributionKobo,
      );
      changes.push(
        `contribution ${formatNaira(wasKobo)} → ${formatNaira(
          contributionRateKobo(input.tier, input.customContributionKobo),
        )} per month`,
      );
    }

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: "member.update",
      entity: "member",
      entityId: memberId,
      summary: `Updated ${input.firstName} ${input.lastName} (${before.membershipNumber})${
        changes.length ? `: ${changes.join(", ")}` : ""
      }.`,
    });
  } catch (error) {
    if (duplicateKeyField(error) === "email") {
      return { fieldErrors: { email: "A member with this email already exists." } };
    }

    console.error("[members] update failed", error);
    return { error: `Could not save the changes. ${messageOf(error)}` };
  }

  revalidatePath("/admin");
  revalidatePath("/admin/members");
  revalidatePath(`/admin/members/${memberId}`);
  redirect(`/admin/members/${memberId}?saved=1`);
}
