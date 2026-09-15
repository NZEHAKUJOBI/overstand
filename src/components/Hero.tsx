import Link from "next/link";
import { Crest } from "./Crest";
import { society } from "@/lib/content";

const stamps = [
  { label: "Established", value: society.established },
  { label: "Classification", value: society.tier },
  { label: "By-Laws", value: "No. R11913" },
];

export function Hero() {
  return (
    <section
      id="top"
      className="relative overflow-hidden bg-forest-950 text-paper"
    >
      {/* Ledger rules — structural texture rather than decoration. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, rgba(217,190,114,0.05) 0px, rgba(217,190,114,0.05) 1px, transparent 1px, transparent 104px)",
        }}
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(120% 85% at 12% -10%, rgba(43,115,88,0.42), transparent 58%)",
        }}
      />

      {/* Document edge, echoing the Society's printed material. */}
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px] bg-gold-500" />
      <div aria-hidden="true" className="absolute inset-x-0 top-[5px] h-px bg-gold-500/40" />

      <div className="shell relative flex min-h-[100svh] flex-col justify-center pt-28 pb-16 md:pt-32 md:pb-20">
        <div className="grid items-center gap-14 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-7">
            <p className="label text-gold-400">
              {society.kind}
            </p>

            <h1 className="font-display mt-6 text-[2.75rem] leading-[1.03] font-normal tracking-[-0.025em] text-balance sm:text-[3.75rem] lg:text-[4.5rem]">
              {society.name}
            </h1>

            <p className="font-display mt-6 text-[1.375rem] leading-[1.4] text-gold-300 italic sm:text-[1.625rem]">
              “{society.tagline}”
            </p>

            <div aria-hidden="true" className="mt-9 h-px w-24 bg-gold-500/50" />

            <p className="mt-9 max-w-xl text-[1.0625rem] leading-[1.7] text-pretty text-paper/75">
              A member-owned cooperative society limited in Abuja, mobilising ₦5 billion
              of member capital into housing, tourism, warehousing and financial
              inclusion across the Federal Capital Territory — and giving every
              member a documented stake in what that capital builds.
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
              <Link
                href="/join"
                className="label bg-gold-400 px-7 py-4 text-center text-forest-950 transition-colors duration-200 hover:bg-gold-300"
              >
                Become a Member
              </Link>
              <a
                href="#membership"
                className="label border border-paper/25 px-7 py-4 text-center text-paper transition-colors duration-200 hover:border-paper/60 hover:bg-paper/5"
              >
                Membership Terms
              </a>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="flex flex-col items-center gap-10 lg:items-end">
              <div className="relative flex items-center justify-center">
                <div
                  aria-hidden="true"
                  className="absolute h-[17rem] w-[17rem] rounded-full border border-gold-400/15 sm:h-[21rem] sm:w-[21rem]"
                />
                <Crest size={208} priority className="h-40 w-40 sm:h-52 sm:w-52" />
              </div>

              <dl className="grid w-full max-w-sm grid-cols-3 border-t border-gold-400/20">
                {stamps.map((stamp) => (
                  <div
                    key={stamp.label}
                    className="border-r border-gold-400/20 px-3 py-5 last:border-r-0"
                  >
                    <dt className="label-sm text-paper/55">{stamp.label}</dt>
                    <dd className="mt-2 text-[0.8125rem] leading-snug text-gold-300">
                      {stamp.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>

        <p className="label-sm mt-16 text-paper/55 md:mt-20">
          {society.location}
        </p>
      </div>
    </section>
  );
}
