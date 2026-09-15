"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { nextMembershipNumber } from "@/lib/models/Counter";
import { recordAudit } from "@/lib/models/AuditLog";
import { fieldErrorsOf, memberSchema } from "@/lib/validation";
import { slotsAllocatedExcluding } from "@/lib/reporting";
import { TOTAL_SLOT_POOL } from "@/lib/constants";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";
import { formatNumber } from "@/lib/money";

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
    tier: formData.get("tier"),
    slots: formData.get("slots"),
    status: formData.get("status"),
    joinedOn: formData.get("joinedOn"),
    notes: formData.get("notes"),
  };
}

/**
 * The pool ceiling is a Society-wide invariant, so it is checked here rather
 * than in the schema — it needs to know what every other member already holds.
 */
async function poolWouldOverflow(
  slots: number,
  status: string,
  excludeMemberId?: string,
): Promise<number | null> {
  if (status !== "active" && status !== "suspended") return null;

  const allocated = await slotsAllocatedExcluding(excludeMemberId);
  const remaining = TOTAL_SLOT_POOL - allocated;

  return slots > remaining ? remaining : null;
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

    const remaining = await poolWouldOverflow(input.slots, input.status);
    if (remaining !== null) {
      return {
        fieldErrors: {
          slots: `Only ${formatNumber(remaining)} slots remain unallocated in the pool.`,
        },
      };
    }

    const membershipNumber = await nextMembershipNumber(
      input.joinedOn.getUTCFullYear(),
    );

    const member = await Member.create({
      ...input,
      otherNames: input.otherNames || undefined,
      address: input.address || undefined,
      notes: input.notes || undefined,
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
      summary: `Registered ${input.firstName} ${input.lastName} (${membershipNumber}) holding ${formatNumber(input.slots)} slots.`,
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

    const remaining = await poolWouldOverflow(
      input.slots,
      input.status,
      memberId,
    );
    if (remaining !== null) {
      return {
        fieldErrors: {
          slots: `Only ${formatNumber(remaining)} slots remain unallocated in the pool.`,
        },
      };
    }

    const before = await Member.findById(memberId).lean();
    if (!before) return { error: "That member no longer exists." };

    await Member.updateOne(
      { _id: memberId },
      {
        $set: {
          ...input,
          otherNames: input.otherNames || undefined,
          address: input.address || undefined,
          notes: input.notes || undefined,
          updatedBy: actorId(guard.session),
        },
      },
      { runValidators: true },
    );

    const changes: string[] = [];
    if (before.slots !== input.slots) {
      changes.push(
        `slots ${formatNumber(before.slots)} → ${formatNumber(input.slots)}`,
      );
    }
    if (before.status !== input.status) {
      changes.push(`status ${before.status} → ${input.status}`);
    }
    if (before.tier !== input.tier) {
      changes.push(`tier ${before.tier} → ${input.tier}`);
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
