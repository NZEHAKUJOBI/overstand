"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Crest } from "./Crest";
import { navigation, society } from "@/lib/content";

export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string>("");

  // Solid bar only once the masthead has left the hero.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Track which section owns the upper third of the viewport.
  useEffect(() => {
    const sections = navigation
      .map((item) => document.getElementById(item.id))
      .filter((el): el is HTMLElement => el !== null);

    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-20% 0px -68% 0px" },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, []);

  // Close the mobile panel when the viewport grows past the breakpoint.
  useEffect(() => {
    if (!open) return;
    const mq = window.matchMedia("(min-width: 1024px)");
    const close = () => mq.matches && setOpen(false);
    mq.addEventListener("change", close);
    return () => mq.removeEventListener("change", close);
  }, [open]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-500 ${
        scrolled || open
          ? "bg-forest-950/95 backdrop-blur-sm"
          : "bg-transparent"
      }`}
    >
      <div
        aria-hidden="true"
        className={`h-px w-full transition-opacity duration-500 ${
          scrolled || open ? "bg-gold-500/45 opacity-100" : "opacity-0"
        } absolute bottom-0`}
      />

      <div className="shell flex h-16 items-center justify-between gap-6">
        <a
          href="#top"
          className="group flex items-center gap-3 text-paper"
          aria-label={`${society.name} — back to top`}
        >
          <Crest
            size={32}
            priority
            className="h-8 w-8 shrink-0 transition-opacity duration-300 group-hover:opacity-80"
          />
          <span className="hidden sm:block">
            <span className="font-display block text-[0.9375rem] leading-tight tracking-[0.005em]">
              {society.name}
            </span>
            <span className="label-sm block text-gold-400/75">
              Cooperative Society Limited
            </span>
          </span>
        </a>

        <nav aria-label="Primary" className="hidden lg:block">
          <ul className="flex items-center gap-7">
            {navigation.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  aria-current={active === item.id ? "true" : undefined}
                  className={`label-sm relative py-2 transition-colors duration-200 ${
                    active === item.id
                      ? "text-gold-300"
                      : "text-paper/70 hover:text-paper"
                  }`}
                >
                  {item.label}
                  <span
                    aria-hidden="true"
                    className={`absolute -bottom-0.5 left-0 h-px bg-gold-400 transition-all duration-300 ${
                      active === item.id ? "w-full" : "w-0"
                    }`}
                  />
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/join"
            className="label-sm hidden border border-gold-500/60 px-4 py-2.5 text-gold-300 transition-colors duration-200 hover:border-gold-400 hover:bg-gold-400 hover:text-forest-950 sm:inline-block"
          >
            Become a Member
          </Link>

          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-nav"
            className="flex h-10 w-10 items-center justify-center text-paper lg:hidden"
          >
            <span className="sr-only">
              {open ? "Close menu" : "Open menu"}
            </span>
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
              {open ? (
                <path d="M6 6 L18 18 M18 6 L6 18" />
              ) : (
                <path d="M3.5 7.5 H20.5 M3.5 16.5 H20.5" />
              )}
            </svg>
          </button>
        </div>
      </div>

      <div
        id="mobile-nav"
        hidden={!open}
        className="border-t border-gold-500/20 lg:hidden"
      >
        <nav aria-label="Primary (compact)" className="shell py-5">
          <ul className="grid gap-1">
            {navigation.map((item) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  onClick={() => setOpen(false)}
                  className="label-sm block border-b border-paper/10 py-3 text-paper/80"
                >
                  {item.label}
                </a>
              </li>
            ))}
            <li className="pt-4">
              <Link
                href="/join"
                onClick={() => setOpen(false)}
                className="label-sm block bg-gold-400 px-4 py-3 text-center text-forest-950"
              >
                Become a Member
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
