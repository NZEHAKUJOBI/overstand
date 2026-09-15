"use server";

import { revalidatePath } from "next/cache";
import { isValidObjectId } from "mongoose";
import { actorId, checkPermission, hashPassword } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { AdminUser } from "@/lib/models/AdminUser";
import { recordAudit } from "@/lib/models/AuditLog";
import { adminUserSchema, fieldErrorsOf } from "@/lib/validation";
import { ROLE_LABEL } from "@/lib/rbac";
import { duplicateKeyField, messageOf } from "@/lib/mongoErrors";

export type UserFormState = {
  error?: string;
  success?: string;
  fieldErrors?: Record<string, string>;
};

export async function createAdminUser(
  _previous: UserFormState,
  formData: FormData,
): Promise<UserFormState> {
  const guard = await checkPermission("users:manage");
  if ("error" in guard) return { error: guard.error };

  const parsed = adminUserSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
    role: formData.get("role"),
  });

  if (!parsed.success) return { fieldErrors: fieldErrorsOf(parsed.error) };

  const input = parsed.data;

  try {
    await connectDb();

    const user = await AdminUser.create({
      name: input.name,
      email: input.email.toLowerCase(),
      passwordHash: await hashPassword(input.password),
      role: input.role,
      active: true,
    });

    await recordAudit({
      actor: actorId(guard.session),
      actorName: guard.session.name,
      actorRole: guard.session.role,
      action: "admin_user.create",
      entity: "admin_user",
      entityId: String(user._id),
      summary: `Created ${ROLE_LABEL[input.role]} account for ${input.name} (${input.email}).`,
    });
  } catch (error) {
    if (duplicateKeyField(error) === "email") {
      return { fieldErrors: { email: "An account with this email already exists." } };
    }

    console.error("[users] create failed", error);
    return { error: `Could not create the account. ${messageOf(error)}` };
  }

  revalidatePath("/admin/users");
  return { success: `Account created for ${input.name}.` };
}

export async function setUserActive(formData: FormData): Promise<void> {
  const guard = await checkPermission("users:manage");
  if ("error" in guard) return;

  const userId = formData.get("userId");
  const active = formData.get("active") === "true";

  if (typeof userId !== "string" || !isValidObjectId(userId)) return;

  // An administrator must not be able to lock themselves out.
  if (userId === guard.session.sub) return;

  await connectDb();

  const user = await AdminUser.findById(userId).select("name email").lean();
  if (!user) return;

  await AdminUser.updateOne({ _id: userId }, { $set: { active } });

  await recordAudit({
    actor: actorId(guard.session),
    actorName: guard.session.name,
    actorRole: guard.session.role,
    action: active ? "admin_user.activate" : "admin_user.deactivate",
    entity: "admin_user",
    entityId: userId,
    summary: `${active ? "Reactivated" : "Deactivated"} the account for ${user.name} (${user.email}).`,
  });

  revalidatePath("/admin/users");
}
