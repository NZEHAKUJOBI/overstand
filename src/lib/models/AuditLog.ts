import { Schema, model, models, type Model, type Types } from "mongoose";

export type AuditLogDoc = {
  _id: Types.ObjectId;
  actor: Types.ObjectId;
  actorName: string;
  actorRole: string;
  action: string;
  entity: "member" | "payment" | "admin_user";
  entityId?: string;
  summary: string;
  createdAt: Date;
};

const AuditLogSchema = new Schema<AuditLogDoc>(
  {
    actor: { type: Schema.Types.ObjectId, ref: "AdminUser", required: true },
    actorName: { type: String, required: true },
    actorRole: { type: String, required: true },
    action: { type: String, required: true },
    entity: {
      type: String,
      required: true,
      enum: ["member", "payment", "admin_user"],
    },
    entityId: { type: String },
    summary: { type: String, required: true },
  },
  { timestamps: { createdAt: true, updatedAt: false } },
);

AuditLogSchema.index({ createdAt: -1 });

export const AuditLog: Model<AuditLogDoc> =
  (models.AuditLog as Model<AuditLogDoc>) ??
  model<AuditLogDoc>("AuditLog", AuditLogSchema);

/**
 * Best-effort audit trail. A logging failure must never roll back or block the
 * business write that succeeded, so this swallows its own errors.
 */
export async function recordAudit(entry: {
  actor: Types.ObjectId;
  actorName: string;
  actorRole: string;
  action: string;
  entity: AuditLogDoc["entity"];
  entityId?: string;
  summary: string;
}): Promise<void> {
  try {
    await AuditLog.create(entry);
  } catch (error) {
    console.error("[audit] failed to write entry", error);
  }
}
