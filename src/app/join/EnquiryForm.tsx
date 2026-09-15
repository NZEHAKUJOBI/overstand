"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { useFormStatus } from "react-dom";
import {
  MAX_INVESTOR_SLOTS,
  MIN_INVESTOR_SLOTS,
  SLOT_PRICE_KOBO,
  TIER_INTERESTS,
  TIER_INTEREST_LABEL,
  type TierInterest,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";
import { submitEnquiry, type EnquiryFormState } from "./actions";

const control =
  "w-full border border-forest-900/20 bg-white px-3.5 py-3 text-[0.9375rem] text-ink placeholder:text-ink-faint focus:border-gold-600 focus:outline-none";

function Field({
  label,
  name,
  error,
  hint,
  required,
  children,
}: {
  label: string;
  name: string;
  error?: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={name} className="label-sm block text-ink-soft">
        {label}
        {required ? <span className="text-alert"> *</span> : null}
      </label>
      <div className="mt-2">{children}</div>
      {error ? (
        <p className="mt-2 text-[0.8125rem] text-alert">{error}</p>
      ) : hint ? (
        <p className="mt-2 text-[0.8125rem] text-ink-faint">{hint}</p>
      ) : null}
    </div>
  );
}

function Submit() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      aria-busy={pending}
      className="label bg-forest-900 px-8 py-4 text-paper transition-colors duration-200 hover:bg-forest-800 disabled:cursor-not-allowed disabled:opacity-55"
    >
      {pending ? "Submitting…" : "Register My Interest"}
    </button>
  );
}

export function EnquiryForm() {
  const [state, action] = useActionState<EnquiryFormState, FormData>(
    submitEnquiry,
    {},
  );
  const [tier, setTier] = useState<TierInterest>("investor");
  const [slots, setSlots] = useState("");

  if (state.reference) {
    return (
      <div className="border-t-2 border-gold-500 bg-paper px-7 py-12 sm:px-10">
        <p className="label text-gold-700">Enquiry received</p>
        <h2 className="font-display mt-5 text-[1.75rem] leading-tight text-forest-900 sm:text-[2rem]">
          Thank you — we have your details.
        </h2>
        <p className="mt-5 max-w-xl text-[1.0625rem] leading-relaxed text-ink-soft">
          Your reference is{" "}
          <strong className="tnum text-forest-900">{state.reference}</strong>.
          Please quote it in any correspondence. A member of the Secretariat
          will contact you.
        </p>

        {state.mailDelayed ? (
          <p className="mt-6 max-w-xl border-l-2 border-gold-600 pl-5 text-[0.9375rem] leading-relaxed text-ink-soft">
            We could not send your confirmation email just now, but your enquiry
            is safely recorded. If you do not hear from us within a few days,
            call the Secretariat on{" "}
            <a href="tel:+2349025250026" className="underline underline-offset-4">
              +234 902 525 0026
            </a>
            .
          </p>
        ) : (
          <p className="mt-6 text-[0.9375rem] text-ink-soft">
            A confirmation has been sent to your email address.
          </p>
        )}

        <p className="mt-9">
          <Link
            href="/"
            className="label-sm text-forest-900 underline-offset-4 hover:underline"
          >
            ← Back to the Society
          </Link>
        </p>
      </div>
    );
  }

  const slotCount = Number(slots);
  const holdingKobo =
    Number.isInteger(slotCount) && slotCount > 0 ? slotCount * SLOT_PRICE_KOBO : 0;

  return (
    <form action={action} className="space-y-8" noValidate>
      {state.error ? (
        <div
          role="alert"
          className="border-l-2 border-alert bg-alert-soft px-4 py-3 text-[0.9375rem] text-alert"
        >
          {state.error}
        </div>
      ) : null}

      {/* Honeypot — hidden from people, tempting to bots. */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-px w-px overflow-hidden">
        <label htmlFor="website">Website</label>
        <input id="website" name="website" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <fieldset className="space-y-6">
        <legend className="label text-gold-700">Your details</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field label="First name" name="firstName" error={state.fieldErrors?.firstName} required>
            <input id="firstName" name="firstName" className={control} autoComplete="given-name" required />
          </Field>
          <Field label="Surname" name="lastName" error={state.fieldErrors?.lastName} required>
            <input id="lastName" name="lastName" className={control} autoComplete="family-name" required />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field label="Email" name="email" error={state.fieldErrors?.email} required>
            <input id="email" name="email" type="email" className={control} autoComplete="email" required />
          </Field>
          <Field
            label="Phone"
            name="phone"
            error={state.fieldErrors?.phone}
            hint="Include the network code, e.g. 0803…"
            required
          >
            <input id="phone" name="phone" type="tel" className={control} autoComplete="tel" required />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field label="Occupation" name="occupation" error={state.fieldErrors?.occupation}>
            <input id="occupation" name="occupation" className={control} autoComplete="organization-title" />
          </Field>
          <Field label="How did you hear about us?" name="heardFrom" error={state.fieldErrors?.heardFrom}>
            <input id="heardFrom" name="heardFrom" className={control} />
          </Field>
        </div>

        <Field label="Address" name="address" error={state.fieldErrors?.address}>
          <textarea id="address" name="address" rows={2} className={control} autoComplete="street-address" />
        </Field>
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Your interest</legend>

        <Field
          label="Which tier interests you?"
          name="tierInterest"
          error={state.fieldErrors?.tierInterest}
          required
        >
          <div className="space-y-3">
            {TIER_INTERESTS.map((value) => (
              <label
                key={value}
                className={`flex cursor-pointer items-start gap-3 border px-4 py-3.5 transition-colors ${
                  tier === value
                    ? "border-gold-600 bg-gold-400/10"
                    : "border-forest-900/20 hover:bg-forest-900/[0.03]"
                }`}
              >
                <input
                  type="radio"
                  name="tierInterest"
                  value={value}
                  checked={tier === value}
                  onChange={() => setTier(value)}
                  className="mt-1 accent-forest-800"
                />
                <span className="text-[0.9375rem] leading-snug text-ink">
                  {TIER_INTEREST_LABEL[value]}
                </span>
              </label>
            ))}
          </div>
        </Field>

        {tier === "investor" ? (
          <Field
            label="Slots you are considering"
            name="slotsInterest"
            error={state.fieldErrors?.slotsInterest}
            hint={
              holdingKobo > 0
                ? `A holding of ${formatNaira(holdingKobo)}. Optional — an indication only.`
                : `${MIN_INVESTOR_SLOTS.toLocaleString()}–${MAX_INVESTOR_SLOTS.toLocaleString()} slots at ₦5,000 each. Optional.`
            }
          >
            <input
              id="slotsInterest"
              name="slotsInterest"
              type="number"
              inputMode="numeric"
              min={MIN_INVESTOR_SLOTS}
              max={MAX_INVESTOR_SLOTS}
              step={1}
              value={slots}
              onChange={(event) => setSlots(event.target.value)}
              placeholder="e.g. 100"
              className={control}
            />
          </Field>
        ) : null}

        <Field
          label="Anything you would like to tell us?"
          name="message"
          error={state.fieldErrors?.message}
        >
          <textarea id="message" name="message" rows={4} className={control} />
        </Field>
      </fieldset>

      <div className="border-t border-rule pt-7">
        <p className="mb-6 max-w-xl text-[0.875rem] leading-relaxed text-ink-soft">
          Submitting this form registers your interest only. It does not create
          membership and commits you to no payment. The Society will send the
          formal documentation once the Board has adopted it.
        </p>
        <Submit />
      </div>
    </form>
  );
}
