import { Schema, model, models, type Model, type Types } from "mongoose";
import { Counter } from "./Counter";
import {
  ENQUIRY_STATUSES,
  TIER_INTERESTS,
  type EnquiryStatus,
  type TierInterest,
} from "../constants";

/**
 * A registration of interest from the public site.
 *
 * Deliberately NOT a membership application: the Board has not adopted
 * eligibility criteria or forms, so this records an enquiry and nothing more.
 * Approving one seeds a Member record with status "pending"; it does not
 * admit anybody.
 */

export type MailState = "pending" | "sent" | "failed" | "skipped";

export type EnquiryDoc = {
  _id: Types.ObjectId;
  reference: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address?: string;
  occupation?: string;
  tierInterest: TierInterest;
  slotsInterest?: number;
  heardFrom?: string;
  message?: string;
  status: EnquiryStatus;
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

const EnquirySchema = new Schema<EnquiryDoc>(
  {
    reference: { type: String, required: true, unique: true },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    email: { type: String, required: true, lowercase: true, trim: true },
    phone: { type: String, required: true, trim: true },
    address: { type: String, trim: true },
    occupation: { type: String, trim: true },
    tierInterest: { type: String, required: true, enum: TIER_INTERESTS },
    slotsInterest: { type: Number, min: 0 },
    heardFrom: { type: String, trim: true },
    message: { type: String, trim: true },
    status: {
      type: String,
      required: true,
      enum: ENQUIRY_STATUSES,
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

EnquirySchema.index({ createdAt: -1 });
EnquirySchema.index({ status: 1, createdAt: -1 });
// Supports the duplicate-submission window without a full collection scan.
EnquirySchema.index({ email: 1, createdAt: -1 });

export const Enquiry: Model<EnquiryDoc> =
  (models.Enquiry as Model<EnquiryDoc>) ??
  model<EnquiryDoc>("Enquiry", EnquirySchema);

/** Atomic reference allocation, same approach as membership numbers. */
export async function nextEnquiryReference(year: number): Promise<string> {
  const counter = await Counter.findByIdAndUpdate(
    `enquiry:${year}`,
    { $inc: { seq: 1 } },
    { returnDocument: "after", upsert: true },
  ).lean();

  return `ARG-INT-${year}-${String(counter?.seq ?? 1).padStart(4, "0")}`;
}
