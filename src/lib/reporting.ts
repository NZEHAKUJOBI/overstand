import { connectDb } from "./db";
import { Member } from "./models/Member";
import { Payment } from "./models/Payment";
import { computeDues } from "./dues";
import {
  CAPITAL_TARGET_KOBO,
  MEMBERSHIP_TARGET,
  SLOT_PRICE_KOBO,
  TOTAL_SLOT_POOL,
  type MemberStatus,
  type MemberTier,
} from "./constants";

/** Dues paid to date, keyed by member id. */
export async function duesPaidByMember(
  memberIds?: string[],
): Promise<Map<string, number>> {
  const match: Record<string, unknown> = { kind: "dues" };

  if (memberIds) {
    const { Types } = await import("mongoose");
    match.member = { $in: memberIds.map((id) => new Types.ObjectId(id)) };
  }

  const rows = await Payment.aggregate<{ _id: unknown; paid: number }>([
    { $match: match },
    { $group: { _id: "$member", paid: { $sum: "$amountKobo" } } },
  ]);

  return new Map(rows.map((row) => [String(row._id), row.paid]));
}

export type Overview = {
  membersByStatus: Record<MemberStatus, number>;
  totalMembers: number;
  activeMembers: number;
  investorCount: number;
  nonInvestorCount: number;
  slotsAllocated: number;
  slotValueKobo: number;
  receivedTotalKobo: number;
  registrationReceivedKobo: number;
  duesReceivedKobo: number;
  duesThisMonthKobo: number;
  totalArrearsKobo: number;
  membersInArrears: number;
  slotPoolPercent: number;
  capitalPercent: number;
  membershipPercent: number;
};

export async function getOverview(): Promise<Overview> {
  await connectDb();

  const [statusRows, tierRows, slotRow, paymentRows, monthDuesRow] =
    await Promise.all([
      Member.aggregate<{ _id: MemberStatus; count: number }>([
        { $group: { _id: "$status", count: { $sum: 1 } } },
      ]),
      Member.aggregate<{ _id: MemberTier; count: number }>([
        { $group: { _id: "$tier", count: { $sum: 1 } } },
      ]),
      // Only admitted members' slots count against the pool.
      Member.aggregate<{ slots: number }>([
        { $match: { status: { $in: ["active", "suspended"] } } },
        { $group: { _id: null, slots: { $sum: "$slots" } } },
      ]),
      Payment.aggregate<{ _id: string; total: number }>([
        { $group: { _id: "$kind", total: { $sum: "$amountKobo" } } },
      ]),
      Payment.aggregate<{ total: number }>([
        { $match: { kind: "dues", duesPeriod: currentMonthKey() } },
        { $group: { _id: null, total: { $sum: "$amountKobo" } } },
      ]),
    ]);

  const membersByStatus: Record<MemberStatus, number> = {
    pending: 0,
    active: 0,
    suspended: 0,
    exited: 0,
  };
  for (const row of statusRows) membersByStatus[row._id] = row.count;

  const byKind = new Map(paymentRows.map((row) => [row._id, row.total]));

  const accruing = await Member.find({
    status: { $in: ["active", "suspended"] },
  })
    .select("tier status joinedOn")
    .lean();

  const duesPaid = await duesPaidByMember();

  let totalArrearsKobo = 0;
  let membersInArrears = 0;

  for (const member of accruing) {
    const position = computeDues(
      { tier: member.tier, status: member.status, joinedOn: member.joinedOn },
      duesPaid.get(String(member._id)) ?? 0,
    );

    if (position.arrearsKobo > 0) {
      totalArrearsKobo += position.arrearsKobo;
      membersInArrears += 1;
    }
  }

  const slotsAllocated = slotRow[0]?.slots ?? 0;
  const slotValueKobo = slotsAllocated * SLOT_PRICE_KOBO;

  const receivedTotalKobo = paymentRows.reduce((sum, row) => sum + row.total, 0);
  const activeMembers = membersByStatus.active;
  const totalMembers = statusRows.reduce((sum, row) => sum + row.count, 0);

  const tierCounts = new Map(tierRows.map((row) => [row._id, row.count]));

  return {
    membersByStatus,
    totalMembers,
    activeMembers,
    investorCount: tierCounts.get("investor") ?? 0,
    nonInvestorCount: tierCounts.get("non_investor") ?? 0,
    slotsAllocated,
    slotValueKobo,
    receivedTotalKobo,
    registrationReceivedKobo: byKind.get("registration") ?? 0,
    duesReceivedKobo: byKind.get("dues") ?? 0,
    duesThisMonthKobo: monthDuesRow[0]?.total ?? 0,
    totalArrearsKobo,
    membersInArrears,
    slotPoolPercent: (slotsAllocated / TOTAL_SLOT_POOL) * 100,
    capitalPercent: (slotValueKobo / CAPITAL_TARGET_KOBO) * 100,
    membershipPercent: (activeMembers / MEMBERSHIP_TARGET) * 100,
  };
}

function currentMonthKey(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}

/** Slots already committed, for validating a new or amended holding. */
export async function slotsAllocatedExcluding(
  memberId?: string,
): Promise<number> {
  await connectDb();

  const match: Record<string, unknown> = {
    status: { $in: ["active", "suspended"] },
  };

  if (memberId) {
    const { Types } = await import("mongoose");
    match._id = { $ne: new Types.ObjectId(memberId) };
  }

  const rows = await Member.aggregate<{ slots: number }>([
    { $match: match },
    { $group: { _id: null, slots: { $sum: "$slots" } } },
  ]);

  return rows[0]?.slots ?? 0;
}

export { TOTAL_SLOT_POOL, MEMBERSHIP_TARGET, CAPITAL_TARGET_KOBO };
