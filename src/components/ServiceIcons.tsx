import type { Service } from "@/lib/content";

/**
 * Line icons for the five member service lines. Drawn on a 24-unit grid with a
 * single stroke weight so the grid reads as one set, and inheriting
 * `currentColor` so each card controls its own tone.
 */
const paths: Record<Service["icon"], React.ReactNode> = {
  // A house on a plot line — land and property.
  realEstate: (
    <>
      <path d="M3.5 11.2 12 4.5l8.5 6.7" />
      <path d="M5.8 9.4v9.1h12.4V9.4" />
      <path d="M10 18.5v-4.8h4v4.8" />
      <path d="M2.5 21.5h19" />
    </>
  ),
  // Wheat ear over a furrow — the crest's own motif.
  agriculture: (
    <>
      <path d="M12 3.2v11.6" />
      <path d="M12 6.4c-1.9 0-3-1-3-2.6 1.9 0 3 1 3 2.6ZM12 6.4c1.9 0 3-1 3-2.6-1.9 0-3 1-3 2.6Z" />
      <path d="M12 10.3c-1.9 0-3-1-3-2.6 1.9 0 3 1 3 2.6ZM12 10.3c1.9 0 3-1 3-2.6-1.9 0-3 1-3 2.6Z" />
      <path d="M12 14.2c-1.9 0-3-1-3-2.6 1.9 0 3 1 3 2.6ZM12 14.2c1.9 0 3-1 3-2.6-1.9 0-3 1-3 2.6Z" />
      <path d="M3.5 19.5c3-1.6 5.8-2.4 8.5-2.4s5.5.8 8.5 2.4" />
    </>
  ),
  // Coin passing between two hands — lending.
  loans: (
    <>
      <circle cx="12" cy="8" r="3.4" />
      <path d="M12 6.6v2.8M10.9 7.3h2.2" />
      <path d="M2.8 15.4c1.5-.9 2.9-.6 4.2.4l2.3 1.8h3.1" />
      <path d="M21.2 15.4c-1.5-.9-2.9-.6-4.2.4l-2 1.6" />
      <path d="M2.8 15.4v4.4M21.2 15.4v4.4" />
    </>
  ),
  // Stacked bars rising out of a vault line — savings and growth.
  wealth: (
    <>
      <path d="M3 20.5h18" />
      <path d="M6 20.5v-5.2M11 20.5V9.8M16 20.5v-7.4M21 20.5V5.5" />
      <path d="M3.6 12.4 8.4 8l3.4 2.6L20 3.6" />
      <path d="M16.4 3.6H20v3.5" />
    </>
  ),
  // Aeroplane on a flight arc — ticketing and travel.
  travel: (
    <>
      <path d="M10.4 13.6 3.2 11.4a.7.7 0 0 1-.2-1.2l1.3-1a.8.8 0 0 1 .7-.1l3.1.9 3-2.6" />
      <path d="m20.2 4.2-9.4 8.2-1.2 4.3a.7.7 0 0 1-1.2.3l-1.5-1.8" />
      <path d="m20.2 4.2-6.6 11.2a.7.7 0 0 1-1.2.1l-2-2.8" />
      <path d="M4 20.5h16" />
    </>
  ),
};

export function ServiceIcon({
  name,
  className = "",
}: {
  name: Service["icon"];
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {paths[name]}
    </svg>
  );
}
