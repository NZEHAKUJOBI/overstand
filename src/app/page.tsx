import { AtAGlance } from "@/components/AtAGlance";
import { Contributions } from "@/components/Contributions";
import { Hero } from "@/components/Hero";
import { HowToJoin } from "@/components/HowToJoin";
import { Membership } from "@/components/Membership";
import { Mission } from "@/components/Mission";
import { Services } from "@/components/Services";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { email, offices, phones, society } from "@/lib/content";

const [headOffice] = offices;

const organisationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: society.legalName,
  alternateName: [`${society.name} ${society.kind}`, society.abbreviation],
  slogan: society.tagline,
  address: {
    "@type": "PostalAddress",
    streetAddress: headOffice.lines.slice(0, 2).join(", "),
    addressLocality: "Abuja",
    addressRegion: "Federal Capital Territory",
    addressCountry: "NG",
  },
  identifier: society.registration,
  // Contact details are omitted until the Society supplies them, rather than
  // publishing a placeholder into structured data that search engines cache.
  ...(phones.length > 0 ? { telephone: phones[0].replace(/\s/g, "") } : {}),
  ...(email.address ? { email: email.address } : {}),
};

export default function Home() {
  return (
    <>
      <a
        href="#at-a-glance"
        className="label sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-60 focus:bg-gold-400 focus:px-5 focus:py-3 focus:text-navy-950"
      >
        Skip to content
      </a>

      <SiteHeader />

      <main className="flex-1">
        <Hero />
        <AtAGlance />
        <Mission />
        <Services />
        <Membership />
        <Contributions />
        <HowToJoin />
      </main>

      <SiteFooter />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organisationSchema) }}
      />
    </>
  );
}
