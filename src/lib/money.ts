/**
 * Money helpers. Every amount crossing this boundary is an integer number of
 * kobo; naira only ever exist as a display string or as user input being
 * parsed. Nothing here uses floating point arithmetic on money.
 */

const nairaFormatter = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const plainFormatter = new Intl.NumberFormat("en-NG");

/** "₦20,000" for whole naira, "₦20,000.50" when there are stray kobo. */
export function formatNaira(kobo: number): string {
  const formatted = nairaFormatter.format(kobo / 100);
  return formatted.endsWith(".00") ? formatted.slice(0, -3) : formatted;
}

/** Compact form for dashboard tiles: ₦5.0bn, ₦12.4m, ₦850k. */
export function formatNairaCompact(kobo: number): string {
  const naira = kobo / 100;
  const abs = Math.abs(naira);

  if (abs >= 1_000_000_000) return `₦${trim(naira / 1_000_000_000)}bn`;
  if (abs >= 1_000_000) return `₦${trim(naira / 1_000_000)}m`;
  if (abs >= 1_000) return `₦${trim(naira / 1_000)}k`;
  return formatNaira(kobo);
}

function trim(value: number): string {
  return value.toFixed(1).replace(/\.0$/, "");
}

export function formatNumber(value: number): string {
  return plainFormatter.format(value);
}

/**
 * Parses user input ("20,000", "₦20,000.50", " 20000 ") into integer kobo.
 * Returns null for anything that is not a clean, non-negative amount, so
 * callers must handle the failure rather than silently coercing to zero.
 */
export function parseNairaToKobo(input: string): number | null {
  const cleaned = input.replace(/[₦,\s]/g, "");
  if (cleaned === "" || !/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;

  const [whole, fraction = ""] = cleaned.split(".");
  const kobo = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));

  return Number.isSafeInteger(kobo) ? kobo : null;
}

export function percentOf(part: number, whole: number): number {
  if (whole <= 0) return 0;
  return (part / whole) * 100;
}
