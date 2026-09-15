import { Fragment } from "react";
import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { expansionNote, marketLanes } from "@/lib/content";

/** Turns down the page on narrow screens, along the lane on wide ones. */
function Arrow() {
  return (
    <span
      aria-hidden="true"
      className="flex shrink-0 items-center justify-center self-center py-2 sm:py-0"
    >
      <svg
        viewBox="0 0 40 12"
        className="h-3 w-8 rotate-90 text-gold-400/70 sm:rotate-0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M0 6 H34" />
        <path d="M29 2 L34 6 L29 10" />
      </svg>
    </span>
  );
}

function Node({ children, terminal }: { children: string; terminal?: boolean }) {
  return (
    <span
      className={`flex items-center px-5 py-4 text-center text-[0.9375rem] leading-snug text-balance sm:flex-1 sm:text-left ${
        terminal
          ? "border border-gold-400/45 bg-gold-400/10 text-gold-300"
          : "border border-paper/20 bg-paper/[0.04] text-paper/85"
      }`}
    >
      {children}
    </span>
  );
}

export function TargetMarket() {
  return (
    <section id="outlook" className="bg-forest-900 py-24 text-paper md:py-32">
      <div className="shell">
        <Reveal>
          <SectionHeading
            index="06"
            tone="dark"
            title="Target Market & Expansion"
            lead="Two routes to membership, sequenced rather than pursued at once. The first is the founding cohort; the second widens access once the schemes and the credit machinery behind them are proven."
          />
        </Reveal>

        <Reveal delay={80}>
          <div className="grid gap-px border-t border-paper/15 bg-paper/15">
            {marketLanes.map((lane) => (
              <div
                key={lane.tier}
                className="bg-forest-900 py-9 lg:grid lg:grid-cols-12 lg:items-center lg:gap-8"
              >
                <p className="label text-gold-400 lg:col-span-2">{lane.tier}</p>

                <div className="mt-6 flex flex-col sm:flex-row sm:items-stretch sm:gap-4 lg:col-span-10 lg:mt-0">
                  <Node>{lane.segment}</Node>
                  {lane.steps.map((step, index) => (
                    <Fragment key={step}>
                      <Arrow />
                      <Node terminal={index === lane.steps.length - 1}>
                        {step}
                      </Node>
                    </Fragment>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={140}>
          <p className="label-sm mt-8 text-paper/55">{expansionNote}</p>
        </Reveal>
      </div>
    </section>
  );
}
