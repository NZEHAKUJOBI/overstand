/**
 * Creates (or updates) an administrator account, so there is a way in before
 * any account exists.
 *
 *   npm run seed:admin -- --name "TPL Lami" --email lami@example.org \
 *                         --password "a-long-passphrase" --role admin
 *
 * Re-running with the same email resets that account's password and role.
 */

import { existsSync } from "node:fs";
import { connectDb } from "../src/lib/db";
import { AdminUser } from "../src/lib/models/AdminUser";
import { hashPassword } from "../src/lib/auth";
import { ROLES, ROLE_LABEL, isRole } from "../src/lib/rbac";

for (const file of [".env.local", ".env"]) {
  if (existsSync(file)) {
    process.loadEnvFile(file);
    break;
  }
}

function arg(name: string): string | undefined {
  const flag = `--${name}`;
  const index = process.argv.indexOf(flag);

  if (index !== -1 && process.argv[index + 1]) return process.argv[index + 1];

  const inline = process.argv.find((value) => value.startsWith(`${flag}=`));
  return inline?.slice(flag.length + 1);
}

function fail(message: string): never {
  console.error(`\n  ✗ ${message}\n`);
  process.exit(1);
}

async function main() {
  const name = arg("name") ?? process.env.SEED_ADMIN_NAME ?? "Admin";
  const email = (
    arg("email") ??
    process.env.SEED_ADMIN_EMAIL ??
    "admin@anchorrealestategroup.ng"
  )?.toLowerCase();
  const password =
    arg("password") ?? process.env.SEED_ADMIN_PASSWORD ?? "123456789";
  const role = arg("role") ?? process.env.SEED_ADMIN_ROLE ?? "admin";

  if (!name) fail("Missing --name");
  if (!email) fail("Missing --email");
  if (!password) fail("Missing --password");
  if (password.length < 6) fail("Password must be at least 6 characters.");
  if (!isRole(role)) fail(`Role must be one of: ${ROLES.join(", ")}`);
  if (!process.env.MONGODB_URI) {
    console.log("  ℹ MONGODB_URI is not set. Skipping admin seed.");
    process.exit(0);
  }

  await connectDb();

  const existing = await AdminUser.findOne({ email });
  const passwordHash = await hashPassword(password);

  if (existing) {
    await AdminUser.updateOne(
      { _id: existing._id },
      { $set: { name, passwordHash, role, active: true } },
    );
    console.log(
      `\n  ✓ Updated ${email} — ${ROLE_LABEL[role]} (password reset, account active)\n`,
    );
  } else {
    await AdminUser.create({ name, email, passwordHash, role, active: true });
    console.log(`\n  ✓ Created ${email} — ${ROLE_LABEL[role]}\n`);
  }

  console.log("  Sign in at /login\n");
  process.exit(0);
}

main().catch((error) => {
  console.error("\n  ✗ Seeding failed:", error);
  process.exit(1);
});
