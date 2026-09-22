export interface CountryCode {
  name: string;
  code: string; // ISO 3166-1 alpha-2
  dialCode: string; // e.g. "+234"
  flag: string;
}

/**
 * Common countries prioritized for the Overstand Cooperative,
 * followed by standard international options.
 */
export const COUNTRY_CODES: CountryCode[] = [
  // Primary (Society home)
  { name: "Nigeria", code: "NG", dialCode: "+234", flag: "🇳🇬" },

  // Key diaspora & West Africa
  { name: "United Kingdom", code: "GB", dialCode: "+44", flag: "🇬🇧" },
  { name: "United States", code: "US", dialCode: "+1", flag: "🇺🇸" },
  { name: "Canada", code: "CA", dialCode: "+1", flag: "🇨🇦" },
  { name: "Ghana", code: "GH", dialCode: "+233", flag: "🇬🇭" },
  { name: "South Africa", code: "ZA", dialCode: "+27", flag: "🇿🇦" },
  { name: "Kenya", code: "KE", dialCode: "+254", flag: "🇰🇪" },
  { name: "United Arab Emirates", code: "AE", dialCode: "+971", flag: "🇦🇪" },

  // Other countries alphabetical
  { name: "Australia", code: "AU", dialCode: "+61", flag: "🇦🇺" },
  { name: "Benin", code: "BJ", dialCode: "+229", flag: "🇧🇯" },
  { name: "Cameroon", code: "CM", dialCode: "+237", flag: "🇨🇲" },
  { name: "China", code: "CN", dialCode: "+86", flag: "🇨🇳" },
  { name: "Côte d'Ivoire", code: "CI", dialCode: "+225", flag: "🇨🇮" },
  { name: "Egypt", code: "EG", dialCode: "+20", flag: "🇪🇬" },
  { name: "France", code: "FR", dialCode: "+33", flag: "🇫🇷" },
  { name: "Gambia", code: "GM", dialCode: "+220", flag: "🇬🇲" },
  { name: "Germany", code: "DE", dialCode: "+49", flag: "🇩🇪" },
  { name: "India", code: "IN", dialCode: "+91", flag: "🇮🇳" },
  { name: "Ireland", code: "IE", dialCode: "+353", flag: "🇮🇪" },
  { name: "Italy", code: "IT", dialCode: "+39", flag: "🇮🇹" },
  { name: "Liberia", code: "LR", dialCode: "+231", flag: "🇱🇷" },
  { name: "Malaysia", code: "MY", dialCode: "+60", flag: "🇲🇾" },
  { name: "Netherlands", code: "NL", dialCode: "+31", flag: "🇳🇱" },
  { name: "Niger", code: "NE", dialCode: "+227", flag: "🇳🇪" },
  { name: "Qatar", code: "QA", dialCode: "+974", flag: "🇶🇦" },
  { name: "Rwanda", code: "RW", dialCode: "+250", flag: "🇷🇼" },
  { name: "Saudi Arabia", code: "SA", dialCode: "+966", flag: "🇸🇦" },
  { name: "Senegal", code: "SN", dialCode: "+221", flag: "🇸🇳" },
  { name: "Sierra Leone", code: "SL", dialCode: "+232", flag: "🇸🇱" },
  { name: "Togo", code: "TG", dialCode: "+228", flag: "🇹🇬" },
  { name: "Uganda", code: "UG", dialCode: "+256", flag: "🇺🇬" },
  { name: "Zambia", code: "ZM", dialCode: "+260", flag: "🇿🇲" },
];

export const DEFAULT_DIAL_CODE = "+234";

/**
 * Deconstructs a stored phone string into its dial code and national digits.
 * If raw input starts with a plus, matches against known dial codes (longest first).
 * If no plus, assumes Nigeria (+234) and strips any leading zero.
 */
export function parsePhone(raw: string | undefined | null): {
  dialCode: string;
  nationalNumber: string;
} {
  if (!raw) {
    return { dialCode: DEFAULT_DIAL_CODE, nationalNumber: "" };
  }

  const trimmed = raw.trim();
  if (!trimmed) {
    return { dialCode: DEFAULT_DIAL_CODE, nationalNumber: "" };
  }

  if (trimmed.startsWith("+")) {
    // Sort dial codes by length descending so +234 matches before shorter prefixes if any
    const sorted = [...COUNTRY_CODES].sort(
      (a, b) => b.dialCode.length - a.dialCode.length,
    );

    for (const c of sorted) {
      if (trimmed.startsWith(c.dialCode)) {
        const national = trimmed.slice(c.dialCode.length).trim();
        return { dialCode: c.dialCode, nationalNumber: national };
      }
    }

    // Unmatched '+' prefix: extract leading digits as dial code up to 4 digits
    const match = trimmed.match(/^(\+\d{1,4})\s*(.*)$/);
    if (match) {
      return { dialCode: match[1], nationalNumber: match[2].trim() };
    }

    return { dialCode: DEFAULT_DIAL_CODE, nationalNumber: trimmed.replace(/^\+/, "") };
  }

  // No country code provided: if starts with 0 (Nigerian local), strip leading 0
  const national = trimmed.startsWith("0") ? trimmed.slice(1) : trimmed;
  return { dialCode: DEFAULT_DIAL_CODE, nationalNumber: national };
}

/**
 * Combines dial code and national number into an international E.164-like string.
 * Strips any accidental leading zero entered in the national number when combined with dial code.
 */
export function formatFullPhone(dialCode: string, nationalNumber: string): string {
  const cleanedNational = nationalNumber.trim().replace(/^0+/, "");
  if (!cleanedNational) {
    return "";
  }
  return `${dialCode.trim()} ${cleanedNational}`;
}
