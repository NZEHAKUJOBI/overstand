import { Reveal } from "./Reveal";
import { about, glanceFigures, headlineFigure } from "@/lib/content";

/**
 * About section presenting the Society's key operational figures
 * and the primary statutory & purpose narrative.
 */
export function About() {
  return (
    <section id="about" className="bg-paper-alt py-16 md:py-24">
      <div id="at-a-glance" className="scroll-mt-24" />
      <div className="shell space-y-10 md:space-y-14">
        {/* ── 01: At a Glance Figures Band ────────────────────────── */}
        <Reveal>
          <div className="grid gap-6 items-stretch lg:grid-cols-12 lg:gap-8">
            {/* Left navy headline card */}
            <div className="flex flex-col justify-between rounded-2xl bg-navy-900 p-8 text-paper shadow-sm sm:p-10 md:p-12 lg:col-span-5">
              <div>
                <p className="label text-gold-400">{headlineFigure.label}</p>
                <p className="figure-num mt-4 text-[3rem] leading-none text-paper sm:text-[3.5rem] md:text-[4rem]">
                  {headlineFigure.value}
                </p>
                <span
                  aria-hidden="true"
                  className="my-7 block h-px w-14 bg-gold-500/50"
                />
                <p className="text-[0.9375rem] leading-[1.65] text-pretty text-paper/75">
                  {headlineFigure.note}
                </p>
              </div>
            </div>

            {/* Right statistics grid (3 columns x 2 rows) */}
            <div className="grid grid-cols-2 rounded-2xl border border-rule/70 bg-rule/70 p-px gap-px overflow-hidden shadow-sm sm:grid-cols-3 lg:col-span-7">
              {glanceFigures.map((figure) => (
                <div
                  key={figure.label}
                  className="flex flex-col justify-start gap-3 bg-paper-alt p-6 sm:p-7 md:p-8"
                >
                  <p className="figure-num text-[1.75rem] leading-none text-navy-900 sm:text-[2rem] md:text-[2.25rem]">
                    {figure.value}
                  </p>
                  <p className="label-sm text-ink-faint leading-normal">
                    {figure.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* ── 02: About Us White Card ─────────────────────────────── */}
        <Reveal delay={80}>
          <div className="card relative overflow-hidden rounded-2xl border border-rule/70 bg-white p-8 shadow-xs sm:p-12 md:p-14 lg:p-16">
            {/* Pill Eyebrow */}
            <div className="inline-flex items-center rounded-full bg-navy-950 px-4 py-1.5 shadow-xs">
              <span className="label text-[11px] text-paper">
                {about.eyebrow}
              </span>
            </div>

            {/* Display Headline */}
            <h2 className="font-display mt-7 text-[2rem] font-normal leading-[1.15] tracking-[-0.02em] text-navy-900 sm:text-[2.375rem] md:text-[2.75rem]">
              {about.heading}
            </h2>

            {/* Gold accent rule */}
            <span
              aria-hidden="true"
              className="my-7 block h-0.5 w-14 bg-gold-600/60"
            />

            {/* Statutory and purpose narrative */}
            <p className="max-w-4xl text-[1.0625rem] leading-[1.8] text-pretty text-ink-soft md:text-[1.125rem]">
              {about.body}
            </p>

            {/* Highlights Tags */}
            <ul
              className="mt-9 flex flex-wrap gap-2.5 sm:gap-3"
              aria-label="What we help members achieve"
            >
              {about.highlights.map((highlight) => (
                <li
                  key={highlight}
                  className="label-sm flex items-center gap-2.5 rounded-md border border-rule/80 bg-paper-alt px-3.5 py-2 text-navy-950 shadow-2xs"
                >
                  <span
                    aria-hidden="true"
                    className="h-1.5 w-1.5 shrink-0 rounded-full bg-gold-600"
                  />
                  {highlight}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
