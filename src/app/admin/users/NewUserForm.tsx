"use client";

import { useActionState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Input, Notice, Select } from "@/components/admin/ui";
import { ROLES, ROLE_DESCRIPTION, ROLE_LABEL } from "@/lib/rbac";
import { createAdminUser } from "./actions";

export function NewUserForm() {
  const [state, action] = useActionState(createAdminUser, {});

  return (
    <form action={action} className="space-y-6" noValidate>
      {state.error ? <Notice tone="error">{state.error}</Notice> : null}
      {state.success ? <Notice tone="success">{state.success}</Notice> : null}

      <div className="grid gap-6 sm:grid-cols-2">
        <Field label="Name" name="name" error={state.fieldErrors?.name} required>
          <Input id="name" name="name" autoComplete="off" required />
        </Field>

        <Field label="Email" name="email" error={state.fieldErrors?.email} required>
          <Input id="email" name="email" type="email" autoComplete="off" required />
        </Field>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <Field
          label="Temporary password"
          name="password"
          error={state.fieldErrors?.password}
          hint="At least 12 characters. Share it out of band and have them change it."
          required
        >
          <Input
            id="password"
            name="password"
            type="text"
            autoComplete="new-password"
            required
          />
        </Field>

        <Field label="Role" name="role" error={state.fieldErrors?.role} required>
          <Select id="role" name="role" defaultValue="viewer">
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {ROLE_LABEL[role]} — {ROLE_DESCRIPTION[role]}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <SubmitButton variant="gold" pendingLabel="Creating…">
        Create Account
      </SubmitButton>
    </form>
  );
}
