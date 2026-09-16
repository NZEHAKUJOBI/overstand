import { Schema, model, models, type Model, type Types } from "mongoose";
import { Counter } from "./Counter";
import {
  APPLICATION_STATUSES,
  MAX_CONTRIBUTION_KOBO,
  TIER_INTERESTS,
  type ApplicationStatus,
  type TierInterest,
} from "../constants";

/**
 * A membership application from the public site.
 *
 * It starts an application; it does not admit anybody and takes no payment.
 * The Society issues the Membership/Entrance Form from its office and collects
 * the ₦20,000 application fee there, so this record is what the Secretariat
 * works from between the two. Approving one seeds a Member with status
 * "pending".
 */

export type MailState = "pending" | "sent" | "failed" | "skipped";

export type ApplicantNextOfKin = {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
  address?: string;
};

export type ApplicationDoc = {
  _id: Types.ObjectId;
  reference: string;
  firstName: string;
  lastName: string;
  otherNames?: string;
  email: string;
  phone: string;
  address?: string;
  dateOfBirth?: Date;
  occupation?: string;
  nextOfKin: ApplicantNextOfKin;
  tierInterest: TierInterest;
  /** Proposed monthly contribution, for applicants above Tier 2. */
  customContributionKobo?: number | null;
  /** The applicant's own confirmation of the Society's eligibility criteria. */
  eligibilityConfirmed: boolean;
  heardFrom?: string;
  message?: string;
  status: ApplicationStatus;
  reviewNote?: string;
  reviewedBy?: Types.ObjectId;
  reviewedByName?: string;
  reviewedAt?: Date;
  /** Set once an approval has seeded a member record. */
  member?: Types.ObjectId;
  submittedIp?: string;
  applicantMail: MailState;
  secretariatMail: MailState;
  mailError?: string;
  createdAt: Date;
  updatedAt: Date;
};

const NextOfKinSchema = new Schema<ApplicantNextOfKin>(
  {
    name: { type: String, required: true, trim: true },
    relationship: { type: String, required: true, trim: true },
    phone: { type: String, required: true, trim: true },
    email: { type: String, lowercase: true, trim: true },
    address: { type: String, trim: true },
  },
  { _id: false },
);

const ApplicationSchema = new Schema<ApplicationDoc>(
  {
    reference: { type: String, required: true, unique: true },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    otherNames: { type: String, trim: true },
    email: { type: String, required: true, lowercase: true, trim: true },
    phone: { type: String, required: true, trim: true },
    address: { type: String, trim: true },
    dateOfBirth: { type: Date },
    occupation: { type: String, trim: true },
    nextOfKin: { type: NextOfKinSchema, required: true },
    tierInterest: { type: String, required: true, enum: TIER_INTERESTS },
    customContributionKobo: {
      type: Number,
      default: null,
      min: 0,
      max: MAX_CONTRIBUTION_KOBO,
    },
    eligibilityConfirmed: { type: Boolean, required: true, default: false },
    heardFrom: { type: String, trim: true },
    message: { type: String, trim: true },
    status: {
      type: String,
      required: true,
      enum: APPLICATION_STATUSES,
      default: "new",
    },
    reviewNote: { type: String, trim: true },
    reviewedBy: { type: Schema.Types.ObjectId, ref: "AdminUser" },
    reviewedByName: { type: String },
    reviewedAt: { type: Date },
    member: { type: Schema.Types.ObjectId, ref: "Member" },
    submittedIp: { type: String },
    applicantMail: { type: String, required: true, default: "pending" },
    secretariatMail: { type: String, required: true, default: "pending" },
    mailError: { type: String },
  },
  { timestamps: true },
);

ApplicationSchema.index({ createdAt: -1 });
ApplicationSchema.index({ status: 1, createdAt: -1 });
// Supports the duplicate-submission window without a full collection scan.
ApplicationSchema.index({ email: 1, createdAt: -1 });

export const Application: Model<ApplicationDoc> =
  (models.Application as Model<ApplicationDoc>) ??
  model<ApplicationDoc>("Application", ApplicationSchema);

/** Atomic reference allocation, same approach as membership numbers. */
export async function nextApplicationReference(year: number): Promise<string> {
  const counter = await Counter.findByIdAndUpdate(
    `application:${year}`,
    { $inc: { seq: 1 } },
    { returnDocument: "after", upsert: true },
  ).lean();

  return `OMCS-APP-${year}-${String(counter?.seq ?? 1).padStart(4, "0")}`;
}
