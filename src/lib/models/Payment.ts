import { Schema, model, models, type Model, type Types } from "mongoose";
import {
  BANKS,
  PAYMENT_KINDS,
  PAYMENT_METHODS,
  type Bank,
  type PaymentKind,
  type PaymentMethod,
} from "@/lib/constants";

export type PaymentDoc = {
  _id: Types.ObjectId;
  member: Types.ObjectId;
  kind: PaymentKind;
  /** Integer kobo. Never a float. */
  amountKobo: number;
  /** "YYYY-MM" — required for dues, absent otherwise. */
  duesPeriod?: string;
  method: PaymentMethod;
  bank?: Bank;
  reference?: string;
  receivedOn: Date;
  note?: string;
  recordedBy: Types.ObjectId;
  recordedByName: string;
  createdAt: Date;
  updatedAt: Date;
};

const PaymentSchema = new Schema<PaymentDoc>(
  {
    member: {
      type: Schema.Types.ObjectId,
      ref: "Member",
      required: true,
      index: true,
    },
    kind: { type: String, required: true, enum: PAYMENT_KINDS },
    amountKobo: {
      type: Number,
      required: true,
      min: 1,
      validate: {
        validator: Number.isInteger,
        message: "Amount must be a whole number of kobo.",
      },
    },
    duesPeriod: {
      type: String,
      match: /^\d{4}-(0[1-9]|1[0-2])$/,
    },
    method: { type: String, required: true, enum: PAYMENT_METHODS },
    bank: { type: String, enum: BANKS },
    reference: { type: String, trim: true },
    receivedOn: { type: Date, required: true },
    note: { type: String, trim: true },
    recordedBy: {
      type: Schema.Types.ObjectId,
      ref: "AdminUser",
      required: true,
    },
    // Denormalised so the ledger renders without a second lookup, and so the
    // record still names its author if the admin account is later removed.
    recordedByName: { type: String, required: true },
  },
  { timestamps: true },
);

PaymentSchema.index({ receivedOn: -1 });
PaymentSchema.index({ member: 1, receivedOn: -1 });

/**
 * One dues payment per member per month. Enforced by the database rather than
 * by a read-then-write check, so a double submission cannot create a duplicate.
 */
PaymentSchema.index(
  { member: 1, duesPeriod: 1 },
  {
    unique: true,
    partialFilterExpression: {
      kind: "dues",
      duesPeriod: { $type: "string" },
    },
  },
);

export const Payment: Model<PaymentDoc> =
  (models.Payment as Model<PaymentDoc>) ??
  model<PaymentDoc>("Payment", PaymentSchema);
