import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import {
  boardOfTrustees,
  executive,
  executiveSecond,
  executiveThird,
  governanceNote,
  type Office,
} from "@/lib/content";

const LINE = "bg-forest-900/18";

function OfficeCard({ office, holder, vacant }: Office) {
  return (
    <div
      className={`flex h-full flex-col justify-center bg-paper px-5 py-5 text-center ${
        vacant
          ? "border border-dashed border-forest-900/25"
          : "border border-forest-900/20"
      }`}
    >
      <p
        className={`label-sm ${vacant ? "text-ink-faint" : "text-gold-700"}`}
      >
        {office}
      </p>
      <p
        className={`font-display mt-2.5 text-[1.0625rem] leading-snug ${
          vacant ? "text-ink-faint italic" : "text-forest-900"
        }`}
      >
        {holder}
      </p>
    </div>
  );
}

/** Vertical drop from a single box down to the bus below. */
function Drop() {
  return (
    <div aria-hidden="true" className="flex h-7 justify-center">
      <span className={`block w-px ${LINE}`} />
    </div>
  );
}

/** Horizontal bus spanning the centres of three columns, with three drops. */
function Bus() {
  return (
    <div aria-hidden="true" className="relative h-8">
      <span
        className={`absolute top-0 right-[16.666%] left-[16.666%] h-px ${LINE}`}
      />
      <div className="grid h-full grid-cols-3">
        {[0, 1, 2].map((i) => (
          <span key={i} className={`mx-auto block w-px ${LINE}`} />
        ))}
      </div>
    </div>
  );
}

export function Governance() {
  const stacked = [...executive, ...executiveSecond, ...executiveThird];

  return (
    <section id="governance" className="shell py-24 md:py-32">
      <Reveal>
        <SectionHeading
          index="03"
          title="Governance & Leadership"
          lead="A cooperative is only as sound as the people accountable for it. The executive committee below is the structure of record as at 20 August 2026; two offices are not yet filled, and are shown as such."
        />
      </Reveal>

      <Reveal delay={80}>
        {/* Full chart — from the medium breakpoint up. */}
        <div className="hidden md:block">
          <div className="mx-auto max-w-xs">
            <OfficeCard {...executive[0]} />
          </div>
          <Drop />
          <Bus />
          <div className="grid grid-cols-3 gap-6">
            {executiveSecond.map((person) => (
              <OfficeCard key={person.office} {...person} />
            ))}
          </div>
          <Drop />
          <Bus />
          <div className="grid grid-cols-3 gap-6">
            {executiveThird.map((person) => (
              <OfficeCard key={person.office} {...person} />
            ))}
          </div>
        </div>

        {/* Compact list — a single spine instead of a chart. */}
        <ol className="space-y-4 border-l border-forest-900/15 pl-6 md:hidden">
          {stacked.map((person) => (
            <li key={person.office} className="relative">
              <span
                aria-hidden="true"
                className={`absolute top-1/2 -left-6 h-px w-4 ${LINE}`}
              />
              <OfficeCard {...person} />
            </li>
          ))}
        </ol>

        <p className="label-sm mt-8 text-ink-faint">{governanceNote}</p>
      </Reveal>

      <Reveal delay={140}>
        <div className="mt-16 bg-forest-900 px-7 py-10 text-paper sm:px-12 sm:py-12">
          <div aria-hidden="true" className="mb-8 h-px w-16 bg-gold-500" />
          <div className="grid gap-8 lg:grid-cols-12 lg:gap-12">
            <h3 className="label text-gold-400 lg:col-span-3">
              {boardOfTrustees.title}
            </h3>
            <div className="lg:col-span-9">
              <p className="font-display text-[1.25rem] leading-[1.55] text-pretty text-paper/90 sm:text-[1.375rem]">
                {boardOfTrustees.body}
              </p>
              <p className="label-sm mt-6 text-paper/60">
                {boardOfTrustees.tenure}
              </p>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
