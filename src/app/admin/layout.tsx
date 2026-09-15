import type { Metadata } from "next";
import { AdminSidebar, type NavItem } from "@/components/admin/AdminSidebar";
import { requireSession } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { signOut } from "../login/actions";

export const metadata: Metadata = {
  title: { default: "Secretariat", template: "%s · Anchor Secretariat" },
  robots: { index: false, follow: false },
};

/** Admin pages read live data on every request. */
export const dynamic = "force-dynamic";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await requireSession();

  const items: NavItem[] = [
    { href: "/admin", label: "Overview" },
    ...(can(session.role, "members:read")
      ? [{ href: "/admin/members", label: "Members" }]
      : []),
    ...(can(session.role, "payments:read")
      ? [{ href: "/admin/payments", label: "Payments" }]
      : []),
    ...(can(session.role, "enquiries:read")
      ? [{ href: "/admin/applications", label: "Enquiries" }]
      : []),
    ...(can(session.role, "users:manage")
      ? [{ href: "/admin/users", label: "Admin Users" }]
      : []),
    ...(can(session.role, "audit:read")
      ? [{ href: "/admin/activity", label: "Activity" }]
      : []),
  ];

  return (
    <div className="flex min-h-screen flex-col bg-paper lg:flex-row">
      <AdminSidebar items={items} user={session} signOut={signOut} />
      <main className="min-w-0 flex-1 px-5 py-8 sm:px-8 lg:px-12 lg:py-12">
        {children}
      </main>
    </div>
  );
}
