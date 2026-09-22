"use client";

import { useId, useState, type ChangeEvent } from "react";
import {
  COUNTRY_CODES,
  DEFAULT_DIAL_CODE,
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
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Hidden input carrying the combined international value for formData.get(name) */}
      <input type="hidden" name={name} value={combinedPhone} />

      {/* Country code selector */}
      <div className="relative shrink-0">
        <label htmlFor={`${inputId}-dialcode`} className="sr-only">
          Country dial code
        </label>
        <select
          id={`${inputId}-dialcode`}
          value={dialCode}
          onChange={handleDialCodeChange}
          disabled={disabled}
          aria-label="Country dial code"
          className="h-[42px] cursor-pointer appearance-none border border-navy-900/20 bg-white py-2 pl-3 pr-8 text-[0.875rem] font-medium text-navy-950 focus:border-gold-600 focus:outline-none focus:ring-1 focus:ring-gold-500 disabled:opacity-50"
        >
          {COUNTRY_CODES.map((c) => (
            <option key={`${c.code}-${c.dialCode}`} value={c.dialCode}>
              {c.flag} {c.dialCode} ({c.name})
            </option>
          ))}
        </select>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 right-2.5 flex items-center text-ink-soft"
        >
          <svg
            className="h-3.5 w-3.5 fill-current"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              fillRule="evenodd"
              d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      </div>

      {/* National digits input */}
      <div className="relative min-w-0 flex-1">
        <input
          id={inputId}
          type="tel"
          value={nationalNumber}
          onChange={handleNumberChange}
          required={required}
          disabled={disabled}
          autoComplete={autoComplete}
          placeholder={placeholder}
          className="h-[42px] w-full border border-navy-900/20 bg-white px-3.5 py-2 text-[0.9375rem] text-ink placeholder:text-ink-faint focus:border-gold-600 focus:outline-none focus:ring-1 focus:ring-gold-500 disabled:opacity-50"
        />
      </div>
    </div>
  );
}
