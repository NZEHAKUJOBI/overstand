import { Reveal } from "./Reveal";
import { responsibility } from "@/lib/content";

export function Responsibility() {
  return (
    <section className="shell py-24 md:py-32">
      <Reveal>
        <div className="grid gap-10 border-t border-rule pt-12 lg:grid-cols-12 lg:gap-14">
          <div className="lg:col-span-4">
            <div className="flex items-center gap-4">
              <span className="label-sm text-gold-700">07</span>
              <span aria-hidden="true" className="h-px w-12 bg-gold-600/35" />
            </div>
            <h2 className="font-display mt-5 text-[1.75rem] leading-[1.2] tracking-[-0.015em] text-forest-900 sm:text-[2rem]">
              Corporate Social Responsibility
            </h2>
          </div>

          <div className="lg:col-span-8">
            <p className="font-display text-[1.5rem] leading-[1.45] text-pretty text-forest-800 sm:text-[1.75rem]">
              {responsibility.lead}
            </p>
            <p className="mt-6 max-w-2xl text-[1.0625rem] leading-[1.7] text-pretty text-ink-soft">
              {responsibility.body}
            </p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
