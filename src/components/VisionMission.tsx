import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { mission, values, vision } from "@/lib/content";

const statements = [vision, mission];

export function VisionMission() {
  return (
    <section id="vision" className="bg-paper-alt py-24 md:py-32">
      <div className="shell">
        <Reveal>
          <SectionHeading
            index="02"
            title="What the Society Stands For"
            lead="The statements below were drafted at the strategic meeting of 15 August 2026 and are recorded here as proposed. They carry no force until the Board formally adopts them."
          />
        </Reveal>

        <Reveal delay={80}>
          <div className="grid gap-px border-t border-rule bg-rule md:grid-cols-2">
            {statements.map((statement, index) => (
              <div
                key={statement.heading}
                className={`bg-paper-alt pt-8 pb-2 ${
                  index === 0 ? "md:pr-12" : "md:pl-12"
                }`}
              >
                <h3 className="label text-gold-700">{statement.heading}</h3>
                <p className="font-display mt-6 text-[1.375rem] leading-[1.5] text-pretty text-forest-900 italic sm:text-[1.5rem]">
                  “{statement.body}”
                </p>
                <p className="label-sm mt-7 flex items-center gap-2 text-ink-faint">
                  <span
                    aria-hidden="true"
                    className="inline-block h-1 w-1 rotate-45 bg-gold-600"
                  />
                  Proposed — pending Board ratification
                </p>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={140}>
          <div className="mt-20 md:mt-24">
            <h3 className="label text-gold-700">Core Values</h3>
            <ul className="mt-8 grid gap-x-10 sm:grid-cols-2 lg:grid-cols-3">
              {values.map((value, index) => (
                <li
                  key={value.title}
                  className="border-t border-rule pt-7 pb-9"
                >
                  <span className="label-sm text-gold-700">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <h4 className="font-display mt-4 text-[1.1875rem] leading-snug text-forest-900">
                    {value.title}
                  </h4>
                  <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-soft">
                    {value.body}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
