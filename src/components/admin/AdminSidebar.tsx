"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Crest } from "@/components/Crest";
import { ROLE_LABEL, type Role } from "@/lib/rbac";

export type NavItem = { href: string; label: string };

export function AdminSidebar({
  items,
  user,
  signOut,
}: {
  items: NavItem[];
  user: { name: string; email: string; role: Role };
  signOut: () => Promise<void>;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isCurrent = (href: string) =>
    href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);

  return (
    <>
      {/* Compact bar, below lg */}
      <div className="flex items-center justify-between border-b border-gold-500/25 bg-forest-950 px-5 py-3 lg:hidden">
        <Link href="/admin" className="flex items-center gap-3 text-paper">
          <Crest size={28} className="h-7 w-7" />
          <span className="label-sm">Anchor Admin</span>
        </Link>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="admin-nav"
          className="flex h-9 w-9 items-center justify-center text-paper"
        >
          <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
          >
            {open ? (
              <path d="M6 6 L18 18 M18 6 L6 18" />
            ) : (
              <path d="M3.5 7.5 H20.5 M3.5 16.5 H20.5" />
            )}
          </svg>
        </button>
      </div>

      <aside
        id="admin-nav"
        className={`${open ? "block" : "hidden"} bg-forest-950 lg:sticky lg:top-0 lg:block lg:h-screen lg:w-64 lg:shrink-0`}
      >
        <div className="flex h-full flex-col">
          <Link
            href="/admin"
            className="hidden items-center gap-3 px-6 py-6 text-paper lg:flex"
          >
            <Crest size={36} className="h-9 w-9 shrink-0" />
            <span>
              <span className="font-display block text-[0.9375rem] leading-tight">
                Anchor Admin
              </span>
              <span className="label-sm block text-gold-400/75">
                Secretariat
              </span>
            </span>
          </Link>

          <nav aria-label="Admin" className="flex-1 px-3 py-3 lg:py-2">
            <ul className="space-y-0.5">
              {items.map((item) => {
                const current = isCurrent(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={() => setOpen(false)}
                      aria-current={current ? "page" : undefined}
                      className={`label-sm block border-l-2 px-4 py-3 transition-colors duration-150 ${
                        current
                          ? "border-gold-400 bg-paper/8 text-gold-300"
                          : "border-transparent text-paper/65 hover:bg-paper/5 hover:text-paper"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="border-t border-paper/12 px-6 py-5">
            <p className="text-[0.875rem] leading-tight text-paper">
              {user.name}
            </p>
            <p className="label-sm mt-1.5 text-gold-400/80">
              {ROLE_LABEL[user.role]}
            </p>
            <form action={signOut} className="mt-4">
              <button
                type="submit"
                className="label-sm text-paper/55 underline-offset-4 transition-colors duration-150 hover:text-paper hover:underline"
              >
                Sign out
              </button>
            </form>
            <Link
              href="/"
              className="label-sm mt-3 block text-paper/40 transition-colors duration-150 hover:text-paper/70"
            >
              View public site
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
}
