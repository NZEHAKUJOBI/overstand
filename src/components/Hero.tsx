import Link from "next/link";
import { Crest } from "./Crest";
import { hero, society } from "@/lib/content";

/**
 * Opening panel. Navy field with a gold rule at the head, the crest set large
 * above the headline, and the registration badge carried inline — the Society
 * being registered and certified is the first thing the Official Update says,
 * so it is the first thing the page says too.
 */
export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-navy-950 text-paper">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px] bg-gold-500" />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(120% 80% at 50% -10%, rgba(36,90,147,0.45), transparent 62%)",
        }}
      />

      {/* Faint green wash at the foot, picking up the crest's third colour. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3"
        style={{
          backgroundImage:
            "radial-gradient(90% 100% at 80% 110%, rgba(47,125,82,0.35), transparent 70%)",
        }}
      />

      <div className="shell relative flex min-h-[92svh] flex-col items-center justify-center py-28 text-center md:py-32">
        <Crest size={112} priority className="h-20 w-20 md:h-28 md:w-28" />

        <p className="label mt-8 text-gold-400">{hero.eyebrow}</p>

        <h1 className="font-display mt-6 max-w-4xl text-[2.5rem] leading-[1.06] font-normal tracking-[-0.025em] text-balance sm:text-[3.25rem] md:text-[4rem]">
          {hero.heading}
        </h1>

        <p className="mt-7 max-w-2xl text-[1.0625rem] leading-[1.7] text-pretty text-paper/75 md:text-[1.125rem]">
          {hero.body}
        </p>

        <div className="mt-11 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <Link
            href="/join"
            className="label bg-gold-400 px-8 py-4 text-navy-950 transition-colors duration-200 hover:bg-gold-300"
          >
            {hero.primaryCta}
          </Link>
          <a
            href="#services"
            className="label border border-paper/25 px-8 py-4 text-paper transition-colors duration-200 hover:border-gold-400 hover:text-gold-300"
          >
            {hero.secondaryCta}
          </a>
        </div>

        <p className="label-sm mt-12 text-paper/50">
          {society.registration}
          <span aria-hidden="true" className="mx-2 text-gold-500/60">
            ·
          </span>
          {society.status}
        </p>
      </div>
    </section>
  );
}
