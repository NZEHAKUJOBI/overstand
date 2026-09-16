import { connectDb } from "./db";
import { Member } from "./models/Member";
import { Payment } from "./models/Payment";
import { computeContribution } from "./contributions";
import {
  MEMBER_TIERS,
  type MemberStatus,
  type MemberTier,
} from "./constants";

/** Contribution paid to date, keyed by member id. */
export async function contributionPaidByMember(
  memberIds?: string[],
): Promise<Map<string, number>> {
  const match: Record<string, unknown> = { kind: "contribution" };

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
  membersByTier: Record<MemberTier, number>;
  totalMembers: number;
  activeMembers: number;
  /**
   * What the accruing membership is committed to contribute each month, at
   * each member's own rate. This is the Society's expected monthly book — the
   * figure everything else is measured against.
   */
  monthlyCommitmentKobo: number;
  receivedTotalKobo: number;
  applicationReceivedKobo: number;
  registrationReceivedKobo: number;
  annualReceivedKobo: number;
  contributionReceivedKobo: number;
  contributionThisMonthKobo: number;
  /** This month's contributions as a share of the monthly commitment. */
  collectionPercent: number;
  totalArrearsKobo: number;
  membersInArrears: number;
};

export async function getOverview(): Promise<Overview> {
  await connectDb();

  const [statusRows, tierRows, paymentRows, monthContributionRow] =
    await Promise.all([
      Member.aggregate<{ _id: MemberStatus; count: number }>([
        { $group: { _id: "$status", count: { $sum: 1 } } },
      ]),
      Member.aggregate<{ _id: MemberTier; count: number }>([
        { $group: { _id: "$tier", count: { $sum: 1 } } },
      ]),
      Payment.aggregate<{ _id: string; total: number }>([
        { $group: { _id: "$kind", total: { $sum: "$amountKobo" } } },
      ]),
      Payment.aggregate<{ total: number }>([
        {
          $match: {
            kind: "contribution",
            contributionPeriod: currentMonthKey(),
          },
        },
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

  const membersByTier = Object.fromEntries(
    MEMBER_TIERS.map((tier) => [tier, 0]),
  ) as Record<MemberTier, number>;
  for (const row of tierRows) membersByTier[row._id] = row.count;

  const byKind = new Map(paymentRows.map((row) => [row._id, row.total]));

  const accruing = await Member.find({
    status: { $in: ["active", "suspended"] },
  })
    .select("tier status joinedOn customContributionKobo")
    .lean();

  const contributionPaid = await contributionPaidByMember();

  let totalArrearsKobo = 0;
  let membersInArrears = 0;
  let monthlyCommitmentKobo = 0;

  for (const member of accruing) {
    const position = computeContribution(
      member,
      contributionPaid.get(String(member._id)) ?? 0,
    );

    monthlyCommitmentKobo += position.rateKobo;

    if (position.arrearsKobo > 0) {
      totalArrearsKobo += position.arrearsKobo;
      membersInArrears += 1;
    }
  }

  const receivedTotalKobo = paymentRows.reduce((sum, row) => sum + row.total, 0);
  const activeMembers = membersByStatus.active;
  const totalMembers = statusRows.reduce((sum, row) => sum + row.count, 0);
  const contributionThisMonthKobo = monthContributionRow[0]?.total ?? 0;

  return {
    membersByStatus,
    membersByTier,
    totalMembers,
    activeMembers,
    monthlyCommitmentKobo,
    receivedTotalKobo,
    applicationReceivedKobo: byKind.get("application") ?? 0,
    registrationReceivedKobo: byKind.get("registration") ?? 0,
    annualReceivedKobo: byKind.get("annual") ?? 0,
    contributionReceivedKobo: byKind.get("contribution") ?? 0,
    contributionThisMonthKobo,
    collectionPercent:
      monthlyCommitmentKobo > 0
        ? (contributionThisMonthKobo / monthlyCommitmentKobo) * 100
        : 0,
    totalArrearsKobo,
    membersInArrears,
  };
}

function currentMonthKey(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
}
