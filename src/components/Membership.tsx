import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { fees, holdingBand, nonInvestorTier } from "@/lib/content";

const TICKS = Array.from({ length: 25 }, (_, i) => i);

function Endpoint({
  slots,
  amount,
  caption,
  align,
}: {
  slots: string;
  amount: string;
  caption: string;
  align: "left" | "right";
}) {
  return (
    <div className={align === "right" ? "text-left sm:text-right" : ""}>
      <p className="label-sm text-gold-700">{caption}</p>
      <p className="figure-num mt-3 text-[1.75rem] leading-none text-forest-900 sm:text-[2.125rem]">
        {amount}
      </p>
      <p className="mt-2.5 text-[0.9375rem] text-ink-soft tnum">{slots}</p>
    </div>
  );
}

export function Membership() {
  return (
    <section id="membership" className="bg-paper-alt py-24 md:py-32">
      <div className="shell">
        <Reveal>
          <SectionHeading
            index="04"
            title="Membership & Ownership"
            lead="Ownership is expressed in slots of ₦5,000 each. A member's stake is simply the number of slots held — nothing is discretionary, and nothing is negotiated case by case."
          />
        </Reveal>

        <Reveal delay={80}>
          <div className="border-t border-rule pt-10">
            <div className="flex items-start justify-between gap-8">
              <Endpoint
                caption={holdingBand.floor.caption}
                amount={holdingBand.floor.amount}
                slots={holdingBand.floor.slots}
                align="left"
              />
              <Endpoint
                caption={holdingBand.ceiling.caption}
                amount={holdingBand.ceiling.amount}
                slots={holdingBand.ceiling.slots}
                align="right"
              />
            </div>

            {/* Graduated scale between the floor and the ceiling. */}
            <div className="mt-10" aria-hidden="true">
              <div className="h-px w-full bg-forest-900/25" />
              <div className="flex items-start justify-between">
                {TICKS.map((tick) => {
                  const major = tick === 0 || tick === TICKS.length - 1;
                  const mid = tick % 6 === 0;
                  return (
                    <span
                      key={tick}
                      className={`w-px ${
                        major
                          ? "h-5 bg-gold-600"
                          : mid
                            ? "h-3.5 bg-forest-900/35"
                            : "h-2 bg-forest-900/20"
                      }`}
                    />
                  );
                })}
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-baseline sm:justify-between">
              <p className="label-sm text-ink-faint">
                {holdingBand.scaleNote}
              </p>
              <p className="label-sm text-gold-700">{holdingBand.capNote}</p>
            </div>
          </div>
        </Reveal>

        <Reveal delay={140}>
          <dl className="mt-16 grid gap-x-10 sm:grid-cols-3">
            {fees.map((fee) => (
              <div
                key={fee.detail}
                className="border-t border-rule pt-7 pb-9"
              >
                <dt className="label-sm text-ink-faint">{fee.label}</dt>
                <dd>
                  <p className="figure-num mt-3 text-[1.875rem] leading-none text-forest-900">
                    {fee.amount}
                  </p>
                  <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink-soft">
                    {fee.detail}
                  </p>
                </dd>
              </div>
            ))}
          </dl>
        </Reveal>

        <Reveal delay={180}>
          <div className="mt-14 border-l-2 border-gold-600 bg-paper px-6 py-7 sm:px-8">
            <h3 className="label text-gold-700">{nonInvestorTier.title}</h3>
            <p className="mt-3 max-w-2xl text-[1.0625rem] leading-relaxed text-pretty text-ink">
              {nonInvestorTier.body}
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
