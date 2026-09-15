"use client";

import { useFormStatus } from "react-dom";
import { Button, type ButtonVariant } from "./ui";

/**
 * Disables itself while its form is in flight, so a slow network cannot
 * produce a duplicate member or a double-recorded payment.
 */
export function SubmitButton({
  children,
  pendingLabel = "Saving…",
  variant = "primary",
  className,
}: {
  children: string;
  pendingLabel?: string;
  variant?: ButtonVariant;
  className?: string;
}) {
  const { pending } = useFormStatus();

  return (
    <Button
      type="submit"
      variant={variant}
      disabled={pending}
      aria-busy={pending}
      className={className}
    >
      {pending ? pendingLabel : children}
    </Button>
  );
}
