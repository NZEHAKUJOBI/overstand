import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import "./globals.css";

/*
  Source Serif carries the display voice, Plex Sans the running text, and Plex
  Mono the labels and legal notes — the pairing of an annual report rather than
  a product page.
*/
const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  style: ["normal", "italic"],
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

const description =
  "A member-owned multipurpose cooperative society limited in Abuja, FCT. Ownership slots of ₦5,000, a ₦5 billion mobilization target, and member capital deployed across housing, tourism, warehousing and financial inclusion.";

export const metadata: Metadata = {
  metadataBase: new URL("https://anchorrealestategroup.ng"),
  title: {
    default: "Anchor Real Estate Group — Multipurpose Cooperative Society Limited",
    template: "%s · Anchor Real Estate Group",
  },
  description,
  applicationName: "Anchor Real Estate Group",
  keywords: [
    "cooperative society limited Abuja",
    "real estate cooperative Nigeria",
    "multipurpose cooperative FCT",
    "property ownership Abuja",
    "rent to own Abuja",
    "Anchor Real Estate Group",
  ],
  authors: [{ name: "Anchor Real Estate Group" }],
  openGraph: {
    type: "website",
    locale: "en_NG",
    siteName: "Anchor Real Estate Group",
    title: "Anchor Real Estate Group — Multipurpose Cooperative Society Limited",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Anchor Real Estate Group — Multipurpose Cooperative Society Limited",
    description,
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#071f17",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en-NG"
      className={`${sourceSerif.variable} ${plexSans.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        {/* Scroll reveals start transparent; without JS they must not stay so. */}
        <noscript>
          <style
            dangerouslySetInnerHTML={{
              __html: ".reveal{opacity:1!important;transform:none!important}",
            }}
          />
        </noscript>
        {children}
      </body>
    </html>
  );
}
