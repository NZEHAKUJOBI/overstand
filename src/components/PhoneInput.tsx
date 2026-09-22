"use client";

import { useId, useState, type ChangeEvent } from "react";
import {
  COUNTRY_CODES,
  formatFullPhone,
  parsePhone,
} from "@/lib/countries";

interface PhoneInputProps {
  name: string;
  id?: string;
  defaultValue?: string;
  required?: boolean;
  disabled?: boolean;
  autoComplete?: string;
  placeholder?: string;
  className?: string;
}

export function PhoneInput({
  name,
  id: explicitId,
  defaultValue = "",
  required = false,
  disabled = false,
  autoComplete = "tel",
  placeholder = "803 000 0000",
  className = "",
}: PhoneInputProps) {
  const generatedId = useId();
  const inputId = explicitId || generatedId;

  // Initialize from defaultValue
  const initial = parsePhone(defaultValue);
  const [dialCode, setDialCode] = useState(initial.dialCode);
  const [nationalNumber, setNationalNumber] = useState(initial.nationalNumber);

  const selectedCountry =
    COUNTRY_CODES.find((c) => c.dialCode === dialCode) || COUNTRY_CODES[0];

  // Compute combined full phone for the form submission
  const combinedPhone = nationalNumber.trim()
    ? formatFullPhone(dialCode, nationalNumber)
    : "";

  const handleDialCodeChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setDialCode(e.target.value);
  };

  const handleNumberChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;

    // If user pastes or types a number starting with '+', parse it out
    if (val.startsWith("+")) {
      const parsed = parsePhone(val);
      setDialCode(parsed.dialCode);
      setNationalNumber(parsed.nationalNumber);
      return;
    }

    setNationalNumber(val);
  };

  return (
    <div
      className={`relative flex items-stretch border border-navy-900/20 bg-white transition-colors focus-within:border-gold-600 focus-within:ring-1 focus-within:ring-gold-500 ${className}`}
    >
      {/* Hidden input carrying the combined international value for formData.get(name) */}
      <input type="hidden" name={name} value={combinedPhone} />

      {/* Country code selector with compact visual display and full native select overlay */}
      <div className="relative flex shrink-0 items-center border-r border-navy-900/15 bg-paper-alt/40 hover:bg-paper-alt transition-colors">
        {/* Compact visual badge (Flag + Dial Code + Chevron) */}
        <div className="pointer-events-none flex items-center gap-1.5 px-3 py-3 text-[0.875rem] font-medium text-navy-950">
          <span className="text-base leading-none" aria-hidden="true">
            {selectedCountry?.flag ?? "🇳🇬"}
          </span>
          <span className="tnum font-mono text-[0.875rem]">{dialCode}</span>
          <svg
            className="h-3.5 w-3.5 text-ink-soft shrink-0"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </div>

        {/* Real accessible select element stretched over the visual area */}
        <select
          id={`${inputId}-dialcode`}
          value={dialCode}
          onChange={handleDialCodeChange}
          disabled={disabled}
          aria-label="Country dial code"
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
        >
          {COUNTRY_CODES.map((c) => (
            <option key={`${c.code}-${c.dialCode}`} value={c.dialCode}>
              {c.flag} {c.dialCode} — {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* National digits input taking all remaining width */}
      <input
        id={inputId}
        type="tel"
        value={nationalNumber}
        onChange={handleNumberChange}
        required={required}
        disabled={disabled}
        autoComplete={autoComplete}
        placeholder={placeholder}
        className="w-full min-w-0 flex-1 bg-transparent px-3.5 py-3 text-[0.9375rem] text-ink placeholder:text-ink-faint focus:outline-none disabled:opacity-50"
      />
    </div>
  );
}
