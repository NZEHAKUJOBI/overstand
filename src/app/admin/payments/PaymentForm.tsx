"use client";

import Link from "next/link";
import { useActionState, useMemo, useState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Input, Notice, Select, Textarea } from "@/components/admin/ui";
import {
  APPLICATION_FEE_KOBO,
  BANKS,
  KIND_LABEL,
  METHOD_LABEL,
  PAYMENT_KINDS,
  PAYMENT_METHODS,
  REGISTRATION_FEE_KOBO,
  contributionRateKobo,
  type MemberTier,
  type PaymentKind,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";
import { recordPayment } from "./actions";

export type MemberOption = {
  id: string;
  label: string;
  tier: MemberTier;
  /** Needed so a tailored member prefills at their own rate, not the floor. */
  customContributionKobo?: number | null;
};

/** Naira, no separators — what the amount input expects. */
function plainAmount(kobo: number): string {
  return String(Math.round(kobo / 100));
}

export function PaymentForm({
  members,
  selectedMemberId,
}: {
  members: MemberOption[];
  selectedMemberId?: string;
}) {
  const [state, formAction] = useActionState(recordPayment, {});

  const [memberId, setMemberId] = useState(selectedMemberId ?? "");
  const [kind, setKind] = useState<PaymentKind>("contribution");
  const [amount, setAmount] = useState("");
  const [touchedAmount, setTouchedAmount] = useState(false);

  const member = useMemo(
    () => members.find((option) => option.id === memberId),
    [members, memberId],
  );

  /**
   * The expected amount for this member and payment type. Used to prefill the
   * field, but never to overwrite a figure the officer has typed — the amount
   * actually received is what gets recorded, not what was owed.
   */
  const expectedKobo =
    kind === "application"
      ? APPLICATION_FEE_KOBO
      : kind === "registration"
        ? // Null until the Society supplies the registration fee amount, in
          // which case nothing is prefilled and the officer enters it.
          REGISTRATION_FEE_KOBO
        : kind === "contribution" && member
          ? contributionRateKobo(member.tier, member.customContributionKobo)
          : null;

  const shownAmount =
    touchedAmount || expectedKobo === null ? amount : plainAmount(expectedKobo);

  function onKindChange(next: PaymentKind) {
    setKind(next);
    if (!touchedAmount) setAmount("");
  }

  const thisMonth = new Date().toISOString().slice(0, 7);
  const today = new Date().toISOString().slice(0, 10);

  return (
    <form action={formAction} className="max-w-3xl space-y-8" noValidate>
      {state.error ? <Notice tone="error">{state.error}</Notice> : null}

      <fieldset className="space-y-6">
        <legend className="label text-gold-700">Receipt</legend>

        <Field
          label="Member"
          name="memberId"
          error={state.fieldErrors?.memberId}
          required
        >
          <Select
            id="memberId"
            name="memberId"
            value={memberId}
            onChange={(event) => setMemberId(event.target.value)}
            required
          >
            <option value="">Select a member…</option>
            {members.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </Select>
        </Field>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field label="Type" name="kind" error={state.fieldErrors?.kind} required>
            <Select
              id="kind"
              name="kind"
              value={kind}
              onChange={(event) => onKindChange(event.target.value as PaymentKind)}
            >
              {PAYMENT_KINDS.map((value) => (
                <option key={value} value={value}>
                  {KIND_LABEL[value]}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Amount received"
            name="amount"
            error={state.fieldErrors?.amount}
            hint={
              expectedKobo !== null
                ? `Expected ${formatNaira(expectedKobo)} — change it if a different sum was received.`
                : "In naira, e.g. 25,000"
            }
            required
          >
            <Input
              id="amount"
              name="amount"
              inputMode="decimal"
              value={shownAmount}
              onChange={(event) => {
                setTouchedAmount(true);
                setAmount(event.target.value);
              }}
              placeholder="0"
              required
            />
          </Field>
        </div>

        {kind === "contribution" ? (
          <Field
            label="Contribution month"
            name="contributionPeriod"
            error={state.fieldErrors?.contributionPeriod}
            hint="The month these contributions settle. One contribution entry per member per month."
            required
          >
            <Input
              id="contributionPeriod"
              name="contributionPeriod"
              type="month"
              defaultValue={thisMonth}
              required
            />
          </Field>
        ) : null}
      </fieldset>

      <fieldset className="space-y-6 border-t border-rule pt-8">
        <legend className="label text-gold-700">Settlement</legend>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Method"
            name="method"
            error={state.fieldErrors?.method}
            required
          >
            <Select id="method" name="method" defaultValue="bank_transfer">
              {PAYMENT_METHODS.map((value) => (
                <option key={value} value={value}>
                  {METHOD_LABEL[value]}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Bank" name="bank" error={state.fieldErrors?.bank}>
            <Select id="bank" name="bank" defaultValue="">
              <option value="">Not applicable</option>
              {BANKS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <Field
            label="Reference"
            name="reference"
            error={state.fieldErrors?.reference}
            hint="Teller number, transfer reference or receipt number."
          >
            <Input id="reference" name="reference" autoComplete="off" />
          </Field>

          <Field
            label="Date received"
            name="receivedOn"
            error={state.fieldErrors?.receivedOn}
            required
          >
            <Input
              id="receivedOn"
              name="receivedOn"
              type="date"
              defaultValue={today}
              max={today}
              required
            />
          </Field>
        </div>

        <Field label="Note" name="note" error={state.fieldErrors?.note}>
          <Textarea id="note" name="note" rows={2} />
        </Field>
      </fieldset>

      <div className="flex items-center gap-4 border-t border-rule pt-6">
        <SubmitButton variant="gold" pendingLabel="Recording…">
          Record Payment
        </SubmitButton>
        <Link
          href={selectedMemberId ? `/admin/members/${selectedMemberId}` : "/admin/payments"}
          className="label-sm text-ink-soft underline-offset-4 hover:underline"
        >
          Cancel
        </Link>
      </div>
    </form>
  );
}
