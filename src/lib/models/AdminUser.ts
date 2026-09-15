import { Schema, model, models, type Model, type Types } from "mongoose";
import { ROLES, type Role } from "@/lib/rbac";

export type AdminUserDoc = {
  _id: Types.ObjectId;
  name: string;
  email: string;
  passwordHash: string;
  role: Role;
  active: boolean;
  lastLoginAt?: Date;
  createdAt: Date;
  updatedAt: Date;
};

const AdminUserSchema = new Schema<AdminUserDoc>(
  {
    name: { type: String, required: true, trim: true },
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    passwordHash: { type: String, required: true },
    role: { type: String, required: true, enum: ROLES, default: "viewer" },
    active: { type: Boolean, required: true, default: true },
    lastLoginAt: { type: Date },
  },
  { timestamps: true },
);

export const AdminUser: Model<AdminUserDoc> =
  (models.AdminUser as Model<AdminUserDoc>) ??
  model<AdminUserDoc>("AdminUser", AdminUserSchema);
