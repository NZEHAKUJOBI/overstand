import Link from "next/link";
import { EmptyState, PageHeader, Table, Td, Th } from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { AuditLog } from "@/lib/models/AuditLog";
import { ROLE_LABEL, isRole } from "@/lib/rbac";

const PAGE_SIZE = 40;

export const metadata = { title: "Activity" };

export default async function ActivityPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  await requirePermission("audit:read");
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam) || 1);

  await connectDb();

  const [entries, total] = await Promise.all([
    AuditLog.find()
      .sort({ createdAt: -1 })
      .skip((page - 1) * PAGE_SIZE)
      .limit(PAGE_SIZE)
      .lean(),
    AuditLog.countDocuments(),
  ]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <>
      <PageHeader
        title="Activity"
        description="Every change to the register, to payments and to admin accounts, with the officer who made it."
      />

      {entries.length === 0 ? (
        <EmptyState
          title="Nothing recorded yet"
          body="Changes made through the Secretariat will be listed here."
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>When</Th>
                <Th>Officer</Th>
                <Th>Change</Th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={String(entry._id)}>
                  <Td>
                    <span className="tnum">
                      {entry.createdAt.toLocaleDateString("en-NG", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="label-sm mt-1 block text-ink-faint">
                      {entry.createdAt.toLocaleTimeString("en-NG", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </Td>
                  <Td>
                    {entry.actorName}
                    <span className="label-sm mt-1 block text-ink-faint">
                      {isRole(entry.actorRole)
                        ? ROLE_LABEL[entry.actorRole]
                        : entry.actorRole}
                    </span>
                  </Td>
                  <Td>
                    {entry.entity === "member" && entry.entityId ? (
                      <Link
                        href={`/admin/members/${entry.entityId}`}
                        className="text-forest-900 underline-offset-4 hover:underline"
                      >
                        {entry.summary}
                      </Link>
                    ) : (
                      entry.summary
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>

          {pageCount > 1 ? (
            <nav
              aria-label="Pagination"
              className="mt-8 flex items-center justify-between gap-4"
            >
              <span className="label-sm text-ink-faint">
                Page {page} of {pageCount}
              </span>
              <div className="flex gap-3">
                {page > 1 ? (
                  <Link
                    href={`/admin/activity?page=${page - 1}`}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Previous
                  </Link>
                ) : null}
                {page < pageCount ? (
                  <Link
                    href={`/admin/activity?page=${page + 1}`}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Next
                  </Link>
                ) : null}
              </div>
            </nav>
          ) : null}
        </>
      )}
    </>
  );
}
