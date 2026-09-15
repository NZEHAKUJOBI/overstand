/** Identifies the field behind a MongoDB duplicate-key (E11000) error. */
export function duplicateKeyField(error: unknown): string | null {
  if (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    (error as { code?: unknown }).code === 11000
  ) {
    const pattern = (error as { keyPattern?: Record<string, unknown> })
      .keyPattern;
    return pattern ? (Object.keys(pattern)[0] ?? "unknown") : "unknown";
  }

  return null;
}

export function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
