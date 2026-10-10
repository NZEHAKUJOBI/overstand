import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { eligibility, fees } from "@/lib/content";

/**
 * Who may join, and what joining costs.
 *
 * Two fee amounts are named by the Society without a figure. They render as
 * "confirm at the office" and are marked visually, rather than being given an
 * invented number or quietly dropped — a page inviting monthly commitments
 * should not be vague about money by accident.
 */
export function Membership() {
  return (
    <section id="membership" className="py-24 md:py-32">
      <div className="shell">
        <SectionHeading
          eyebrow="Membership"
          title="Joining the Society"
          lead="Membership is open to individuals building structured wealth through collective investment."
        />

        <div className="grid gap-6 lg:grid-cols-12 lg:gap-8">
          <Reveal className="lg:col-span-4">
            <div className="h-full rounded-xl border border-rule bg-white p-8">
              <h3 className="font-display text-[1.375rem] leading-snug text-navy-900">
                {eligibility.heading}
              </h3>

              <ul className="mt-7 grid gap-4">
                {eligibility.criteria.map((criterion) => (
                  <li key={criterion} className="flex items-start gap-3">
                    <svg
                      viewBox="0 0 20 20"
                      aria-hidden="true"
                      className="mt-0.5 h-5 w-5 shrink-0 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <circle cx="10" cy="10" r="8" />
                      <path d="m6.5 10.2 2.4 2.4 4.6-4.9" />
                    </svg>
                    <span className="text-[0.9375rem] leading-[1.6] text-ink-soft">
                      {criterion}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

          <Reveal delay={80} className="lg:col-span-8">
            <div className="h-full rounded-xl border border-rule bg-white">
              <h3 className="font-display border-b border-rule px-8 py-6 text-[1.375rem] leading-snug text-navy-900">
                What joining costs
              </h3>

              <ul>
                {fees.map((fee) => (
                  <li
                    key={fee.label}
                    className="grid gap-2 border-b border-rule px-8 py-6 last:border-b-0 sm:grid-cols-12 sm:items-baseline sm:gap-6"
                  >
                    <p
                      className={`sm:col-span-4 ${
                        fee.provisional
                          ? "label-sm text-ink-faint"
                          : "figure-num text-[1.75rem] leading-none text-navy-900"
                      }`}
                    >
                      {fee.amount}
                    </p>

                    <div className="sm:col-span-8">
                      <p className="label-sm text-gold-700">{fee.label}</p>
                      <p className="mt-2 text-[0.9375rem] leading-[1.65] text-pretty text-ink-soft">
                        {fee.detail}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
