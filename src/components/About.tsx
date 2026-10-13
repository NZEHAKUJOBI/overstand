import { about } from "@/lib/content";
import { Reveal } from "./Reveal";

export function About() {
  return (
    <section id="about" className="py-24 md:py-32">
      <div className="shell">
        <Reveal>
          <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
            <span className="label text-gold-700">
              {about.eyebrow}
            </span>

            <h2 className="font-display mt-7 text-[2rem] leading-[1.12] font-normal tracking-[-0.02em] text-balance text-navy-900 sm:text-[2.5rem] md:text-[3rem]">
              {about.heading}
            </h2>

            <span
              aria-hidden="true"
              className="mt-10 block h-px w-16 bg-gold-600/50"
            />

            <p className="mt-10 text-[1.0625rem] leading-[1.75] text-pretty text-ink-soft">
              {about.body}
            </p>
          </div>

          <ul
            className="mt-12 grid gap-px overflow-hidden rounded-xl bg-rule sm:grid-cols-2 md:mt-16 lg:grid-cols-5"
            aria-label="What we help members achieve"
          >
            {about.highlights.map((highlight) => (
              <li
                key={highlight}
                className="label-sm flex items-center justify-center gap-2.5 bg-paper-alt px-5 py-7 text-center text-navy-900 md:px-6 md:py-8"
              >
                <span
                  aria-hidden="true"
                  className="h-1.5 w-1.5 shrink-0 rounded-full bg-gold-500"
                />
                {highlight}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
