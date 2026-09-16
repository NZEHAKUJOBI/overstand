import Link from "next/link";
import { Crest } from "./Crest";
import { email, navigation, offices, phones, society, sourceNote } from "@/lib/content";

/**
 * Footer. Phone and email render only when the Society has supplied them —
 * an empty contact block is better than a placeholder that looks like a real
 * channel and silently goes nowhere.
 */
export function SiteFooter() {
  const year = new Date().getFullYear();
  const hasEmail = email.address.length > 0;

  return (
    <footer className="border-t border-gold-500/25 bg-navy-950 text-paper">
      <div className="shell py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-12 md:gap-8">
          <div className="md:col-span-5">
            <div className="flex items-center gap-3">
              <Crest size={44} className="h-11 w-11 shrink-0" />
              <span>
                <span className="font-display block text-[1.0625rem] leading-tight">
                  {society.name}
                </span>
                <span className="label-sm block text-gold-400/75">
                  {society.kind}
                </span>
              </span>
            </div>

            <p className="mt-6 max-w-sm text-[0.9375rem] leading-[1.7] text-pretty text-paper/60">
              {society.legalName} — {society.registration}. {society.status}.
            </p>
          </div>

          <nav aria-label="Footer" className="md:col-span-3">
            <p className="label-sm text-gold-400/75">This page</p>
            <ul className="mt-5 grid gap-2.5">
              {navigation.map((item) => (
                <li key={item.id}>
                  <a
                    href={`#${item.id}`}
                    className="text-[0.9375rem] text-paper/65 transition-colors duration-200 hover:text-paper"
                  >
                    {item.label}
                  </a>
                </li>
              ))}
              <li>
                <Link
                  href="/join"
                  className="text-[0.9375rem] text-gold-300 transition-colors duration-200 hover:text-gold-400"
                >
                  Apply for membership
                </Link>
              </li>
            </ul>
          </nav>

          <div className="md:col-span-4">
            {offices.map((office) => (
              <div key={office.label}>
                <p className="label-sm text-gold-400/75">{office.label}</p>
                <address className="mt-5 text-[0.9375rem] leading-[1.7] text-paper/65 not-italic">
                  {office.lines.map((line) => (
                    <span key={line} className="block">
                      {line}
                    </span>
                  ))}
                </address>
              </div>
            ))}

            {phones.length > 0 || hasEmail ? (
              <div className="mt-7 grid gap-2">
                {phones.map((phone) => (
                  <a
                    key={phone}
                    href={`tel:${phone.replace(/\s/g, "")}`}
                    className="text-[0.9375rem] text-paper/65 transition-colors duration-200 hover:text-paper"
                  >
                    {phone}
                  </a>
                ))}

                {hasEmail ? (
                  <a
                    href={`mailto:${email.address}`}
                    className="text-[0.9375rem] break-all text-paper/65 transition-colors duration-200 hover:text-paper"
                  >
                    {email.address}
                  </a>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>

        <div className="mt-14 border-t border-paper/12 pt-8">
          <p className="text-[0.8125rem] leading-[1.65] text-pretty text-paper/45">
            {sourceNote}
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
            <p className="label-sm text-paper/45">
              © {year} {society.legalName}
            </p>
            <Link
              href="/login"
              className="label-sm text-paper/45 transition-colors duration-200 hover:text-gold-400"
            >
              Officer sign-in
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
