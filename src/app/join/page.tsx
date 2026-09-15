import type { Metadata } from "next";
import Link from "next/link";
import { Crest } from "@/components/Crest";
import { EnquiryForm } from "./EnquiryForm";
import { joinSteps, society } from "@/lib/content";

export const metadata: Metadata = {
  title: "Register Your Interest",
  description:
    "Register your interest in membership of Anchor Real Estate Group, a multipurpose cooperative society limited in Abuja. Ownership slots of ₦5,000, from 100 to 10,000 per member.",
};

export default function JoinPage() {
  return (
    <>
      <header className="relative overflow-hidden bg-forest-950 text-paper">
        <div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px] bg-gold-500" />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(120% 85% at 15% -10%, rgba(43,115,88,0.4), transparent 60%)",
          }}
        />

        <div className="shell relative py-16 md:py-20">
          <Link
            href="/"
            className="inline-flex items-center gap-3 text-paper transition-opacity hover:opacity-85"
          >
            <Crest size={36} className="h-9 w-9" />
            <span>
              <span className="font-display block text-[0.9375rem] leading-tight">
                {society.name}
              </span>
              <span className="label-sm block text-gold-400/75">
                {society.kind}
              </span>
            </span>
          </Link>

          <h1 className="font-display mt-12 max-w-3xl text-[2.25rem] leading-[1.08] tracking-[-0.02em] text-balance sm:text-[3rem]">
            Register your interest in membership
          </h1>
          <p className="mt-6 max-w-2xl text-[1.0625rem] leading-[1.7] text-pretty text-paper/75">
            The Society is constituting a founding cohort of two hundred
            members. Tell us how to reach you and what kind of membership suits
            you, and the Secretariat will take it from there.
          </p>
        </div>
      </header>

      <main className="shell py-16 md:py-24">
        <div className="grid gap-14 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-7">
            <EnquiryForm />
          </div>

          <aside className="lg:col-span-5">
            <div className="lg:sticky lg:top-10">
              <h2 className="label text-gold-700">What happens next</h2>
              <ol className="mt-7 space-y-7">
                {joinSteps.map((step, index) => (
                  <li key={step.title} className="flex gap-5">
                    <span className="figure-num shrink-0 text-[1.25rem] leading-none text-gold-600">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span>
                      <span className="font-display block text-[1.0625rem] leading-snug text-forest-900">
                        {step.title}
                      </span>
                      <span className="mt-1.5 block text-[0.9375rem] leading-relaxed text-ink-soft">
                        {step.body}
                      </span>
                    </span>
                  </li>
                ))}
              </ol>

              <div className="mt-10 border-t border-rule pt-7">
                <h3 className="label-sm text-ink-faint">Prefer to speak to someone?</h3>
                <div className="mt-4 space-y-1.5">
                  <a
                    href="tel:+2349025250026"
                    className="block text-[0.9375rem] text-forest-900 tnum underline-offset-4 hover:underline"
                  >
                    +234 902 525 0026
                  </a>
                  <a
                    href="tel:+2348036125057"
                    className="block text-[0.9375rem] text-forest-900 tnum underline-offset-4 hover:underline"
                  >
                    +234 803 612 5057
                  </a>
                </div>
                <p className="mt-5 text-[0.875rem] leading-relaxed text-ink-soft">
                  124 Sherifat Adenusi Crescent, ACO Estate, Life Camp,
                  Abuja–FCT
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <footer className="bg-forest-950 py-10 text-paper">
        <div className="shell flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="label-sm text-paper/55">
            {society.tier} · {society.bylaws}
          </p>
          <Link href="/" className="label-sm text-gold-400 underline-offset-4 hover:underline">
            Return to the Society
          </Link>
        </div>
      </footer>
    </>
  );
}
