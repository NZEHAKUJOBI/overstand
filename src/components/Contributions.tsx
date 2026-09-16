import Link from "next/link";
import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { contributions } from "@/lib/content";

/**
 * The monthly contribution tiers, and the notice that they are a floor rather
 * than a ceiling. The flexibility notice is given its own panel because it is
 * the Society's own emphasis — the tiers are described as inclusive, not
 * restrictive, and a tier table alone would imply the opposite.
 */
export function Contributions() {
  return (
    <section id="contributions" className="bg-paper-alt py-24 md:py-32">
      <div className="shell">
        <SectionHeading
          eyebrow="Contributions"
          title={contributions.heading}
          lead={contributions.lead}
        />

        <div className="mx-auto grid max-w-4xl gap-5 sm:grid-cols-2">
          {contributions.tiers.map((tier, index) => (
            <Reveal key={tier.name} delay={index * 80}>
              <article className="flex h-full flex-col rounded-xl border border-rule bg-white p-8 md:p-10">
                <p className="label text-gold-700">{tier.name}</p>

                <p className="figure-num mt-5 text-[2.75rem] leading-none text-navy-900 md:text-[3.25rem]">
                  {tier.amount}
                </p>
                <p className="label-sm mt-3 text-ink-faint">{tier.cadence}</p>

                <span
                  aria-hidden="true"
                  className="mt-7 block h-px w-12 bg-gold-600/45"
                />

                <p className="mt-7 text-[0.9375rem] leading-[1.65] text-ink-soft">
                  {tier.detail}
                </p>
              </article>
            </Reveal>
          ))}
        </div>

        <Reveal delay={160}>
          <aside className="mx-auto mt-6 max-w-4xl rounded-xl border border-gold-600/35 bg-gold-300/25 p-8 md:p-10">
            <p className="label text-gold-700">
              {contributions.flexibility.title}
            </p>
            <p className="mt-5 text-[1rem] leading-[1.7] text-pretty text-ink-soft">
              {contributions.flexibility.body}
            </p>
            <Link
              href="/join"
              className="label-sm mt-7 inline-block border-b border-gold-700/50 pb-1 text-navy-900 transition-colors duration-200 hover:border-gold-700 hover:text-gold-700"
            >
              Discuss a tailored structure
            </Link>
          </aside>
        </Reveal>
      </div>
    </section>
  );
}
