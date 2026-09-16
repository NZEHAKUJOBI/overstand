import Link from "next/link";
import type { QueryFilter } from "mongoose";
import {
  Badge,
  EmptyState,
  PageHeader,
  Select,
  Table,
  Td,
  Th,
} from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Application, type ApplicationDoc } from "@/lib/models/Application";
import {
  APPLICATION_STATUSES,
  APPLICATION_STATUS_LABEL,
  TIER_INTEREST_LABEL,
  contributionRateKobo,
  type ApplicationStatus,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";

const PAGE_SIZE = 25;

export const metadata = { title: "Applications" };

const STATUS_TONE: Record<ApplicationStatus, "ok" | "warn" | "alert" | "neutral"> = {
  new: "warn",
  reviewing: "neutral",
  approved: "ok",
  declined: "alert",
};

export default async function ApplicationsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; page?: string }>;
}) {
  await requirePermission("applications:read");
  const params = await searchParams;

  const status = APPLICATION_STATUSES.includes(params.status as ApplicationStatus)
    ? (params.status as ApplicationStatus)
    : "";
  const page = Math.max(1, Number(params.page) || 1);

  await connectDb();

  const filter: QueryFilter<ApplicationDoc> = {};
  if (status) filter.status = status;

  const [applications, total, newCount] = await Promise.all([
    Application.find(filter)
      .sort({ createdAt: -1 })
      .skip((page - 1) * PAGE_SIZE)
      .limit(PAGE_SIZE)
      .lean(),
    Application.countDocuments(filter),
    Application.countDocuments({ status: "new" }),
  ]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <>
      <PageHeader
        title="Registrations of interest"
        description={
          newCount > 0
            ? `${newCount} awaiting review. Approving one seeds a pending member record from the application.`
            : "Applications submitted through the public site."
        }
      />

      <form
        method="GET"
        action="/admin/applications"
        className="mb-8 flex flex-wrap items-end gap-4 border-b border-rule pb-8"
      >
        <div className="w-full sm:w-64">
          <label htmlFor="status" className="label-sm block text-ink-soft">
            Status
          </label>
          <Select id="status" name="status" defaultValue={status} className="mt-2">
            <option value="">All statuses</option>
            {APPLICATION_STATUSES.map((value) => (
              <option key={value} value={value}>
                {APPLICATION_STATUS_LABEL[value]}
              </option>
            ))}
          </Select>
        </div>
        <button
          type="submit"
          className="label border border-navy-900/25 px-5 py-3 text-navy-900 transition-colors hover:bg-navy-900/5"
        >
          Apply
        </button>
      </form>

      {applications.length === 0 ? (
        <EmptyState
          title={status ? "No matching applications" : "No applications yet"}
          body={
            status
              ? "Nothing is at this status right now."
              : "Applications submitted through the public form will appear here, newest first."
          }
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Applicant</Th>
                <Th>Interest</Th>
                <Th align="right">Monthly</Th>
                <Th>Status</Th>
                <Th>Receipt</Th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={String(application._id)}>
                  <Td>
                    <span className="tnum">
                      {application.createdAt.toLocaleDateString("en-NG", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="label-sm mt-1 block text-ink-faint">
                      {application.reference}
                    </span>
                  </Td>
                  <Td>
                    <Link
                      href={`/admin/applications/${String(application._id)}`}
                      className="text-navy-900 underline-offset-4 hover:underline"
                    >
                      {application.firstName} {application.lastName}
                    </Link>
                    <span className="label-sm mt-1 block break-all text-ink-faint">
                      {application.email}
                    </span>
                  </Td>
                  <Td>
                    <span className="text-[0.875rem]">
                      {TIER_INTEREST_LABEL[application.tierInterest].split(" — ")[0]}
                    </span>
                  </Td>
                  <Td align="right">
                    <span className="tnum">
                      {formatNaira(
                        contributionRateKobo(
                          application.tierInterest,
                          application.customContributionKobo,
                        ),
                      )}
                    </span>
                  </Td>
                  <Td>
                    <Badge tone={STATUS_TONE[application.status]}>
                      {APPLICATION_STATUS_LABEL[application.status]}
                    </Badge>
                  </Td>
                  <Td>
                    {application.applicantMail === "sent" ? (
                      <span className="label-sm text-ok">Sent</span>
                    ) : application.applicantMail === "failed" ? (
                      <span className="label-sm text-alert">Failed</span>
                    ) : (
                      <span className="label-sm text-ink-faint">
                        {application.applicantMail}
                      </span>
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
                    href={`/admin/applications?${new URLSearchParams({ ...(status ? { status } : {}), page: String(page - 1) })}`}
                    className="label-sm border border-navy-900/25 px-4 py-2.5 text-navy-900 hover:bg-navy-900/5"
                  >
                    Previous
                  </Link>
                ) : null}
                {page < pageCount ? (
                  <Link
                    href={`/admin/applications?${new URLSearchParams({ ...(status ? { status } : {}), page: String(page + 1) })}`}
                    className="label-sm border border-navy-900/25 px-4 py-2.5 text-navy-900 hover:bg-navy-900/5"
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
