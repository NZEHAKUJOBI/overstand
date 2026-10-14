import { Reveal } from "./Reveal";
import { glanceFigures, headlineFigure } from "@/lib/content";

/**
 * The figures band. The headline figure sits on a navy card at the left with
 * the supporting six in a tiled grid beside it, so the entry contribution
 * reads first and the rest qualify it.
 */
export function AtAGlance() {
  return (
    <section id="at-a-glance" className="bg-paper-alt py-16 md:py-24">
      <div className="shell">
        <Reveal>
          <div className="grid gap-6 items-stretch lg:grid-cols-12 lg:gap-8">
            <div className="flex flex-col justify-between rounded-2xl bg-navy-900 p-8 text-paper shadow-sm sm:p-10 md:p-12 lg:col-span-5">
              <div>
                <p className="label text-gold-400">{headlineFigure.label}</p>
                <p className="figure-num mt-4 text-[3rem] leading-none text-paper sm:text-[3.5rem] md:text-[4rem]">
                  {headlineFigure.value}
                </p>
                <span
                  aria-hidden="true"
                  className="my-7 block h-px w-14 bg-gold-500/50"
                />
                <p className="text-[0.9375rem] leading-[1.65] text-pretty text-paper/75">
                  {headlineFigure.note}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 rounded-2xl border border-rule/70 bg-rule/70 p-px gap-px overflow-hidden shadow-sm sm:grid-cols-3 lg:col-span-7">
              {glanceFigures.map((figure) => (
                <div
                  key={figure.label}
                  className="flex flex-col justify-start gap-3 bg-paper-alt p-6 sm:p-7 md:p-8"
                >
                  <p className="figure-num text-[1.75rem] leading-none text-navy-900 sm:text-[2rem] md:text-[2.25rem]">
                    {figure.value}
                  </p>
                  <p className="label-sm text-ink-faint leading-normal">
                    {figure.label}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
