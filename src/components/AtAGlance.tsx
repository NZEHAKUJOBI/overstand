import { Reveal } from "./Reveal";
import { glanceFigures, headlineFigure } from "@/lib/content";

/**
 * The figures band. The headline figure sits on a navy card at the left with
 * the supporting six in a tiled grid beside it, so the entry contribution
 * reads first and the rest qualify it.
 */
export function AtAGlance() {
  return (
    <section id="at-a-glance" className="bg-paper-alt py-20 md:py-28">
      <div className="shell">
        <Reveal>
          <div className="grid gap-6 lg:grid-cols-12 lg:gap-8">
            <div className="rounded-xl bg-navy-900 p-8 text-paper md:p-10 lg:col-span-5">
              <p className="label text-gold-400">{headlineFigure.label}</p>
              <p className="figure-num mt-4 text-[3.25rem] leading-none text-paper md:text-[4rem]">
                {headlineFigure.value}
              </p>
              <span
                aria-hidden="true"
                className="mt-7 block h-px w-14 bg-gold-500/50"
              />
              <p className="mt-7 text-[0.9375rem] leading-[1.65] text-pretty text-paper/70">
                {headlineFigure.note}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-px overflow-hidden rounded-xl bg-rule sm:grid-cols-3 lg:col-span-7">
              {glanceFigures.map((figure) => (
                <div
                  key={figure.label}
                  className="flex flex-col justify-between gap-3 bg-paper-alt px-5 py-7 md:px-6 md:py-8"
                >
                  <p className="figure-num text-[1.625rem] leading-none text-navy-900 md:text-[1.875rem]">
                    {figure.value}
                  </p>
                  <p className="label-sm text-ink-faint">{figure.label}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
