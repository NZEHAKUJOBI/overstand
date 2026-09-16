import type { Metadata, Viewport } from "next";
import { Fraunces, IBM_Plex_Mono, Inter } from "next/font/google";
import "./globals.css";

/*
  Fraunces carries the display voice — a warm, high-contrast serif that reads
  as considered rather than corporate — Inter the running text, and Plex Mono
  the labels and legal notes.
*/
const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  axes: ["SOFT", "WONK", "opsz"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});

const description =
  "A registered multipurpose cooperative society in Wuye, Abuja (Reg. No. 3591). Membership is open — real estate, agriculture, loans, wealth management and travel services, on monthly contributions from ₦25,000.";

export const metadata: Metadata = {
  // TODO: set to the Society's real domain before launch.
  metadataBase: new URL("https://overstandcooperative.ng"),
  title: {
    default: "Overstand Multipurpose Cooperative Society",
    template: "%s · Overstand Cooperative",
  },
  description,
  applicationName: "Overstand Multipurpose Cooperative Society",
  keywords: [
    "cooperative society Abuja",
    "multipurpose cooperative Nigeria",
    "Overstand Cooperative",
    "cooperative loans Abuja",
    "agricultural cooperative FCT",
    "land and property cooperative Abuja",
  ],
  authors: [{ name: "Overstand Multipurpose Cooperative Society" }],
  openGraph: {
    type: "website",
    locale: "en_NG",
    siteName: "Overstand Multipurpose Cooperative Society",
    title: "Overstand Multipurpose Cooperative Society",
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: "Overstand Multipurpose Cooperative Society",
    description,
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#05142a",
  colorScheme: "light",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en-NG"
      className={`${fraunces.variable} ${inter.variable} ${plexMono.variable} h-full antialiased`}
    >
      {/*
        No noscript override for the scroll reveals: they are visible by
        default and only script can hide them, so there is nothing to undo.
        The old override only covered script being disabled, not script being
        broken — which is the failure that actually blanks a page.
      */}
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}
