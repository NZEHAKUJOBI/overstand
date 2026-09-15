import { Crest } from "./Crest";
import {
  bankers,
  email,
  offices,
  phones,
  society,
  sourceNote,
} from "@/lib/content";

export function SiteFooter() {
  return (
    <footer className="relative bg-forest-950 text-paper">
      <div aria-hidden="true" className="h-px w-full bg-gold-500/40" />
      <div aria-hidden="true" className="mt-[3px] h-[3px] w-full bg-gold-500" />

      <div className="shell py-20 md:py-24">
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
          <div className="lg:col-span-4">
            <div className="flex items-center gap-4">
              <Crest size={44} className="h-11 w-11 shrink-0" />
              <div>
                <p className="font-display text-[1.0625rem] leading-tight">
                  {society.name}
                </p>
                <p className="label-sm mt-1.5 text-gold-400/75">
                  {society.kind}
                </p>
              </div>
            </div>
            <p className="font-display mt-7 max-w-xs text-[1.0625rem] leading-relaxed text-paper/60 italic">
              “{society.tagline}”
            </p>
          </div>

          {offices.map((office) => (
            <div key={office.label} className="lg:col-span-3">
              <h2 className="label-sm text-gold-400">{office.label}</h2>
              <address className="mt-4 text-[0.9375rem] leading-relaxed text-paper/70 not-italic">
                {office.lines.map((line) => (
                  <span key={line} className="block">
                    {line}
                  </span>
                ))}
              </address>
            </div>
          ))}

          <div className="lg:col-span-2">
            <h2 className="label-sm text-gold-400">Contact</h2>
            <div className="mt-4 space-y-1.5">
              {phones.map((phone) => (
                <a
                  key={phone}
                  href={`tel:${phone.replace(/\s/g, "")}`}
                  className="block text-[0.9375rem] text-paper/70 tnum transition-colors duration-200 hover:text-gold-300"
                >
                  {phone}
                </a>
              ))}
              <a
                href={`mailto:${email.address}`}
                className="block pt-1.5 text-[0.9375rem] break-all text-paper/70 transition-colors duration-200 hover:text-gold-300"
              >
                {email.address}
              </a>
            </div>
          </div>
        </div>

        <div className="mt-16 border-t border-paper/12 pt-8">
          <h2 className="label-sm text-paper/55">Bankers</h2>
          <ul className="mt-4 flex flex-col gap-x-8 gap-y-2 sm:flex-row sm:flex-wrap">
            {bankers.map((bank) => (
              <li key={bank.short} className="text-[0.9375rem] text-paper/70">
                {bank.name}{" "}
                <span className="text-paper/55">({bank.short})</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-12 border-t border-paper/12 pt-8">
          <p className="label-sm text-paper/50">
            {society.location} · Est. {society.established} · {society.tier} ·{" "}
            {society.bylaws}
          </p>
          <p className="mt-5 max-w-4xl text-[0.8125rem] leading-relaxed text-paper/55">
            {sourceNote}
          </p>
          <p className="label-sm mt-8 text-paper/55">
            © {society.established} {society.name}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
