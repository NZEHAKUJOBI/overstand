import type { ReactNode } from "react";

/**
 * Numbered section head. The index sits in the left gutter against a gold
 * hairline that runs out to the measure — the device that ties the page
 * together in place of boxes or cards.
 */
export function SectionHeading({
  index,
  title,
  lead,
  tone = "light",
}: {
  index: string;
  title: string;
  lead?: ReactNode;
  tone?: "light" | "dark";
}) {
  const dark = tone === "dark";

  return (
    <header className="mb-12 md:mb-16">
      <div className="flex items-center gap-4">
        <span
          className={`label-sm shrink-0 ${dark ? "text-gold-400" : "text-gold-700"}`}
        >
          {index}
        </span>
        <span
          aria-hidden="true"
          className={`h-px flex-1 ${dark ? "bg-gold-400/30" : "bg-gold-600/35"}`}
        />
      </div>

      <h2
        className={`font-display mt-5 text-[2rem] leading-[1.12] font-normal tracking-[-0.02em] text-balance sm:text-[2.5rem] md:text-[3rem] ${
          dark ? "text-paper" : "text-forest-900"
        }`}
      >
        {title}
      </h2>

      {lead ? (
        <p
          className={`mt-5 max-w-2xl text-[1.0625rem] leading-[1.6] text-pretty ${
            dark ? "text-paper/70" : "text-ink-soft"
          }`}
        >
          {lead}
        </p>
      ) : null}
    </header>
  );
}
