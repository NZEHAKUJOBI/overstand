import type { ReactNode } from "react";

/**
 * Section head: a gold eyebrow over the title, with a short gold rule beneath.
 * Centred by default — the page is built from cards and bands rather than a
 * single running measure, so the heads sit above their grids instead of
 * hanging in a left gutter.
 */
export function SectionHeading({
  eyebrow,
  title,
  lead,
  tone = "light",
  align = "center",
}: {
  eyebrow: string;
  title: string;
  lead?: ReactNode;
  tone?: "light" | "dark";
  align?: "center" | "left";
}) {
  const dark = tone === "dark";
  const centred = align === "center";

  return (
    <header
      className={`mb-12 md:mb-16 ${centred ? "flex flex-col items-center text-center" : ""}`}
    >
      <span className={`label ${dark ? "text-gold-400" : "text-gold-700"}`}>
        {eyebrow}
      </span>

      <h2
        className={`font-display mt-4 text-[2rem] leading-[1.12] font-normal tracking-[-0.02em] text-balance sm:text-[2.5rem] md:text-[3rem] ${
          dark ? "text-paper" : "text-navy-900"
        }`}
      >
        {title}
      </h2>

      <span
        aria-hidden="true"
        className={`mt-6 h-px w-16 ${dark ? "bg-gold-400/50" : "bg-gold-600/50"}`}
      />

      {lead ? (
        <p
          className={`mt-6 max-w-2xl text-[1.0625rem] leading-[1.6] text-pretty ${
            dark ? "text-paper/70" : "text-ink-soft"
          }`}
        >
          {lead}
        </p>
      ) : null}
    </header>
  );
}
