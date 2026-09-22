import { Reveal } from "./Reveal";
import { about, mission, vision } from "@/lib/content";

/**
 * About section presenting the Society's legal background,
 * member-driven purpose, and strategic Vision & Mission statements.
 *
 * Fully integrated with Overstand's signature brand design tokens:
 * deep navy grounds, gold accents, Fraunces display typography,
 * and high-contrast paper/ink surfaces.
 */
export function About() {
  return (
    <section id="about" className="py-20 md:py-28">
      <div className="shell space-y-8 md:space-y-12">
        {/* ── 01: About Us Panel ───────────────────────────────────── */}
        <Reveal>
          <div className="card relative overflow-hidden bg-white p-8 md:p-12 lg:p-14">
            <div className="relative max-w-4xl">
              {/* Eyebrow badge in navy and gold */}
              <div className="inline-flex items-center rounded-full border border-gold-500/35 bg-navy-900 px-4 py-1.5">
                <span className="label text-gold-400">
                  {about.badge}
                </span>
              </div>

              {/* Display Headline in Fraunces serif & Navy 900 */}
              <h2 className="font-display mt-6 text-[1.875rem] font-normal tracking-[-0.02em] text-navy-900 sm:text-[2.25rem] md:text-[2.625rem]">
                {about.heading}
              </h2>

              <span
                aria-hidden="true"
                className="mt-6 block h-px w-16 bg-gold-600/50"
              />

              {/* Main statutory & purpose narrative */}
              <p className="mt-6 text-[1.0625rem] leading-[1.8] text-ink-soft md:text-[1.125rem]">
                {about.body}
              </p>

              {/* Core service opportunities */}
              <div className="mt-8 flex flex-wrap gap-2.5 pt-2">
                {about.servicesSummary.map((item) => (
                  <span
                    key={item}
                    className="label-sm inline-flex items-center rounded-md border border-rule bg-paper-alt px-3.5 py-1.5 text-navy-900"
                  >
                    <span
                      aria-hidden="true"
                      className="mr-2 h-1.5 w-1.5 rounded-full bg-gold-500"
                    />
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Reveal>

        {/* ── 02: Vision & Mission Statement Grid ──────────────────── */}
        <div className="grid gap-6 md:grid-cols-2 md:gap-8">
          {/* Vision Statement Card */}
          <Reveal delay={60}>
            <article className="flex h-full flex-col justify-between rounded-xl border border-gold-500/20 bg-navy-900 p-8 text-paper md:p-10">
              <div>
                <span className="label text-gold-400">Pillar 01</span>
                <h3 className="font-display mt-4 text-[1.375rem] font-normal tracking-[0.03em] text-paper uppercase sm:text-[1.625rem]">
                  {vision.heading}
                </h3>
                <span
                  aria-hidden="true"
                  className="mt-5 block h-px w-14 bg-gold-500/50"
                />

                <p className="mt-6 text-[1.0625rem] leading-[1.75] font-normal text-paper/85 sm:text-[1.125rem]">
                  {vision.body}
                </p>
              </div>

              <div className="mt-8 border-t border-paper/10 pt-6">
                <p className="label-sm text-gold-400/80">
                  Transforming lives · Sustainable growth
                </p>
              </div>
            </article>
          </Reveal>

          {/* Mission Statement Card */}
          <Reveal delay={120}>
            <article className="flex h-full flex-col justify-between rounded-xl border border-gold-500/20 bg-navy-900 p-8 text-paper md:p-10">
              <div>
                <span className="label text-gold-400">Pillar 02</span>
                <h3 className="font-display mt-4 text-[1.375rem] font-normal tracking-[0.03em] text-paper uppercase sm:text-[1.625rem]">
                  {mission.heading}
                </h3>
                <span
                  aria-hidden="true"
                  className="mt-5 block h-px w-14 bg-gold-500/50"
                />

                <p className="mt-6 text-[1.0625rem] leading-[1.75] font-normal text-paper/85 sm:text-[1.125rem]">
                  {mission.body}
                </p>

                <p className="mt-4 text-[0.9375rem] leading-[1.7] text-paper/65">
                  {mission.support}
                </p>
              </div>

              <div className="mt-8 border-t border-paper/10 pt-6">
                <p className="label-sm text-gold-400/80">
                  Credible · Transparent · Professionally Managed
                </p>
              </div>
            </article>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
