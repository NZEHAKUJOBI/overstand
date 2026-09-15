/**
 * Roles mirror the Society's offices, so an account's access matches the
 * responsibility the office actually carries. Kept free of any Node or
 * Mongoose import: `middleware.ts` runs on the Edge runtime and imports Role
 * from here.
 */

export const ROLES = [
  "admin",
  "treasurer",
  "financial_secretary",
  "secretary",
  "viewer",
] as const;

export type Role = (typeof ROLES)[number];

export const PERMISSIONS = [
  "members:read",
  "members:write",
  "payments:read",
  "payments:write",
  "enquiries:read",
  "enquiries:write",
  "users:manage",
  "audit:read",
] as const;

export type Permission = (typeof PERMISSIONS)[number];

const MATRIX: Record<Role, readonly Permission[]> = {
  // Typically the President or Secretary General: full control, including
  // creating and deactivating other admin accounts.
  admin: [
    "members:read",
    "members:write",
    "payments:read",
    "payments:write",
    "enquiries:read",
    "enquiries:write",
    "users:manage",
    "audit:read",
  ],
  // Holds the funds: records money in, and maintains the register.
  treasurer: [
    "members:read",
    "members:write",
    "payments:read",
    "payments:write",
    "enquiries:read",
    "enquiries:write",
    "audit:read",
  ],
  // Books the receipts, but does not alter the register.
  financial_secretary: [
    "members:read",
    "payments:read",
    "payments:write",
    "enquiries:read",
  ],
  // Maintains the register and handles applications; cannot touch money.
  secretary: [
    "members:read",
    "members:write",
    "payments:read",
    "enquiries:read",
    "enquiries:write",
  ],
  viewer: ["members:read", "payments:read", "enquiries:read"],
};

export const ROLE_LABEL: Record<Role, string> = {
  admin: "Administrator",
  treasurer: "Treasurer",
  financial_secretary: "Financial Secretary",
  secretary: "Secretary",
  viewer: "Viewer",
};

export const ROLE_DESCRIPTION: Record<Role, string> = {
  admin: "Full access, including admin accounts.",
  treasurer: "Register and payments, with audit access.",
  financial_secretary: "Records payments; reads the register.",
  secretary: "Maintains the register; reads payments.",
  viewer: "Read-only access.",
};

export function can(role: Role, permission: Permission): boolean {
  return MATRIX[role].includes(permission);
}

export function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as readonly string[]).includes(value);
}
