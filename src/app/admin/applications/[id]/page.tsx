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
import { Application } from "@/lib/models/Application";
import {
  APPLICATION_STATUS_LABEL,
  TIER_INTEREST_LABEL,
  contributionRateKobo,
  type ApplicationStatus,
} from "@/lib/constants";
import { formatNaira } from "@/lib/money";
import { ReviewForm } from "../ReviewForm";

const STATUS_TONE: Record<ApplicationStatus, "ok" | "warn" | "alert" | "neutral"> = {
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

export default async function ApplicationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requirePermission("applications:read");
  const { id } = await params;

  if (!isValidObjectId(id)) notFound();

  await connectDb();
  const application = await Application.findById(id).lean();
  if (!application) notFound();

  return (
    <>
      <PageHeader
        title={`${application.firstName} ${application.lastName}`}
        description={`${application.reference} · received ${application.createdAt.toLocaleDateString("en-NG", dateFormat)}`}
        action={
          application.member ? (
            <ButtonLink href={`/admin/members/${String(application.member)}`} variant="ghost">
              View Member Record
            </ButtonLink>
          ) : undefined
        }
      />

      {application.applicantMail === "failed" ? (
        <div className="mb-8">
          <Notice tone="error">
            The confirmation email to the applicant could not be sent
            {application.mailError ? `: ${application.mailError}` : "."} Contact them by
            phone, and check the SMTP settings.
          </Notice>
        </div>
      ) : application.applicantMail === "skipped" ? (
        <div className="mb-8">
          <Notice tone="info">
            No confirmation was sent — SMTP is not configured on this server.
          </Notice>
        </div>
      ) : null}

      <div className="grid gap-12 xl:grid-cols-12 xl:gap-14">
        <div className="xl:col-span-7">
          <h2 className="font-display mb-5 text-[1.25rem] text-navy-900">
            Application
          </h2>

          <DescriptionList>
            <DescriptionItem term="Status">
              <Badge tone={STATUS_TONE[application.status]}>
                {APPLICATION_STATUS_LABEL[application.status]}
              </Badge>
            </DescriptionItem>
            <DescriptionItem term="Interest">
              {TIER_INTEREST_LABEL[application.tierInterest]}
            </DescriptionItem>
            <DescriptionItem term="Email">
              <a
                href={`mailto:${application.email}`}
                className="break-all underline-offset-4 hover:underline"
              >
                {application.email}
              </a>
            </DescriptionItem>
            <DescriptionItem term="Phone">
              <a
                href={`tel:${application.phone.replace(/\s/g, "")}`}
                className="tnum underline-offset-4 hover:underline"
              >
                {application.phone}
              </a>
            </DescriptionItem>
            <DescriptionItem term="Monthly contribution">
              <span className="tnum">
                {formatNaira(
                  contributionRateKobo(
                    application.tierInterest,
                    application.customContributionKobo,
                  ),
                )}
              </span>{" "}
              per month
            </DescriptionItem>
            {application.occupation ? (
              <DescriptionItem term="Occupation">
                {application.occupation}
              </DescriptionItem>
            ) : null}
            {application.address ? (
              <DescriptionItem term="Address">{application.address}</DescriptionItem>
            ) : null}
            {application.heardFrom ? (
              <DescriptionItem term="Heard about us via">
                {application.heardFrom}
              </DescriptionItem>
            ) : null}
          </DescriptionList>

          {application.message ? (
            <div className="mt-8">
              <h3 className="label-sm text-ink-faint">Message</h3>
              <p className="mt-3 border-l-2 border-gold-600 pl-5 text-[0.9375rem] leading-relaxed whitespace-pre-wrap text-ink">
                {application.message}
              </p>
            </div>
          ) : null}

          {application.reviewedAt ? (
            <div className="mt-8 border-t border-rule pt-6">
              <h3 className="label-sm text-ink-faint">Review</h3>
              <p className="mt-3 text-[0.9375rem] text-ink-soft">
                {APPLICATION_STATUS_LABEL[application.status]} by{" "}
                {application.reviewedByName ?? "an officer"} on{" "}
                {application.reviewedAt.toLocaleDateString("en-NG", dateFormat)}.
              </p>
              {application.reviewNote ? (
                <p className="mt-3 text-[0.9375rem] leading-relaxed text-ink">
                  {application.reviewNote}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="xl:col-span-5">
          {can(session.role, "applications:write") ? (
            <>
              <h2 className="font-display mb-5 text-[1.25rem] text-navy-900">
                Record a decision
              </h2>
              <ReviewForm
                applicationId={id}
                currentStatus={application.status}
                alreadyLinked={Boolean(application.member)}
              />
            </>
          ) : (
            <Notice tone="info">
              Your role can read applications but not act on them.
            </Notice>
          )}
        </div>
      </div>

      <p className="mt-12">
        <Link
          href="/admin/applications"
          className="label-sm text-ink-soft underline-offset-4 hover:underline"
        >
          ← Back to applications
        </Link>
      </p>
    </>
  );
}
