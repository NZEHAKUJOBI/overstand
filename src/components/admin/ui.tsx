import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

/* Presentational primitives for the admin area, in the Society's palette. */

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-10 flex flex-col gap-5 border-b border-rule pb-7 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-[1.875rem] leading-tight tracking-[-0.015em] text-forest-900">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 max-w-2xl text-[0.9375rem] text-ink-soft">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

const buttonBase =
  "label inline-flex items-center justify-center px-5 py-3 transition-colors duration-200 disabled:cursor-not-allowed disabled:opacity-55";

const buttonVariants = {
  primary: "bg-forest-900 text-paper hover:bg-forest-800",
  gold: "bg-gold-400 text-forest-950 hover:bg-gold-300",
  ghost: "border border-forest-900/25 text-forest-900 hover:bg-forest-900/5",
  danger: "border border-alert/40 text-alert hover:bg-alert/8",
} as const;

export type ButtonVariant = keyof typeof buttonVariants;

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<"button"> & { variant?: ButtonVariant }) {
  return (
    <button
      {...props}
      className={`${buttonBase} ${buttonVariants[variant]} ${className}`}
    />
  );
}

export function ButtonLink({
  variant = "primary",
  className = "",
  ...props
}: ComponentProps<typeof Link> & { variant?: ButtonVariant }) {
  return (
    <Link
      {...props}
      className={`${buttonBase} ${buttonVariants[variant]} ${className}`}
    />
  );
}

/* ── Form fields ──────────────────────────────────────────────────── */

const controlClass =
  "w-full border border-forest-900/20 bg-white px-3.5 py-2.5 text-[0.9375rem] text-ink placeholder:text-ink-faint focus:border-gold-600 focus:outline-none";

export function Field({
  label,
  name,
  error,
  hint,
  children,
  required,
}: {
  label: string;
  name: string;
  error?: string;
  hint?: string;
  children: ReactNode;
  required?: boolean;
}) {
  const describedBy = error
    ? `${name}-error`
    : hint
      ? `${name}-hint`
      : undefined;

  return (
    <div>
      <label htmlFor={name} className="label-sm block text-ink-soft">
        {label}
        {required ? <span className="text-alert"> *</span> : null}
      </label>
      <div className="mt-2" data-described-by={describedBy}>
        {children}
      </div>
      {error ? (
        <p id={`${name}-error`} className="mt-2 text-[0.8125rem] text-alert">
          {error}
        </p>
      ) : hint ? (
        <p id={`${name}-hint`} className="mt-2 text-[0.8125rem] text-ink-faint">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function Input({ className = "", ...props }: ComponentProps<"input">) {
  return <input {...props} className={`${controlClass} ${className}`} />;
}

export function Select({ className = "", ...props }: ComponentProps<"select">) {
  return <select {...props} className={`${controlClass} ${className}`} />;
}

export function Textarea({
  className = "",
  ...props
}: ComponentProps<"textarea">) {
  return <textarea {...props} className={`${controlClass} ${className}`} />;
}

/* ── Feedback ─────────────────────────────────────────────────────── */

export function Notice({
  tone = "info",
  children,
}: {
  tone?: "info" | "error" | "success";
  children: ReactNode;
}) {
  const tones = {
    info: "border-forest-900/20 bg-paper-alt text-ink",
    error: "border-alert/35 bg-alert-soft text-alert",
    success: "border-ok/30 bg-ok-soft text-ok",
  } as const;

  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`border-l-2 px-4 py-3 text-[0.9375rem] ${tones[tone]}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "ok" | "warn" | "alert";
  children: ReactNode;
}) {
  const tones = {
    neutral: "bg-forest-900/8 text-ink-soft",
    ok: "bg-ok-soft text-ok",
    warn: "bg-gold-400/25 text-gold-700",
    alert: "bg-alert-soft text-alert",
  } as const;

  return (
    <span className={`label-sm inline-block px-2.5 py-1 ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="border border-dashed border-forest-900/20 px-6 py-16 text-center">
      <p className="font-display text-[1.25rem] text-forest-900">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-[0.9375rem] text-ink-soft">
        {body}
      </p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}

/* ── Data display ─────────────────────────────────────────────────── */

export function StatTile({
  label,
  value,
  detail,
  progress,
}: {
  label: string;
  value: string;
  detail?: string;
  progress?: number;
}) {
  return (
    <div className="border-t border-rule pt-6 pb-7">
      <p className="label-sm text-ink-faint">{label}</p>
      <p className="figure-num mt-3 text-[1.75rem] leading-none text-forest-900">
        {value}
      </p>
      {typeof progress === "number" ? (
        <div className="mt-4 h-1 w-full bg-forest-900/10">
          <div
            className="h-full bg-gold-500"
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      ) : null}
      {detail ? (
        <p className="mt-3 text-[0.8125rem] text-ink-soft">{detail}</p>
      ) : null}
    </div>
  );
}

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[46rem] border-collapse text-left">
        {children}
      </table>
    </div>
  );
}

export function Th({
  children,
  align = "left",
}: {
  children: ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th
      scope="col"
      className={`label-sm border-b border-forest-900/20 pb-3 text-ink-faint ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      {children}
    </th>
  );
}

export function Td({
  children,
  align = "left",
  className = "",
}: {
  children: ReactNode;
  align?: "left" | "right";
  className?: string;
}) {
  return (
    <td
      className={`border-b border-rule py-4 pr-6 align-top text-[0.9375rem] last:pr-0 ${
        align === "right" ? "text-right" : ""
      } ${className}`}
    >
      {children}
    </td>
  );
}

export function DescriptionList({ children }: { children: ReactNode }) {
  return <dl className="grid gap-px bg-rule sm:grid-cols-2">{children}</dl>;
}

export function DescriptionItem({
  term,
  children,
}: {
  term: string;
  children: ReactNode;
}) {
  return (
    <div className="bg-paper px-4 py-4">
      <dt className="label-sm text-ink-faint">{term}</dt>
      <dd className="mt-2 text-[0.9375rem] text-ink">{children}</dd>
    </div>
  );
}
