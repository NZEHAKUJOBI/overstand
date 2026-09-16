"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { useFormStatus } from "react-dom";
import {
  APPLICATION_FEE_KOBO,
  CONTRIBUTION_TIER_2_KOBO,
  MIN_MEMBER_AGE,
  TIER_INTERESTS,
  TIER_INTEREST_LABEL,
  type TierInterest,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";
import { offices } from "@/lib/content";
import { submitApplication, type ApplicationFormState } from "./actions";

const control =
  "w-full border border-navy-900/20 bg-white px-3.5 py-3 text-[0.9375rem] text-ink placeholder:text-ink-faint focus:border-gold-600 focus:outline-none";

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
      className="label bg-navy-900 px-8 py-4 text-paper transition-colors duration-200 hover:bg-navy-800 disabled:cursor-not-allowed disabled:opacity-55"
    >
      {pending ? "Submitting…" : "Submit my application"}
    </button>
  );
}

export function ApplicationForm() {
  const [state, action] = useActionState<ApplicationFormState, FormData>(
    submitApplication,
    {},
  );
  const [tier, setTier] = useState<TierInterest>("tier_1");

  if (state.reference) {
    return (
      <div className="border-t-2 border-gold-500 bg-paper px-7 py-12 sm:px-10">
        <p className="label text-gold-700">Application received</p>
        <h2 className="font-display mt-5 text-[1.75rem] leading-tight text-navy-900 sm:text-[2rem]">
          Thank you — we have your details.
        </h2>
        <p className="mt-5 max-w-xl text-[1.0625rem] leading-relaxed text-ink-soft">
          Your reference is{" "}
          <strong className="tnum text-navy-900">{state.reference}</strong>.
          Please quote it in any correspondence. A member of the Secretariat
          will contact you with the Membership/Entrance Form and instructions
          for the {formatNaira(APPLICATION_FEE_KOBO)} application fee.
        </p>

        {state.mailDelayed ? (
          <p className="mt-6 max-w-xl border-l-2 border-gold-600 pl-5 text-[0.9375rem] leading-relaxed text-ink-soft">
            We could not send your confirmation email just now, but your
            application is safely recorded. If you do not hear from us within a
            few days, call at the Society&apos;s office —{" "}
            {offices[0].lines.join(", ")}.
          </p>
        ) : (
          <p className="mt-6 text-[0.9375rem] text-ink-soft">
            A confirmation has been sent to your email address.
          </p>
        )}

        <p className="mt-9">
          <Link
            href="/"
            className="label-sm text-navy-900 underline-offset-4 hover:underline"
          >
            ← Back to the Society
          </Link>
        </p>
      </div>
    );
  }

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
          <Field label="Other names" name="otherNames" error={state.fieldErrors?.otherNames}>
            <input id="otherNames" name="otherNames" className={control} autoComplete="additional-name" />
          </Field>
          <Field
            label="Date of birth"
            name="dateOfBirth"
            error={state.fieldErrors?.dateOfBirth}
            hint={`Membership is open from age ${MIN_MEMBER_AGE}.`}
            required
          >
            <input id="dateOfBirth" name="dateOfBirth" type="date" className={control} autoComplete="bday" required />
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
        <legend className="label text-gold-700">Next of kin</legend>

        <p className="max-w-xl text-[0.875rem] leading-relaxed text-ink-soft">
          The Membership Application Form requires next-of-kin details. We will
          hold them with your membership record.
        </p>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Full name"
            name="nextOfKin.name"
            error={state.fieldErrors?.["nextOfKin.name"]}
            required
          >
            <input id="nextOfKin.name" name="nextOfKin.name" className={control} required />
          </Field>
          <Field
            label="Relationship to you"
            name="nextOfKin.relationship"
            error={state.fieldErrors?.["nextOfKin.relationship"]}
            hint="Spouse, sibling, parent, and so on."
            required
          >
            <input id="nextOfKin.relationship" name="nextOfKin.relationship" className={control} required />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Phone"
            name="nextOfKin.phone"
            error={state.fieldErrors?.["nextOfKin.phone"]}
            required
          >
            <input id="nextOfKin.phone" name="nextOfKin.phone" type="tel" className={control} required />
          </Field>
          <Field
            label="Email"
            name="nextOfKin.email"
            error={state.fieldErrors?.["nextOfKin.email"]}
          >
            <input id="nextOfKin.email" name="nextOfKin.email" type="email" className={control} />
          </Field>
        </div>

        <Field
          label="Address"
          name="nextOfKin.address"
          error={state.fieldErrors?.["nextOfKin.address"]}
        >
          <textarea id="nextOfKin.address" name="nextOfKin.address" rows={2} className={control} />
        </Field>
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Your contribution</legend>

        <Field
          label="Which monthly tier suits you?"
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
                    : "border-navy-900/20 hover:bg-navy-900/[0.03]"
                }`}
              >
                <input
                  type="radio"
                  name="tierInterest"
                  value={value}
                  checked={tier === value}
                  onChange={() => setTier(value)}
                  className="mt-1 accent-navy-800"
                />
                <span className="text-[0.9375rem] leading-snug text-ink">
                  {TIER_INTEREST_LABEL[value]}
                </span>
              </label>
            ))}
          </div>
        </Field>

        {tier === "custom" ? (
          <Field
            label="Monthly amount you intend to contribute"
            name="customContribution"
            error={state.fieldErrors?.customContribution}
            hint={`Above ${formatNaira(CONTRIBUTION_TIER_2_KOBO)}. The Secretariat will agree the final structure with you.`}
            required
          >
            <input
              id="customContribution"
              name="customContribution"
              inputMode="decimal"
              placeholder="75,000"
              className={control}
              required
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

      <fieldset className="border-t border-rule pt-8">
        <legend className="label text-gold-700">Declaration</legend>

        <label
          htmlFor="eligibilityConfirmed"
          className="mt-6 flex cursor-pointer items-start gap-3"
        >
          <input
            id="eligibilityConfirmed"
            name="eligibilityConfirmed"
            type="checkbox"
            className="mt-1 h-4 w-4 shrink-0 accent-navy-800"
          />
          <span className="text-[0.9375rem] leading-relaxed text-ink">
            I confirm that I am at least {MIN_MEMBER_AGE} years of age, of good
            character and of sound mind, and that the details above are correct.
          </span>
        </label>

        {state.fieldErrors?.eligibilityConfirmed ? (
          <p className="mt-2 text-[0.8125rem] text-alert">
            {state.fieldErrors.eligibilityConfirmed}
          </p>
        ) : null}
      </fieldset>

      <div className="border-t border-rule pt-7">
        <p className="mb-6 max-w-xl text-[0.875rem] leading-relaxed text-ink-soft">
          Submitting this form starts your application. It does not admit you to
          membership and takes no payment — the Secretariat will contact you
          with the Membership/Entrance Form and instructions for the{" "}
          {formatNaira(APPLICATION_FEE_KOBO)} application fee, which is
          non-refundable.
        </p>
        <Submit />
      </div>
    </form>
  );
}
