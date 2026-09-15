import Link from "next/link";
import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { email, joinCaveat, joinSteps, phones } from "@/lib/content";

export function HowToJoin() {
  return (
    <section id="join" className="bg-paper-alt py-24 md:py-32">
      <div className="shell">
        <Reveal>
          <SectionHeading
            index="08"
            title="How to Join"
            lead="Four steps, in order. The Society is at the point of constituting its founding cohort of two hundred members."
          />
        </Reveal>

        <Reveal delay={80}>
          <ol className="grid gap-x-10 sm:grid-cols-2 lg:grid-cols-4">
            {joinSteps.map((step, index) => (
              <li key={step.title} className="border-t border-rule pt-7 pb-9">
                <span className="figure-num block text-[2rem] leading-none text-gold-600">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="font-display mt-6 text-[1.125rem] leading-snug text-forest-900">
                  {step.title}
                </h3>
                <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-soft">
                  {step.body}
                </p>
              </li>
            ))}
          </ol>
        </Reveal>

        <Reveal delay={140}>
          <p className="mt-10 max-w-3xl border-l-2 border-gold-600 pl-5 text-[0.9375rem] leading-relaxed text-ink-soft">
            {joinCaveat}
          </p>
        </Reveal>

        <Reveal delay={180}>
          <div className="mt-16 bg-forest-950 px-7 py-12 text-paper sm:px-12 sm:py-14">
            <div className="grid gap-10 lg:grid-cols-12 lg:items-center lg:gap-12">
              <div className="lg:col-span-6">
                <h3 className="font-display text-[1.75rem] leading-[1.2] text-balance sm:text-[2.125rem]">
                  Register your interest with the Secretariat
                </h3>
                <p className="mt-4 max-w-md text-[1.0625rem] leading-relaxed text-paper/70">
                  Complete the short form and we will be in touch. Membership
                  documentation follows once the Board finalises it.
                </p>
                <Link
                  href="/join"
                  className="label mt-8 inline-block bg-gold-400 px-7 py-4 text-forest-950 transition-colors duration-200 hover:bg-gold-300"
                >
                  Register Your Interest
                </Link>
              </div>

              <div className="lg:col-span-6">
                <dl className="grid gap-x-8 sm:grid-cols-2">
                  <div className="border-t border-paper/20 pt-5 pb-2">
                    <dt className="label-sm text-paper/55">Telephone</dt>
                    <dd className="mt-3 space-y-1.5">
                      {phones.map((phone) => (
                        <a
                          key={phone}
                          href={`tel:${phone.replace(/\s/g, "")}`}
                          className="block text-[0.9375rem] text-gold-300 tnum transition-colors duration-200 hover:text-gold-400"
                        >
                          {phone}
                        </a>
                      ))}
                    </dd>
                  </div>
                  <div className="border-t border-paper/20 pt-5 pb-2">
                    <dt className="label-sm text-paper/55">Email</dt>
                    <dd className="mt-3">
                      <a
                        href={`mailto:${email.address}`}
                        className="block text-[0.9375rem] break-all text-gold-300 transition-colors duration-200 hover:text-gold-400"
                      >
                        {email.address}
                      </a>
                      {email.provisional ? (
                        <span className="label-sm mt-2 block text-paper/55">
                          Interim address
                        </span>
                      ) : null}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
