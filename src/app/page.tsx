import { AtAGlance } from "@/components/AtAGlance";
import { Governance } from "@/components/Governance";
import { Hero } from "@/components/Hero";
import { HowToJoin } from "@/components/HowToJoin";
import { Membership } from "@/components/Membership";
import { Responsibility } from "@/components/Responsibility";
import { Services } from "@/components/Services";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { TargetMarket } from "@/components/TargetMarket";
import { VisionMission } from "@/components/VisionMission";
import { email, phones, society } from "@/lib/content";

const organisationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: society.name,
  alternateName: `${society.name} ${society.kind}`,
  slogan: society.tagline,
  foundingDate: society.established,
  address: {
    "@type": "PostalAddress",
    streetAddress: "124 Sherifat Adenusi Crescent, ACO Estate, Life Camp",
    addressLocality: "Abuja",
    addressRegion: "Federal Capital Territory",
    addressCountry: "NG",
  },
  telephone: phones[0].replace(/\s/g, ""),
  email: email.address,
  identifier: society.bylaws,
};

export default function Home() {
  return (
    <>
      <a
        href="#at-a-glance"
        className="label sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-60 focus:bg-gold-400 focus:px-5 focus:py-3 focus:text-forest-950"
      >
        Skip to content
      </a>

      <SiteHeader />

      <main className="flex-1">
        <Hero />
        <AtAGlance />
        <VisionMission />
        <Governance />
        <Membership />
        <Services />
        <TargetMarket />
        <Responsibility />
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
