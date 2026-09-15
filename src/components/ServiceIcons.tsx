import type { Service } from "@/lib/content";

/**
 * Line marks for the eight service lines. Kept to one stroke weight and a
 * shared 32-unit box so the grid reads as a single drawn set.
 */
const paths: Record<Service["icon"], React.ReactNode> = {
  housing: (
    <>
      <path d="M5 15 L16 6 L27 15" />
      <path d="M8 13.5 V26 H24 V13.5" />
      <path d="M13.5 26 V19 H18.5 V26" />
    </>
  ),
  tourism: (
    <>
      <circle cx="16" cy="14" r="5.5" />
      <path d="M16 4 V6.5 M16 21.5 V24 M6 14 H8.5 M23.5 14 H26 M9 7 L10.7 8.7 M21.3 19.3 L23 21" />
      <path d="M4 27.5 H28" />
    </>
  ),
  institutional: (
    <>
      <path d="M4.5 12 L16 5.5 L27.5 12" />
      <path d="M4.5 27 H27.5" />
      <path d="M9 12 V23 M15 12 V23 M21 12 V23 M26 12 V23" />
      <path d="M6.5 23 H27.5" />
    </>
  ),
  warehousing: (
    <>
      <path d="M4 13.5 L16 7 L28 13.5 V27 H4 Z" />
      <path d="M11 27 V17.5 H21 V27" />
      <path d="M11 21 H21" />
    </>
  ),
  financing: (
    <>
      <path d="M5 20.5 H27 V24 H23.5" />
      <path d="M8.5 24 H5 V17 L8 11.5 H21 L25 17 H27" />
      <circle cx="10.5" cy="24" r="2.6" />
      <circle cx="21.5" cy="24" r="2.6" />
      <path d="M13.1 24 H18.9" />
    </>
  ),
  project: (
    <>
      <path d="M4.5 27.5 H27.5" />
      <path d="M7 27.5 V19 H12 V27.5" />
      <path d="M14 27.5 V14 H19 V27.5" />
      <path d="M21 27.5 V21.5 H26 V27.5" />
      <path d="M8 10 L15 5 L22 8.5" />
      <path d="M22 4.5 V8.5 H18" />
    </>
  ),
  platform: (
    <>
      <rect x="5" y="5.5" width="22" height="16" rx="1" />
      <path d="M5 17.5 H27" />
      <path d="M12 26.5 H20" />
      <path d="M16 21.5 V26.5" />
      <circle cx="16" cy="11.5" r="2.5" />
    </>
  ),
  space: (
    <>
      <rect x="4.5" y="4.5" width="10.5" height="10.5" />
      <rect x="17" y="4.5" width="10.5" height="10.5" />
      <rect x="4.5" y="17" width="10.5" height="10.5" />
      <path d="M18.5 18.5 L26 26 M26 18.5 L18.5 26" />
    </>
  ),
};

export function ServiceIcon({
  name,
  className,
}: {
  name: Service["icon"];
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={className}
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}
