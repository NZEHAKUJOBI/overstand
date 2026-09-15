import { Schema, model, models, type Model, type Types } from "mongoose";
import {
  MAX_INVESTOR_SLOTS,
  MEMBER_STATUSES,
  MEMBER_TIERS,
  type MemberStatus,
  type MemberTier,
} from "@/lib/constants";

export type MemberDoc = {
  _id: Types.ObjectId;
  membershipNumber: string;
  firstName: string;
  lastName: string;
  otherNames?: string;
  email: string;
  phone: string;
  address?: string;
  tier: MemberTier;
  /** Ownership slots held. Always 0 for non-investor members. */
  slots: number;
  status: MemberStatus;
  /** First month for which monthly dues are owed. */
  joinedOn: Date;
  notes?: string;
  createdBy?: Types.ObjectId;
  updatedBy?: Types.ObjectId;
  createdAt: Date;
  updatedAt: Date;
};

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
    tier: { type: String, required: true, enum: MEMBER_TIERS },
    slots: {
      type: Number,
      required: true,
      default: 0,
      min: 0,
      max: MAX_INVESTOR_SLOTS,
      validate: {
        validator: Number.isInteger,
        message: "Slots must be a whole number.",
      },
    },
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
