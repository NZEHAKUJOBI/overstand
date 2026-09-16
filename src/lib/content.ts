/**
 * Single source of truth for the site copy.
 *
 * Every figure, name and address here is transcribed from the Society's
 * Official Update. Nothing on the public page is asserted beyond what that
 * document supports: where the Update names something without stating it —
 * the registration and annual fee amounts, the Society's phone and email —
 * the entry is marked `provisional` and the page says so plainly rather than
 * quietly implying otherwise.
 *
 * Deliberately absent, because the Official Update does not cover them:
 * a vision statement, core values, the roster of offices, a target-market
 * breakdown and a social-responsibility programme. Add sections back when
 * the Society supplies the source material, not before.
 */

export const society = {
  name: "Overstand",
  kind: "Multipurpose Cooperative Society",
  legalName: "Overstand Multi-Purpose Cooperative Society Limited",
  abbreviation: "OMCS",
  tagline: "Building Structured Wealth Through Collective Investment",
  location: "Wuye, Abuja, Federal Capital Territory, Nigeria",
  registration: "Reg. No. 3591",
  status: "Fully registered and duly certified",
} as const;

/**
 * Nav labels are short on purpose. They are set in wide-tracked small caps, so
 * a three-word label costs roughly three times the bar width of a one-word
 * one, and six of those will not fit beside the wordmark and the call to
 * action. They point at the section headings rather than repeating them.
 */
export const navigation = [
  { id: "at-a-glance", label: "Overview" },
  { id: "mission", label: "Mission" },
  { id: "services", label: "Services" },
  { id: "membership", label: "Membership" },
  { id: "contributions", label: "Contributions" },
  { id: "join", label: "Join" },
] as const;

/* ── Hero ─────────────────────────────────────────────────────────── */

export const hero = {
  eyebrow: "Membership registration is now open",
  heading: "Building structured wealth through collective investment",
  body: "Overstand Multi-Purpose Cooperative Society Limited is fully registered and duly certified. Membership is open to individuals interested in building structured wealth and achieving economic growth together.",
  primaryCta: "Apply for membership",
  secondaryCta: "What we offer",
};

/* ── 01 · At a Glance ─────────────────────────────────────────────── */

export const headlineFigure = {
  value: "₦25,000",
  label: "Monthly contribution from",
  note: "Tier 1 entry. Tier 2 is ₦50,000, and members contributing above that agree a tailored structure with the Society.",
};

export const glanceFigures = [
  { value: "₦20,000", label: "One-time application fee" },
  { value: "₦25,000", label: "Tier 1 monthly contribution" },
  { value: "₦50,000", label: "Tier 2 monthly contribution" },
  { value: "5", label: "Member service lines" },
  { value: "18+", label: "Minimum age to join" },
  { value: "3591", label: "Cooperative registration number" },
];

/* ── 02 · Mission ─────────────────────────────────────────────────── */

export const mission = {
  heading: "Mission",
  body: "To create financial freedom through innovative solutions, strategic investments, and sustainable wealth-building.",
  support:
    "The Society is committed to being credible, transparent and professionally managed. By pooling the resources and talents of its members, it creates pathways to financial independence and builds lasting value together.",
};

/* ── 03 · Products & Services ─────────────────────────────────────── */

export type Service = {
  title: string;
  body: string;
  icon: "realEstate" | "agriculture" | "loans" | "wealth" | "travel";
};

export const servicesIntro =
  "Membership provides access to a comprehensive suite of professional services.";

export const services: Service[] = [
  {
    title: "Real Estate Investments",
    body: "Affordable land and property with flexible payment plans.",
    icon: "realEstate",
  },
  {
    title: "Agricultural Projects",
    body: "Professionally managed, profitable and sustainable ventures.",
    icon: "agriculture",
  },
  {
    title: "Loan Products",
    body: "Car loans, salary advances and micro-lending to meet immediate financial needs.",
    icon: "loans",
  },
  {
    title: "Wealth Management",
    body: "Tailored savings accounts and strategic investment opportunities for collective and individual growth.",
    icon: "wealth",
  },
  {
    title: "Travel & Tour Services",
    body: "Seamless ticket booking and travel convenience.",
    icon: "travel",
  },
];

/* ── 04 · Membership ──────────────────────────────────────────────── */

export const eligibility = {
  heading: "Who can join",
  criteria: [
    "At least 18 years of age",
    "Of good character",
    "Of sound mind",
  ],
};

export const fees = [
  {
    amount: "₦20,000",
    label: "Application fee",
    detail:
      "Non-refundable, due on submission. Covers the form, your ID card and administrative processing.",
  },
  {
    amount: "Confirm at the office",
    label: "One-time registration fee",
    detail:
      "Set by the Society's internal structure. The Secretariat will confirm the amount.",
    provisional: true,
  },
  {
    amount: "Confirm at the office",
    label: "Annual membership fee",
    detail:
      "Keeps your access to member benefits and opportunities current year to year.",
    provisional: true,
  },
];

/* ── 05 · Contribution Structure ──────────────────────────────────── */

export const contributions = {
  heading: "Monthly contribution structure",
  lead: "Contributions build a sustainable financial base for the Society's shared goals, including land acquisition and estate development.",
  tiers: [
    {
      name: "Tier 1",
      amount: "₦25,000",
      cadence: "per month",
      detail: "Entry tier.",
    },
    {
      name: "Tier 2",
      amount: "₦50,000",
      cadence: "per month",
      detail: "Higher monthly commitment.",
    },
  ],
  flexibility: {
    title: "Flexibility notice",
    body: "The tiers are designed to be inclusive, not restrictive. Members with the financial capacity to contribute above ₦50,000 are encouraged to reach out and agree a tailored contribution structure. This flexibility strengthens the Society's collective investment base and accelerates its shared goals.",
  },
};

/* ── 06 · How to Join ─────────────────────────────────────────────── */

export const joinSteps = [
  {
    title: "Confirm you are eligible",
    body: "Membership is open to individuals at least 18 years of age, of good character and of sound mind.",
  },
  {
    title: "Obtain the Membership/Entrance Form",
    body: "Collect the form from the Society's office, or start online and the Secretariat will follow up with it.",
  },
  {
    title: "Complete your details",
    body: "The Membership Application Form asks for your personal information and your next of kin.",
  },
  {
    title: "Pay the ₦20,000 application fee",
    body: "Non-refundable, due on submission. It covers the form, your ID card and administrative processing.",
  },
  {
    title: "Choose your contribution tier",
    body: "₦25,000 or ₦50,000 monthly — or speak to the Secretariat about a tailored structure above ₦50,000.",
  },
];

export const joinCaveat =
  "Submitting this form starts your application. It does not admit you to membership and takes no payment — the Secretariat will contact you with the Membership/Entrance Form and payment instructions.";

/* ── Contact ──────────────────────────────────────────────────────── */

export const offices = [
  {
    label: "Head office",
    lines: [
      "1004 Ameh Ebute Street",
      "Suite D-18, Boya Place Plaza",
      "Wuye, Abuja–FCT",
    ],
  },
];

/** No phone number appears in the Official Update — confirm before launch. */
export const phones: string[] = [];

/** No Society address appears in the Official Update — confirm before launch. */
export const email = { address: "", provisional: true };

export const contactNote =
  "For enquiries or to proceed with registration, reach out to any of the Society's official representatives for the membership application form, or visit the head office.";

export const sourceNote =
  "Source: Overstand Multipurpose Cooperative Society — Official Update. Fee amounts shown as “confirm at the office” are named in that document without a stated figure.";
