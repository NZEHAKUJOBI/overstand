"use client";

import { useEffect } from "react";
import { Button, Notice, PageHeader } from "@/components/admin/ui";

/**
 * Most failures here are a missing or unreachable MONGODB_URI, so the message
 * points at that first rather than showing a bare stack trace.
 */
export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[admin]", error);
  }, [error]);

  const looksLikeDatabase =
    /mongo|MONGODB_URI|ECONNREFUSED|ServerSelection|querySrv/i.test(
      error.message,
    );

  return (
    <>
      <PageHeader title="Something went wrong" />

      <div className="max-w-2xl space-y-6">
        <Notice tone="error">
          {looksLikeDatabase
            ? "The database could not be reached."
            : "This page failed to load."}
        </Notice>

        {looksLikeDatabase ? (
          <div className="space-y-3 text-[0.9375rem] text-ink-soft">
            <p>Check that:</p>
            <ul className="list-disc space-y-1.5 pl-5">
              <li>
                <code className="font-mono text-[0.875rem]">MONGODB_URI</code> is
                set in <code className="font-mono text-[0.875rem]">.env.local</code>{" "}
                locally, or in the Render service environment.
              </li>
              <li>
                On MongoDB Atlas, this server&rsquo;s IP is allowed under Network
                Access.
              </li>
              <li>The database user&rsquo;s password is URL-encoded in the URI.</li>
            </ul>
          </div>
        ) : null}

        <details className="border border-rule bg-paper-alt px-4 py-3">
          <summary className="label-sm cursor-pointer text-ink-soft">
            Technical detail
          </summary>
          <p className="mt-3 font-mono text-[0.8125rem] break-words text-ink-soft">
            {error.message}
            {error.digest ? ` (digest: ${error.digest})` : ""}
          </p>
        </details>

        <Button onClick={reset} variant="ghost">
          Try again
        </Button>
      </div>
    </>
  );
}
