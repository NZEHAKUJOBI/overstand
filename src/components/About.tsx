import { about } from "@/lib/content";
import { Reveal } from "./Reveal";

export function About() {
  return (
    <section id="about" className="bg-paper-alt py-16 md:py-20">
      <div className="shell">
        <Reveal>
          <div className="card px-6 py-10 sm:px-10 md:px-14 md:py-12">
            <span className="label inline-flex rounded-full bg-navy-900 px-5 py-2 text-gold-400">
              {about.eyebrow}
            </span>

            <h2 className="font-display mt-9 text-[2.25rem] leading-[1.08] font-normal tracking-[-0.025em] text-balance text-navy-900 sm:text-[2.5rem] md:text-[3rem] xl:whitespace-nowrap">
              {about.heading}
            </h2>

            <span
              aria-hidden="true"
              className="mt-9 block h-px w-16 bg-gold-600/60"
            />

            <p className="mt-8 max-w-6xl text-[1.0625rem] leading-[1.85] text-pretty text-ink-soft md:text-[1.125rem]">
              {about.body}
            </p>

            <ul className="mt-9 flex flex-wrap gap-2" aria-label="What we help members achieve">
              {about.highlights.map((highlight) => (
                <li
                  key={highlight}
                  className="label-sm flex items-center gap-2.5 rounded-md border border-rule bg-paper-alt px-3.5 py-2 text-navy-900"
                >
                  <span
                    aria-hidden="true"
                    className="h-1.5 w-1.5 shrink-0 rounded-full bg-gold-500"
                  />
                  {highlight}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
