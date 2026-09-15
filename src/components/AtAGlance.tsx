import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { glanceFigures, headlineFigure } from "@/lib/content";

export function AtAGlance() {
  return (
    <section id="at-a-glance" className="shell py-24 md:py-32">
      <Reveal>
        <SectionHeading
          index="01"
          title="At a Glance"
          lead="The Society's mobilization is deliberately granular: a large target reached through small, equally priced units, so that a founding cohort of two hundred can hold it between them without any one member dominating."
        />
      </Reveal>

      <Reveal delay={80}>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
          <div className="lg:col-span-4">
            <p className="figure-num text-[4rem] leading-none text-forest-800 sm:text-[5rem]">
              {headlineFigure.value}
            </p>
            <p className="label mt-5 text-gold-700">{headlineFigure.label}</p>
            <p className="mt-4 max-w-xs text-[0.9375rem] leading-relaxed text-ink-soft">
              {headlineFigure.note}
            </p>
          </div>

          <div className="lg:col-span-8">
            <dl className="grid grid-cols-2 border-t border-l border-rule sm:grid-cols-3">
              {glanceFigures.map((figure) => (
                <div
                  key={figure.label}
                  className="border-r border-b border-rule px-5 py-7 sm:px-6 sm:py-8"
                >
                  <dd className="figure-num text-[1.5rem] leading-none text-forest-900 sm:text-[1.875rem]">
                    {figure.value}
                  </dd>
                  <dt className="label-sm mt-4 text-ink-faint">
                    {figure.label}
                  </dt>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
