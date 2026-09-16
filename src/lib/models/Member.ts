import { Schema, model, models, type Model, type Types } from "mongoose";
import {
  MAX_CONTRIBUTION_KOBO,
  MEMBER_STATUSES,
  MEMBER_TIERS,
  type MemberStatus,
  type MemberTier,
} from "@/lib/constants";

/**
 * Next of kin, which the Membership Application Form requires. Held as a
 * subdocument rather than flattened fields so it can be required as a unit.
 */
export type NextOfKin = {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
  address?: string;
};

export type MemberDoc = {
  _id: Types.ObjectId;
  membershipNumber: string;
  firstName: string;
  lastName: string;
  otherNames?: string;
  email: string;
  phone: string;
  address?: string;
  dateOfBirth?: Date;
  occupation?: string;
  tier: MemberTier;
  /**
   * Agreed monthly contribution for members above Tier 2. Null on the standard
   * tiers, whose rate comes from constants — storing it there too would let the
   * two drift apart.
   */
  customContributionKobo?: number | null;
  nextOfKin: NextOfKin;
  status: MemberStatus;
  /** First month for which a monthly contribution is owed. */
  joinedOn: Date;
  notes?: string;
  createdBy?: Types.ObjectId;
  updatedBy?: Types.ObjectId;
  createdAt: Date;
  updatedAt: Date;
};

const NextOfKinSchema = new Schema<NextOfKin>(
  {
    name: { type: String, required: true, trim: true },
    relationship: { type: String, required: true, trim: true },
    phone: { type: String, required: true, trim: true },
    email: { type: String, lowercase: true, trim: true },
    address: { type: String, trim: true },
  },
  { _id: false },
);

const MemberSchema = new Schema<MemberDoc>(
  {
    membershipNumber: { type: String, required: true, unique: true },
    firstName: { type: String, required: true, trim: true },
    lastName: { type: String, required: true, trim: true },
    otherNames: { type: String, trim: true },
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    phone: { type: String, required: true, trim: true },
    address: { type: String, trim: true },
    dateOfBirth: { type: Date },
    occupation: { type: String, trim: true },
    tier: { type: String, required: true, enum: MEMBER_TIERS },
    customContributionKobo: {
      type: Number,
      default: null,
      min: 0,
      max: MAX_CONTRIBUTION_KOBO,
      validate: {
        validator: (value: number | null) =>
          value === null || Number.isInteger(value),
        message: "Contribution must be a whole number of kobo.",
      },
    },
    nextOfKin: { type: NextOfKinSchema, required: true },
    status: {
      type: String,
      required: true,
      enum: MEMBER_STATUSES,
      default: "pending",
    },
    joinedOn: { type: Date, required: true },
    notes: { type: String, trim: true },
    createdBy: { type: Schema.Types.ObjectId, ref: "AdminUser" },
    updatedBy: { type: Schema.Types.ObjectId, ref: "AdminUser" },
  },
  { timestamps: true },
);

// Supports the register's default ordering and the status/tier filters.
MemberSchema.index({ lastName: 1, firstName: 1 });
MemberSchema.index({ status: 1, tier: 1 });

export const Member: Model<MemberDoc> =
  (models.Member as Model<MemberDoc>) ??
  model<MemberDoc>("Member", MemberSchema);
