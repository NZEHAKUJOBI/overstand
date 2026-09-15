"use client";

import Link from "next/link";
import { useActionState, useState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Input, Notice, Select, Textarea } from "@/components/admin/ui";
import {
  MAX_INVESTOR_SLOTS,
  MEMBER_STATUSES,
  MIN_INVESTOR_SLOTS,
  SLOT_PRICE_KOBO,
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
  tier: MemberTier;
  slots: number;
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
  tier: "investor",
  slots: MIN_INVESTOR_SLOTS,
  status: "pending",
  joinedOn: new Date().toISOString().slice(0, 10),
  notes: "",
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
  const [slots, setSlots] = useState(String(defaults.slots));

  const isInvestor = tier === "investor";
  const slotCount = Number(slots);
  const holdingKobo =
    Number.isFinite(slotCount) && slotCount > 0 ? slotCount * SLOT_PRICE_KOBO : 0;

  function onTierChange(value: MemberTier) {
    setTier(value);
    // The tiers are defined by whether slots are held at all, so keep the two
    // fields consistent instead of letting the server reject the combination.
    if (value === "non_investor") setSlots("0");
    else if (slots === "0") setSlots(String(MIN_INVESTOR_SLOTS));
  }

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

        <Field label="Address" name="address" error={state.fieldErrors?.address}>
          <Textarea
            id="address"
            name="address"
            rows={2}
            defaultValue={defaults.address}
          />
        </Field>
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Membership</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field label="Tier" name="tier" error={state.fieldErrors?.tier} required>
            <Select
              id="tier"
              name="tier"
              value={tier}
              onChange={(event) => onTierChange(event.target.value as MemberTier)}
            >
              <option value="investor">{TIER_LABEL.investor}</option>
              <option value="non_investor">{TIER_LABEL.non_investor}</option>
            </Select>
          </Field>

          <Field
            label="Ownership slots"
            name="slots"
            error={state.fieldErrors?.slots}
            hint={
              isInvestor
                ? `${MIN_INVESTOR_SLOTS.toLocaleString()}–${MAX_INVESTOR_SLOTS.toLocaleString()} · holding ${formatNaira(holdingKobo)}`
                : "Non-investor members hold no slots."
            }
            required
          >
            <Input
              id="slots"
              name="slots"
              type="number"
              inputMode="numeric"
              min={isInvestor ? MIN_INVESTOR_SLOTS : 0}
              max={MAX_INVESTOR_SLOTS}
              step={1}
              value={slots}
              onChange={(event) => setSlots(event.target.value)}
              readOnly={!isInvestor}
              className={isInvestor ? "" : "bg-paper-alt text-ink-faint"}
              required
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
            label="Dues start"
            name="joinedOn"
            error={state.fieldErrors?.joinedOn}
            hint="Monthly dues accrue from this month onward."
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
