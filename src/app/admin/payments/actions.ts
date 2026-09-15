"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { Payment } from "@/lib/models/Payment";
import { recordAudit } from "@/lib/models/AuditLog";
import { fieldErrorsOf, paymentSchema } from "@/lib/validation";
import { KIND_LABEL } from "@/lib/constants";
import { formatMonthKey } from "@/lib/dues";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";
import { formatNaira } from "@/lib/money";

export type PaymentFormState = {
  error?: string;
  fieldErrors?: Record<string, string>;
};

export async function recordPayment(
  _previous: PaymentFormState,
  formData: FormData,
): Promise<PaymentFormState> {
  const guard = await checkPermission("payments:write");
  if ("error" in guard) return { error: guard.error };

  const parsed = paymentSchema.safeParse({
    memberId: formData.get("memberId"),
    kind: formData.get("kind"),
    amount: formData.get("amount"),
    duesPeriod: formData.get("duesPeriod"),
    method: formData.get("method"),
    bank: formData.get("bank"),
    reference: formData.get("reference"),
    receivedOn: formData.get("receivedOn"),
    note: formData.get("note"),
  });

  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const input = parsed.data;

  if (!isValidObjectId(input.memberId)) {
    return { fieldErrors: { memberId: "Choose a member." } };
  }

  let memberId: string;

  try {
    await connectDb();

    const member = await Member.findById(input.memberId)
      .select("membershipNumber firstName lastName")
      .lean();

    if (!member) return { fieldErrors: { memberId: "That member no longer exists." } };

    memberId = String(member._id);

    await Payment.create({
      member: member._id,
      kind: input.kind,
      amountKobo: input.amount,
      // Only dues carry a period; storing one on other kinds would break the
      // partial unique index that prevents duplicate months.
      duesPeriod: input.kind === "dues" ? input.duesPeriod : undefined,
      method: input.method,
      bank: input.bank || undefined,
      reference: input.reference || undefined,
      receivedOn: input.receivedOn,
      note: input.note || undefined,
      recordedBy: actorId(guard.session),
      recordedByName: guard.session.name,
    });

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: "payment.create",
      entity: "payment",
      entityId: memberId,
      summary: `Recorded ${formatNaira(input.amount)} — ${KIND_LABEL[input.kind]}${
        input.kind === "dues" && input.duesPeriod
          ? ` for ${formatMonthKey(input.duesPeriod)}`
          : ""
      } from ${member.firstName} ${member.lastName} (${member.membershipNumber}).`,
    });
  } catch (error) {
    if (duplicateKeyField(error)) {
      return {
        fieldErrors: {
          duesPeriod:
            "Dues for this member and month have already been recorded.",
        },
      };
    }

    console.error("[payments] create failed", error);
    return { error: `Could not record the payment. ${messageOf(error)}` };
  }

  revalidatePath("/admin");
  revalidatePath("/admin/payments");
  revalidatePath(`/admin/members/${memberId}`);
  redirect(`/admin/members/${memberId}`);
}
