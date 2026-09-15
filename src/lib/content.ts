/**
 * Single source of truth for the site copy.
 *
 * Every figure, name and address here is transcribed from the Society's
 * infographic, which in turn cites the Minutes of Meeting of 20 August 2026 and
 * the Strategic Meeting Report & Implementation Brief of 15 August 2026.
 * Items the Society has not yet ratified or filled are marked `provisional`
 * so the page can say so plainly rather than quietly implying otherwise.
 */

export const society = {
  name: "Anchor Real Estate Group",
  kind: "Multipurpose Cooperative Society Limited",
  tagline: "Building Shared Prosperity Through Real Estate",
  location: "Abuja, Federal Capital Territory, Nigeria",
  established: "2026",
  tier: "Tier 1 Cooperative",
  bylaws: "FCTA By-Laws No. R11913",
} as const;

export const navigation = [
  { id: "at-a-glance", label: "At a Glance" },
  { id: "vision", label: "Vision" },
  { id: "governance", label: "Governance" },
  { id: "membership", label: "Membership" },
  { id: "services", label: "Services" },
  { id: "outlook", label: "Outlook" },
  { id: "join", label: "How to Join" },
] as const;

/* ── 01 · At a Glance ─────────────────────────────────────────────── */

export const headlineFigure = {
  value: "₦5.0bn",
  label: "Capital mobilization target",
  note: "The Society's total mobilization objective across the full slot pool.",
};

export const glanceFigures = [
  { value: "1,000,000", label: "Ownership slots on offer" },
  { value: "₦5,000", label: "Price per ownership slot" },
  { value: "200", label: "Initial membership target" },
  { value: "₦500K–₦50M", label: "Min–max member holding" },
  { value: "₦20,000", label: "Registration fee" },
  { value: "₦10,000", label: "Monthly dues — investor" },
];

/* ── 02 · Vision, Mission & Values ────────────────────────────────── */

export const vision = {
  heading: "Vision",
  body: "To be a leading member-owned real estate and multipurpose cooperative in Nigeria, recognized for creating inclusive pathways to property ownership, wealth-building and shared prosperity.",
};

export const mission = {
  heading: "Mission",
  body: "To mobilize member capital responsibly and transparently, delivering affordable, well-governed real estate, tourism, financial-inclusion and social-impact programmes across the FCT and beyond.",
};

export const values = [
  {
    title: "Transparency & Accountability",
    body: "Open reporting on funds, slots and project performance.",
  },
  {
    title: "Member-Centricity",
    body: "Governance designed around member interests first.",
  },
  {
    title: "Integrity",
    body: "Disciplined stewardship of member contributions.",
  },
  {
    title: "Inclusion & Shared Prosperity",
    body: "Pathways to ownership for every income level.",
  },
  {
    title: "Innovation",
    body: "A digital platform and differentiated products.",
  },
  {
    title: "Prudent Stewardship",
    body: "Safeguards against concentration and undue risk.",
  },
];

/* ── 03 · Governance ──────────────────────────────────────────────── */

export type Office = {
  office: string;
  holder: string;
  vacant?: boolean;
};

export const executive: Office[] = [
  { office: "President", holder: "TPL Lami" },
];

export const executiveSecond: Office[] = [
  { office: "Vice President", holder: "Dr. Adeoye Adegboye" },
  { office: "Secretary General", holder: "Dr Dayo Popoola" },
  { office: "Treasurer", holder: "Omotayo Abiola" },
];

export const executiveThird: Office[] = [
  { office: "Financial Secretary", holder: "Pending appointment", vacant: true },
  { office: "Assistant Secretary", holder: "Pending appointment", vacant: true },
  { office: "Publicity Secretary", holder: "Victoria Jim" },
];

export const boardOfTrustees = {
  title: "Board of Trustees",
  body: "Highly professional, reputable individuals — captains of industry spanning real estate, health, technology, finance and engineering.",
  tenure: "Two-year tenure, subject to the final Bye-Laws.",
};

export const governanceNote =
  "Reporting structure as at 20 August 2026. Dashed offices remain to be filled.";

/* ── 04 · Membership & Ownership ──────────────────────────────────── */

export const holdingBand = {
  floor: {
    slots: "100 slots",
    amount: "₦500,000",
    caption: "Minimum holding",
  },
  ceiling: {
    slots: "10,000 slots",
    amount: "₦50,000,000",
    caption: "Maximum holding",
  },
  scaleNote: "Holding grows with member commitment",
  capNote: "Ceiling equals 1% of the 1,000,000-slot pool.",
};

export const fees = [
  {
    amount: "₦20,000",
    label: "Registration fee",
    detail: "One-time, payable on application.",
  },
  {
    amount: "₦10,000",
    label: "Monthly dues",
    detail: "Investing member — holds ownership slots.",
  },
  {
    amount: "₦50,000",
    label: "Monthly dues",
    detail: "Non-investor member — no ownership slots.",
  },
];

export const nonInvestorTier = {
  title: "Non-investor tier",
  body: "Full Society membership and access to services, without holding ownership slots.",
};

/* ── 05 · Products & Services ─────────────────────────────────────── */

export type Service = {
  title: string;
  body: string;
  icon:
    | "housing"
    | "tourism"
    | "institutional"
    | "warehousing"
    | "financing"
    | "project"
    | "platform"
    | "space";
};

export const services: Service[] = [
  {
    title: "Housing & Property",
    body: "Residential schemes and property holdings developed for and with members.",
    icon: "housing",
  },
  {
    title: "Holiday & Tourism",
    body: "Leisure and hospitality assets held within the Society's portfolio.",
    icon: "tourism",
  },
  {
    title: "Institutional Real Estate",
    body: "Larger-scale holdings serving organisations rather than households.",
    icon: "institutional",
  },
  {
    title: "Warehousing",
    body: "Logistics and industrial storage capacity across the Territory.",
    icon: "warehousing",
  },
  {
    title: "Household & Auto Financing",
    body: "Cooperative credit for household assets and vehicle acquisition.",
    icon: "financing",
  },
  {
    title: "Project Financing",
    body: "Pooled member capital deployed into vetted development projects.",
    icon: "project",
  },
  {
    title: "Digital Cooperative Platform",
    body: "Member records, slot holdings and contributions administered online.",
    icon: "platform",
  },
  {
    title: "Recreational, Storage & Office Space",
    body: "Commercial and community space held and let by the Society.",
    icon: "space",
  },
];

/* ── 06 · Target Market & Expansion ───────────────────────────────── */

export const marketLanes = [
  {
    tier: "Primary",
    segment: "Young professionals",
    steps: ["Abuja metropolis housing schemes"],
  },
  {
    tier: "Secondary",
    segment: "Broader population",
    steps: ["Rent-to-Own + credit scoring", "FCT Area Councils — Phases 1–4"],
  },
];

export const expansionNote =
  "Expansion is paced by demand, resource availability and project viability.";

/* ── 07 · Corporate Social Responsibility ─────────────────────────── */

export const responsibility = {
  lead: "A social-impact component is built into the Society's operating model.",
  body: "The initial focus is vocational training for housewives, women and teenagers — supporting skills development, household resilience and community inclusion alongside the Society's broader development mandate.",
};

/* ── 08 · How to Join ─────────────────────────────────────────────── */

export const joinSteps = [
  {
    title: "Pay the registration fee",
    body: "A one-time payment of ₦20,000 opens your membership file.",
  },
  {
    title: "Commit to monthly dues",
    body: "₦10,000 monthly as an investing member, or ₦50,000 as a non-investor member.",
  },
  {
    title: "Choose your holding",
    body: "Take between 100 and 10,000 ownership slots, or join on the non-investor tier.",
  },
  {
    title: "Complete documentation",
    body: "Membership forms are signed once the Society finalises them.",
  },
];

export const joinCaveat =
  "Detailed eligibility criteria and standard application forms are still being developed. Registrations of interest are being recorded in the meantime.";

/* ── Contact ──────────────────────────────────────────────────────── */

export const offices = [
  {
    label: "Registered address",
    lines: [
      "124 Sherifat Adenusi Crescent",
      "ACO Estate, Life Camp",
      "Abuja–FCT",
    ],
  },
  {
    label: "Alternative office",
    lines: [
      "1004 Ameh Ebute Street, Suite D-14",
      "Boya Place Plaza, Wuye",
      "Abuja–FCT",
    ],
  },
];

export const phones = ["+234 902 525 0026", "+234 803 612 5057"];

export const email = { address: "babdayo111@gmail.com", provisional: true };

export const bankers = [
  { name: "First City Monument Bank", short: "FCMB" },
  { name: "Federal Mortgage Bank of Nigeria", short: "FMBN" },
  { name: "Guaranty Trust Bank", short: "GTBank" },
];

export const sourceNote =
  "Sources: Anchor Real Estate Group — Minutes of Meeting, 20 August 2026; Strategic Meeting Report & Implementation Brief, 15 August 2026. Vision, Mission and Core Values are proposed, pending formal Board adoption.";
