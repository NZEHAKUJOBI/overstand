"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Input, Notice, Select, Textarea } from "@/components/admin/ui";
import {
  CONTRIBUTION_TIER_1_KOBO,
  CONTRIBUTION_TIER_2_KOBO,
  MEMBER_STATUSES,
  MEMBER_TIERS,
  STATUS_LABEL,
  TIER_LABEL,
  type MemberStatus,
  type MemberTier,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";
import type { MemberFormState } from "./actions";

export type MemberDefaults = {
  firstName: string;
  lastName: string;
  otherNames: string;
  email: string;
  phone: string;
  address: string;
  dateOfBirth: string;
  occupation: string;
  tier: MemberTier;
  customContribution: string;
  nextOfKinName: string;
  nextOfKinRelationship: string;
  nextOfKinPhone: string;
  nextOfKinEmail: string;
  nextOfKinAddress: string;
  status: MemberStatus;
  joinedOn: string;
  notes: string;
};

const empty: MemberDefaults = {
  firstName: "",
  lastName: "",
  otherNames: "",
  email: "",
  phone: "",
  address: "",
  dateOfBirth: "",
  occupation: "",
  tier: "tier_1",
  customContribution: "",
  nextOfKinName: "",
  nextOfKinRelationship: "",
  nextOfKinPhone: "",
  nextOfKinEmail: "",
  nextOfKinAddress: "",
  status: "pending",
  joinedOn: new Date().toISOString().slice(0, 10),
  notes: "",
};

const TIER_RATE: Record<MemberTier, string> = {
  tier_1: `${formatNaira(CONTRIBUTION_TIER_1_KOBO)} per month`,
  tier_2: `${formatNaira(CONTRIBUTION_TIER_2_KOBO)} per month`,
  custom: `Above ${formatNaira(CONTRIBUTION_TIER_2_KOBO)} — agreed with the member`,
};

export function MemberForm({
  action,
  memberId,
  defaults = empty,
  submitLabel,
  cancelHref,
}: {
  action: (
    previous: MemberFormState,
    formData: FormData,
  ) => Promise<MemberFormState>;
  memberId?: string;
  defaults?: MemberDefaults;
  submitLabel: string;
  cancelHref: string;
}) {
  const [state, formAction] = useActionState(action, {});
  const [tier, setTier] = useState<MemberTier>(defaults.tier);

  const isCustom = tier === "custom";

  return (
    <form action={formAction} className="max-w-3xl space-y-8" noValidate>
      {memberId ? <input type="hidden" name="memberId" value={memberId} /> : null}

      {state.error ? <Notice tone="error">{state.error}</Notice> : null}

      <fieldset className="space-y-6">
        <legend className="label text-gold-700">Personal details</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="First name"
            name="firstName"
            error={state.fieldErrors?.firstName}
            required
          >
            <Input
              id="firstName"
              name="firstName"
              defaultValue={defaults.firstName}
              autoComplete="off"
              required
            />
          </Field>

          <Field
            label="Surname"
            name="lastName"
            error={state.fieldErrors?.lastName}
            required
          >
            <Input
              id="lastName"
              name="lastName"
              defaultValue={defaults.lastName}
              autoComplete="off"
              required
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Other names"
            name="otherNames"
            error={state.fieldErrors?.otherNames}
          >
            <Input
              id="otherNames"
              name="otherNames"
              defaultValue={defaults.otherNames}
              autoComplete="off"
            />
          </Field>

          <Field
            label="Occupation"
            name="occupation"
            error={state.fieldErrors?.occupation}
          >
            <Input
              id="occupation"
              name="occupation"
              defaultValue={defaults.occupation}
              autoComplete="off"
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Email"
            name="email"
            error={state.fieldErrors?.email}
            required
          >
            <Input
              id="email"
              name="email"
              type="email"
              defaultValue={defaults.email}
              autoComplete="off"
              required
            />
          </Field>

          <Field
            label="Phone"
            name="phone"
            error={state.fieldErrors?.phone}
            hint="Include the country or network code."
            required
          >
            <Input
              id="phone"
              name="phone"
              type="tel"
              defaultValue={defaults.phone}
              autoComplete="off"
              required
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Date of birth"
            name="dateOfBirth"
            error={state.fieldErrors?.dateOfBirth}
            hint="Members must be at least 18."
          >
            <Input
              id="dateOfBirth"
              name="dateOfBirth"
              type="date"
              defaultValue={defaults.dateOfBirth}
            />
          </Field>

          <Field label="Address" name="address" error={state.fieldErrors?.address}>
            <Textarea
              id="address"
              name="address"
              rows={2}
              defaultValue={defaults.address}
            />
          </Field>
        </div>
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Next of kin</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Full name"
            name="nextOfKin.name"
            error={state.fieldErrors?.["nextOfKin.name"]}
            required
          >
            <Input
              id="nextOfKin.name"
              name="nextOfKin.name"
              defaultValue={defaults.nextOfKinName}
              autoComplete="off"
              required
            />
          </Field>

          <Field
            label="Relationship"
            name="nextOfKin.relationship"
            error={state.fieldErrors?.["nextOfKin.relationship"]}
            hint="Spouse, sibling, parent, and so on."
            required
          >
            <Input
              id="nextOfKin.relationship"
              name="nextOfKin.relationship"
              defaultValue={defaults.nextOfKinRelationship}
              autoComplete="off"
              required
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Phone"
            name="nextOfKin.phone"
            error={state.fieldErrors?.["nextOfKin.phone"]}
            required
          >
            <Input
              id="nextOfKin.phone"
              name="nextOfKin.phone"
              type="tel"
              defaultValue={defaults.nextOfKinPhone}
              autoComplete="off"
              required
            />
          </Field>

          <Field
            label="Email"
            name="nextOfKin.email"
            error={state.fieldErrors?.["nextOfKin.email"]}
          >
            <Input
              id="nextOfKin.email"
              name="nextOfKin.email"
              type="email"
              defaultValue={defaults.nextOfKinEmail}
              autoComplete="off"
            />
          </Field>
        </div>

        <Field
          label="Address"
          name="nextOfKin.address"
          error={state.fieldErrors?.["nextOfKin.address"]}
        >
          <Textarea
            id="nextOfKin.address"
            name="nextOfKin.address"
            rows={2}
            defaultValue={defaults.nextOfKinAddress}
          />
        </Field>
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Membership</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Contribution tier"
            name="tier"
            error={state.fieldErrors?.tier}
            hint={TIER_RATE[tier]}
            required
          >
            <Select
              id="tier"
              name="tier"
              value={tier}
              onChange={(event) => setTier(event.target.value as MemberTier)}
            >
              {MEMBER_TIERS.map((value) => (
                <option key={value} value={value}>
                  {TIER_LABEL[value]}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Agreed monthly amount"
            name="customContribution"
            error={state.fieldErrors?.customContribution}
            hint={
              isCustom
                ? `Must be above ${formatNaira(CONTRIBUTION_TIER_2_KOBO)}.`
                : "Only for a tailored contribution."
            }
            required={isCustom}
          >
            <Input
              id="customContribution"
              name="customContribution"
              inputMode="decimal"
              placeholder="75,000"
              defaultValue={defaults.customContribution}
              disabled={!isCustom}
              className={isCustom ? "" : "bg-paper-alt text-ink-faint"}
              required={isCustom}
            />
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Status"
            name="status"
            error={state.fieldErrors?.status}
            required
          >
            <Select id="status" name="status" defaultValue={defaults.status}>
              {MEMBER_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABEL[status]}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Contribution start"
            name="joinedOn"
            error={state.fieldErrors?.joinedOn}
            hint="Monthly contributions accrue from this month onward."
            required
          >
            <Input
              id="joinedOn"
              name="joinedOn"
              type="date"
              defaultValue={defaults.joinedOn}
              required
            />
          </Field>
        </div>

        <Field label="Notes" name="notes" error={state.fieldErrors?.notes}>
          <Textarea id="notes" name="notes" rows={3} defaultValue={defaults.notes} />
        </Field>
      </fieldset>

      <div className="flex items-center gap-4 border-t border-rule pt-6">
        <SubmitButton variant="gold">{submitLabel}</SubmitButton>
        <Link
          href={cancelHref}
          className="label-sm text-ink-soft underline-offset-4 hover:underline"
        >
          Cancel
        </Link>
      </div>
    </form>
  );
}
