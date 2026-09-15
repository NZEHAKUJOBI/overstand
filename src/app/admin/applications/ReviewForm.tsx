"use client";

import { useActionState, useState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Notice, Select, Textarea } from "@/components/admin/ui";
import { reviewEnquiry, type ReviewState } from "./actions";

const DECISIONS = [
  { value: "reviewing", label: "Mark as reviewing" },
  { value: "approved", label: "Approve — create a pending member record" },
  { value: "declined", label: "Decline" },
] as const;

export function ReviewForm({
  enquiryId,
  currentStatus,
  alreadyLinked,
}: {
  enquiryId: string;
  currentStatus: string;
  alreadyLinked: boolean;
}) {
  const [state, action] = useActionState<ReviewState, FormData>(
    reviewEnquiry,
    {},
  );
  const [decision, setDecision] = useState<string>(
    currentStatus === "new" ? "reviewing" : currentStatus,
  );

  return (
    <form action={action} className="space-y-6" noValidate>
      <input type="hidden" name="enquiryId" value={enquiryId} />

      {state.error ? <Notice tone="error">{state.error}</Notice> : null}
      {state.success ? <Notice tone="success">{state.success}</Notice> : null}

      <Field label="Decision" name="decision" error={state.fieldErrors?.decision} required>
        <Select
          id="decision"
          name="decision"
          value={decision}
          onChange={(event) => setDecision(event.target.value)}
        >
          {DECISIONS.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.value === "approved" && alreadyLinked}
            >
              {option.label}
            </option>
          ))}
        </Select>
      </Field>

      {decision === "approved" && !alreadyLinked ? (
        <Notice tone="info">
          A member record will be created with status <strong>pending</strong>,
          pre-filled from this enquiry. It does not admit the applicant or take
          any payment — an officer completes admission on the member record.
        </Notice>
      ) : null}

      <Field
        label="Note"
        name="reviewNote"
        error={state.fieldErrors?.reviewNote}
        hint="Recorded against the enquiry and visible to other officers."
      >
        <Textarea id="reviewNote" name="reviewNote" rows={3} />
      </Field>

      <SubmitButton variant="gold" pendingLabel="Saving…">
        Save Decision
      </SubmitButton>
    </form>
  );
}
