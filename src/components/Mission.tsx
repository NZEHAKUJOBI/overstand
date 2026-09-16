import { Reveal } from "./Reveal";
import { mission } from "@/lib/content";

/**
 * The mission, set large and alone.
 *
 * The Official Update states a mission and nothing else of this kind — no
 * vision, no core values — so this section carries the one statement rather
 * than padding a three-column grid with material the Society has not adopted.
 */
export function Mission() {
  return (
    <section id="mission" className="py-24 md:py-32">
      <div className="shell">
        <Reveal>
          <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
            <span className="label text-gold-700">{mission.heading}</span>

            <p className="font-display mt-7 text-[1.75rem] leading-[1.32] font-normal tracking-[-0.015em] text-balance text-navy-900 sm:text-[2.125rem] md:text-[2.5rem]">
              {mission.body}
            </p>

            <span aria-hidden="true" className="mt-10 h-px w-16 bg-gold-600/50" />

            <p className="mt-10 text-[1.0625rem] leading-[1.75] text-pretty text-ink-soft">
              {mission.support}
            </p>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
