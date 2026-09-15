import { Schema, model, models, type Model } from "mongoose";

export type CounterDoc = {
  _id: string;
  seq: number;
};

const CounterSchema = new Schema<CounterDoc>({
  _id: { type: String, required: true },
  seq: { type: Number, required: true, default: 0 },
});

export const Counter: Model<CounterDoc> =
  (models.Counter as Model<CounterDoc>) ??
  model<CounterDoc>("Counter", CounterSchema);

/**
 * Allocates the next membership number atomically.
 *
 * `$inc` inside `findOneAndUpdate` is a single-document atomic operation, so
 * two admins registering members at the same moment cannot receive the same
 * number. This is deliberately not a `count() + 1` read-then-write, and
 * deliberately not a transaction — it works on a standalone mongod as well as
 * on a replica set.
 */
export async function nextMembershipNumber(year: number): Promise<string> {
  const key = `member:${year}`;

  const counter = await Counter.findByIdAndUpdate(
    key,
    { $inc: { seq: 1 } },
    { returnDocument: "after", upsert: true },
  ).lean();

  const seq = counter?.seq ?? 1;
  return `ARG-${year}-${String(seq).padStart(4, "0")}`;
}
