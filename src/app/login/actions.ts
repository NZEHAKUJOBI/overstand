"use server";

import { redirect } from "next/navigation";
import { connectDb } from "@/lib/db";
import { AdminUser } from "@/lib/models/AdminUser";
import {
  endSession,
  hashPassword,
  startSession,
  verifyPassword,
} from "@/lib/auth";
import { fieldErrorsOf, loginSchema } from "@/lib/validation";

export type LoginState = {
  error?: string;
  fieldErrors?: Record<string, string>;
};

/**
 * A hash of a random value nobody knows, compared against when the email is
 * unknown. Without it, a missing account returns far faster than a wrong
 * password, and the response time reveals which addresses are registered.
 * Computed once per process and reused.
 */
let decoyHash: Promise<string> | null = null;

function getDecoyHash(): Promise<string> {
  decoyHash ??= hashPassword(crypto.randomUUID());
  return decoyHash;
}

export async function signIn(
  _previous: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const parsed = loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });

  if (!parsed.success) {
    return { fieldErrors: fieldErrorsOf(parsed.error) };
  }

  let destination = "/admin";

  try {
    await connectDb();

    const identifier = parsed.data.email.toLowerCase();
    const resolvedEmail = identifier.includes("@")
      ? identifier
      : `${identifier}@anchorrealestategroup.ng`;

    let user = await AdminUser.findOne({
      email: { $in: [identifier, resolvedEmail] },
    });

    const defaultSeedEmail = (
      process.env.SEED_ADMIN_EMAIL ?? "admin@anchorrealestategroup.ng"
    ).toLowerCase();
    const defaultSeedPassword = process.env.SEED_ADMIN_PASSWORD ?? "123456789";

    // Auto-seed admin on first login (essential on serverless platforms like Vercel
    // where background start scripts do not run).
    if (
      !user &&
      (resolvedEmail === defaultSeedEmail ||
        (await AdminUser.countDocuments({ role: "admin" })) === 0) &&
      parsed.data.password === defaultSeedPassword
    ) {
      const passwordHash = await hashPassword(defaultSeedPassword);
      user = await AdminUser.create({
        name: process.env.SEED_ADMIN_NAME ?? "Admin",
        email:
          resolvedEmail === defaultSeedEmail ? defaultSeedEmail : resolvedEmail,
        passwordHash,
        role: "admin",
        active: true,
      });
    }

    let passwordMatches = await verifyPassword(
      parsed.data.password,
      user?.passwordHash ?? (await getDecoyHash()),
    );

    // If this is the seed admin account and the password matches SEED_ADMIN_PASSWORD,
    // sync the password in case it was reset.
    if (
      user &&
      !passwordMatches &&
      resolvedEmail === defaultSeedEmail &&
      parsed.data.password === defaultSeedPassword
    ) {
      const newHash = await hashPassword(defaultSeedPassword);
      await AdminUser.updateOne(
        { _id: user._id },
        { $set: { passwordHash: newHash, active: true } },
      );
      passwordMatches = true;
    }

    // One message for every failure mode: unknown email, wrong password, and
    // deactivated account are indistinguishable to the caller.
    if (!user || !user.active || !passwordMatches) {
      return { error: "Email or password is incorrect." };
    }

    await AdminUser.updateOne(
      { _id: user._id },
      { $set: { lastLoginAt: new Date() } },
    );

    await startSession({
      sub: user._id.toString(),
      name: user.name,
      email: user.email,
      role: user.role,
    });

    const next = formData.get("next");
    // Only same-site admin paths, so `next` cannot become an open redirect.
    if (typeof next === "string" && /^\/admin(?:[/?#]|$)/.test(next)) {
      destination = next;
    }
  } catch (error) {
    console.error("[login] failed", error);
    return {
      error:
        "Could not reach the database. Check the server configuration and try again.",
    };
  }

  redirect(destination);
}

export async function signOut(): Promise<void> {
  await endSession();
  redirect("/login");
}
