import Link from "next/link";
import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { contactNote, joinCaveat, joinSteps, offices } from "@/lib/content";

/**
 * The five steps to membership, as a numbered rail, with the office details
 * and the caveat alongside. The caveat is load-bearing: the online form starts
 * an application, it does not admit anybody and takes no payment, and the page
 * has to say so where somebody is about to click.
 */
export function HowToJoin() {
  return (
    <section id="join" className="bg-navy-950 py-24 text-paper md:py-32">
      <div className="shell">
        <SectionHeading
          eyebrow="How to join"
          title="Five steps to membership"
          tone="dark"
        />

        <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-7">
            <ol className="grid gap-px bg-paper/12">
              {joinSteps.map((step, index) => (
                <Reveal key={step.title} delay={index * 60}>
                  <li className="flex gap-6 bg-navy-950 py-7">
                    <span
                      aria-hidden="true"
                      className="figure-num w-8 shrink-0 text-[1.25rem] leading-none text-gold-500"
                    >
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <div>
                      <h3 className="font-display text-[1.1875rem] leading-snug text-paper">
                        {step.title}
                      </h3>
                      <p className="mt-2.5 text-[0.9375rem] leading-[1.7] text-pretty text-paper/65">
                        {step.body}
                      </p>
                    </div>
                  </li>
                </Reveal>
              ))}
            </ol>
          </div>

          <div className="lg:col-span-5">
            <Reveal delay={120}>
              <div className="rounded-xl border border-gold-500/30 bg-paper/[0.04] p-8 md:p-9">
                <h3 className="font-display text-[1.375rem] leading-snug text-paper">
                  Start your application
                </h3>

                <p className="mt-4 text-[0.9375rem] leading-[1.7] text-pretty text-paper/65">
                  {joinCaveat}
                </p>

                <Link
                  href="/join"
                  className="label mt-8 block bg-gold-400 px-6 py-4 text-center text-navy-950 transition-colors duration-200 hover:bg-gold-300"
                >
                  Apply for membership
                </Link>
              </div>
            </Reveal>

            <Reveal delay={180}>
              <div className="mt-6 rounded-xl border border-paper/12 p-8 md:p-9">
                <p className="text-[0.9375rem] leading-[1.7] text-pretty text-paper/65">
                  {contactNote}
                </p>

                {offices.map((office) => (
                  <div key={office.label} className="mt-7">
                    <p className="label-sm text-gold-400/75">{office.label}</p>
                    <address className="mt-3 text-[0.9375rem] leading-[1.7] text-paper/80 not-italic">
                      {office.lines.map((line) => (
                        <span key={line} className="block">
                          {line}
                        </span>
                      ))}
                    </address>
                  </div>
                ))}
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
}
