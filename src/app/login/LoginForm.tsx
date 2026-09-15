"use client";

import { useActionState } from "react";
import { SubmitButton } from "@/components/admin/SubmitButton";
import { Field, Input, Notice } from "@/components/admin/ui";
import { signIn, type LoginState } from "./actions";

const initial: LoginState = {};

export function LoginForm({ next }: { next?: string }) {
  const [state, action] = useActionState(signIn, initial);

  return (
    <form action={action} className="space-y-6" noValidate>
      {next ? <input type="hidden" name="next" value={next} /> : null}

      {state.error ? <Notice tone="error">{state.error}</Notice> : null}

      <Field label="Email" name="email" error={state.fieldErrors?.email} required>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          autoFocus
          required
        />
      </Field>

      <Field
        label="Password"
        name="password"
        error={state.fieldErrors?.password}
        required
      >
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </Field>

      <SubmitButton variant="gold" pendingLabel="Signing in…" className="w-full">
        Sign In
      </SubmitButton>
    </form>
  );
}
