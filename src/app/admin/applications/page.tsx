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
import { Enquiry, type EnquiryDoc } from "@/lib/models/Enquiry";
import {
  ENQUIRY_STATUSES,
  ENQUIRY_STATUS_LABEL,
  SLOT_PRICE_KOBO,
  TIER_INTEREST_LABEL,
  type EnquiryStatus,
} from "@/lib/constants";
import { formatNaira, formatNumber } from "@/lib/money";

const PAGE_SIZE = 25;

export const metadata = { title: "Enquiries" };

const STATUS_TONE: Record<EnquiryStatus, "ok" | "warn" | "alert" | "neutral"> = {
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
  await requirePermission("enquiries:read");
  const params = await searchParams;

  const status = ENQUIRY_STATUSES.includes(params.status as EnquiryStatus)
    ? (params.status as EnquiryStatus)
    : "";
  const page = Math.max(1, Number(params.page) || 1);

  await connectDb();

  const filter: QueryFilter<EnquiryDoc> = {};
  if (status) filter.status = status;

  const [enquiries, total, newCount] = await Promise.all([
    Enquiry.find(filter)
      .sort({ createdAt: -1 })
      .skip((page - 1) * PAGE_SIZE)
      .limit(PAGE_SIZE)
      .lean(),
    Enquiry.countDocuments(filter),
    Enquiry.countDocuments({ status: "new" }),
  ]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <>
      <PageHeader
        title="Registrations of interest"
        description={
          newCount > 0
            ? `${newCount} awaiting review. Approving one seeds a pending member record from the enquiry.`
            : "Enquiries submitted through the public site."
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
            {ENQUIRY_STATUSES.map((value) => (
              <option key={value} value={value}>
                {ENQUIRY_STATUS_LABEL[value]}
              </option>
            ))}
          </Select>
        </div>
        <button
          type="submit"
          className="label border border-forest-900/25 px-5 py-3 text-forest-900 transition-colors hover:bg-forest-900/5"
        >
          Apply
        </button>
      </form>

      {enquiries.length === 0 ? (
        <EmptyState
          title={status ? "No matching enquiries" : "No enquiries yet"}
          body={
            status
              ? "Nothing is at this status right now."
              : "Enquiries submitted through the public form will appear here, newest first."
          }
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Received</Th>
                <Th>Enquirer</Th>
                <Th>Interest</Th>
                <Th align="right">Slots</Th>
                <Th>Status</Th>
                <Th>Receipt</Th>
              </tr>
            </thead>
            <tbody>
              {enquiries.map((enquiry) => (
                <tr key={String(enquiry._id)}>
                  <Td>
                    <span className="tnum">
                      {enquiry.createdAt.toLocaleDateString("en-NG", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="label-sm mt-1 block text-ink-faint">
                      {enquiry.reference}
                    </span>
                  </Td>
                  <Td>
                    <Link
                      href={`/admin/applications/${String(enquiry._id)}`}
                      className="text-forest-900 underline-offset-4 hover:underline"
                    >
                      {enquiry.firstName} {enquiry.lastName}
                    </Link>
                    <span className="label-sm mt-1 block break-all text-ink-faint">
                      {enquiry.email}
                    </span>
                  </Td>
                  <Td>
                    <span className="text-[0.875rem]">
                      {TIER_INTEREST_LABEL[enquiry.tierInterest].split(" — ")[0]}
                    </span>
                  </Td>
                  <Td align="right">
                    {enquiry.slotsInterest ? (
                      <>
                        <span className="tnum">
                          {formatNumber(enquiry.slotsInterest)}
                        </span>
                        <span className="label-sm mt-1 block text-ink-faint">
                          {formatNaira(enquiry.slotsInterest * SLOT_PRICE_KOBO)}
                        </span>
                      </>
                    ) : (
                      <span className="text-ink-faint">—</span>
                    )}
                  </Td>
                  <Td>
                    <Badge tone={STATUS_TONE[enquiry.status]}>
                      {ENQUIRY_STATUS_LABEL[enquiry.status]}
                    </Badge>
                  </Td>
                  <Td>
                    {enquiry.applicantMail === "sent" ? (
                      <span className="label-sm text-ok">Sent</span>
                    ) : enquiry.applicantMail === "failed" ? (
                      <span className="label-sm text-alert">Failed</span>
                    ) : (
                      <span className="label-sm text-ink-faint">
                        {enquiry.applicantMail}
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
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Previous
                  </Link>
                ) : null}
                {page < pageCount ? (
                  <Link
                    href={`/admin/applications?${new URLSearchParams({ ...(status ? { status } : {}), page: String(page + 1) })}`}
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
