import type { Metadata } from "next";
import Link from "next/link";
import { Crest } from "@/components/Crest";
import { ApplicationForm } from "./ApplicationForm";
import { joinSteps, offices, phones, society } from "@/lib/content";

export const metadata: Metadata = {
  title: "Apply for Membership",
  description:
    "Apply for membership of Overstand Multi-Purpose Cooperative Society Limited, a registered multipurpose cooperative in Wuye, Abuja. Monthly contributions from ₦25,000.",
};

export default function JoinPage() {
  const [headOffice] = offices;

  return (
    <>
      <header className="relative overflow-hidden bg-navy-950 text-paper">
        <div aria-hidden="true" className="absolute inset-x-0 top-0 h-[3px] bg-gold-500" />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "radial-gradient(120% 85% at 15% -10%, rgba(36,90,147,0.45), transparent 60%)",
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
            Apply for membership
          </h1>
          <p className="mt-6 max-w-2xl text-[1.0625rem] leading-[1.7] text-pretty text-paper/75">
            Membership is open to individuals building structured wealth through
            collective investment. Complete your details below and the
            Secretariat will follow up with the Membership/Entrance Form.
          </p>
        </div>
      </header>

      <main className="shell py-16 md:py-24">
        <div className="grid gap-14 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-7">
            <ApplicationForm />
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
                      <span className="font-display block text-[1.0625rem] leading-snug text-navy-900">
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
                <h3 className="label-sm text-ink-faint">
                  Prefer to do this in person?
                </h3>

                {phones.length > 0 ? (
                  <div className="mt-4 space-y-1.5">
                    {phones.map((phone) => (
                      <a
                        key={phone}
                        href={`tel:${phone.replace(/\s/g, "")}`}
                        className="tnum block text-[0.9375rem] text-navy-900 underline-offset-4 hover:underline"
                      >
                        {phone}
                      </a>
                    ))}
                  </div>
                ) : null}

                <p className="mt-5 text-[0.875rem] leading-relaxed text-ink-soft">
                  Membership/Entrance Forms are issued from the Society&apos;s
                  office at {headOffice.lines.join(", ")}.
                </p>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <footer className="bg-navy-950 py-10 text-paper">
        <div className="shell flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="label-sm text-paper/55">
            {society.legalName} · {society.registration}
          </p>
          <Link href="/" className="label-sm text-gold-400 underline-offset-4 hover:underline">
            Return to the Society
          </Link>
        </div>
      </footer>
    </>
  );
}
