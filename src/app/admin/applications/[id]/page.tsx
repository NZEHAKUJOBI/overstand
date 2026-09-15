import Link from "next/link";
import { notFound } from "next/navigation";
import { isValidObjectId } from "mongoose";
import {
  Badge,
  ButtonLink,
  DescriptionItem,
  DescriptionList,
  Notice,
  PageHeader,
} from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { connectDb } from "@/lib/db";
import { Enquiry } from "@/lib/models/Enquiry";
import {
  ENQUIRY_STATUS_LABEL,
  SLOT_PRICE_KOBO,
  TIER_INTEREST_LABEL,
  type EnquiryStatus,
} from "@/lib/constants";
import { formatNaira, formatNumber } from "@/lib/money";
import { ReviewForm } from "../ReviewForm";

const STATUS_TONE: Record<EnquiryStatus, "ok" | "warn" | "alert" | "neutral"> = {
  new: "warn",
  reviewing: "neutral",
  approved: "ok",
  declined: "alert",
};

const dateFormat: Intl.DateTimeFormatOptions = {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
};

export default async function EnquiryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requirePermission("enquiries:read");
  const { id } = await params;

  if (!isValidObjectId(id)) notFound();

  await connectDb();
  const enquiry = await Enquiry.findById(id).lean();
  if (!enquiry) notFound();

  return (
    <>
      <PageHeader
        title={`${enquiry.firstName} ${enquiry.lastName}`}
        description={`${enquiry.reference} · received ${enquiry.createdAt.toLocaleDateString("en-NG", dateFormat)}`}
        action={
          enquiry.member ? (
            <ButtonLink href={`/admin/members/${String(enquiry.member)}`} variant="ghost">
              View Member Record
            </ButtonLink>
          ) : undefined
        }
      />

      {enquiry.applicantMail === "failed" ? (
        <div className="mb-8">
          <Notice tone="error">
            The confirmation email to the applicant could not be sent
            {enquiry.mailError ? `: ${enquiry.mailError}` : "."} Contact them by
            phone, and check the SMTP settings.
          </Notice>
        </div>
      ) : enquiry.applicantMail === "skipped" ? (
        <div className="mb-8">
          <Notice tone="info">
            No confirmation was sent — SMTP is not configured on this server.
          </Notice>
        </div>
      ) : null}

      <div className="grid gap-12 xl:grid-cols-12 xl:gap-14">
        <div className="xl:col-span-7">
          <h2 className="font-display mb-5 text-[1.25rem] text-forest-900">
            Enquiry
          </h2>

          <DescriptionList>
            <DescriptionItem term="Status">
              <Badge tone={STATUS_TONE[enquiry.status]}>
                {ENQUIRY_STATUS_LABEL[enquiry.status]}
              </Badge>
            </DescriptionItem>
            <DescriptionItem term="Interest">
              {TIER_INTEREST_LABEL[enquiry.tierInterest]}
            </DescriptionItem>
            <DescriptionItem term="Email">
              <a
                href={`mailto:${enquiry.email}`}
                className="break-all underline-offset-4 hover:underline"
              >
                {enquiry.email}
              </a>
            </DescriptionItem>
            <DescriptionItem term="Phone">
              <a
                href={`tel:${enquiry.phone.replace(/\s/g, "")}`}
                className="tnum underline-offset-4 hover:underline"
              >
                {enquiry.phone}
              </a>
            </DescriptionItem>
            {enquiry.slotsInterest ? (
              <DescriptionItem term="Slots of interest">
                <span className="tnum">
                  {formatNumber(enquiry.slotsInterest)}
                </span>{" "}
                — {formatNaira(enquiry.slotsInterest * SLOT_PRICE_KOBO)}
              </DescriptionItem>
            ) : null}
            {enquiry.occupation ? (
              <DescriptionItem term="Occupation">
                {enquiry.occupation}
              </DescriptionItem>
            ) : null}
            {enquiry.address ? (
              <DescriptionItem term="Address">{enquiry.address}</DescriptionItem>
            ) : null}
            {enquiry.heardFrom ? (
              <DescriptionItem term="Heard about us via">
                {enquiry.heardFrom}
              </DescriptionItem>
            ) : null}
          </DescriptionList>

          {enquiry.message ? (
            <div className="mt-8">
              <h3 className="label-sm text-ink-faint">Message</h3>
              <p className="mt-3 border-l-2 border-gold-600 pl-5 text-[0.9375rem] leading-relaxed whitespace-pre-wrap text-ink">
                {enquiry.message}
              </p>
            </div>
          ) : null}

          {enquiry.reviewedAt ? (
            <div className="mt-8 border-t border-rule pt-6">
              <h3 className="label-sm text-ink-faint">Review</h3>
              <p className="mt-3 text-[0.9375rem] text-ink-soft">
                {ENQUIRY_STATUS_LABEL[enquiry.status]} by{" "}
                {enquiry.reviewedByName ?? "an officer"} on{" "}
                {enquiry.reviewedAt.toLocaleDateString("en-NG", dateFormat)}.
              </p>
              {enquiry.reviewNote ? (
                <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink">
                  {enquiry.reviewNote}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="xl:col-span-5">
          {can(session.role, "enquiries:write") ? (
            <>
              <h2 className="font-display mb-5 text-[1.25rem] text-forest-900">
                Record a decision
              </h2>
              <ReviewForm
                enquiryId={id}
                currentStatus={enquiry.status}
                alreadyLinked={Boolean(enquiry.member)}
              />
            </>
          ) : (
            <Notice tone="info">
              Your role can read enquiries but not act on them.
            </Notice>
          )}
        </div>
      </div>

      <p className="mt-12">
        <Link
          href="/admin/applications"
          className="label-sm text-ink-soft underline-offset-4 hover:underline"
        >
          ← Back to enquiries
        </Link>
      </p>
    </>
  );
}
