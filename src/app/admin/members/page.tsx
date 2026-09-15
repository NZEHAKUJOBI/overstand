import Link from "next/link";
import type { QueryFilter } from "mongoose";
import {
  Badge,
  ButtonLink,
  EmptyState,
  Input,
  PageHeader,
  Select,
  Table,
  Td,
  Th,
} from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { can } from "@/lib/rbac";
import { connectDb } from "@/lib/db";
import { Member, type MemberDoc } from "@/lib/models/Member";
import { computeDues } from "@/lib/dues";
import { duesPaidByMember } from "@/lib/reporting";
import {
  MEMBER_STATUSES,
  MEMBER_TIERS,
  SLOT_PRICE_KOBO,
  STATUS_LABEL,
  TIER_LABEL,
  type MemberStatus,
  type MemberTier,
} from "@/lib/constants";
import { formatNaira, formatNumber } from "@/lib/money";

const PAGE_SIZE = 20;

type MemberRow = Awaited<ReturnType<typeof fetchMembers>>[number];

const STATUS_TONE: Record<MemberStatus, "ok" | "warn" | "alert" | "neutral"> = {
  active: "ok",
  pending: "warn",
  suspended: "alert",
  exited: "neutral",
};

/** User input goes into a $regex, so metacharacters must be neutralised. */
function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

type Search = {
  q?: string;
  tier?: string;
  status?: string;
  arrears?: string;
  page?: string;
};

export default async function MembersPage({
  searchParams,
}: {
  searchParams: Promise<Search>;
}) {
  const session = await requirePermission("members:read");
  const params = await searchParams;

  const q = (params.q ?? "").trim();
  const tier = MEMBER_TIERS.includes(params.tier as MemberTier)
    ? (params.tier as MemberTier)
    : "";
  const status = MEMBER_STATUSES.includes(params.status as MemberStatus)
    ? (params.status as MemberStatus)
    : "";
  const arrearsOnly = params.arrears === "1";
  const page = Math.max(1, Number(params.page) || 1);

  await connectDb();

  const filter: QueryFilter<MemberDoc> = {};

  if (q) {
    const pattern = new RegExp(escapeRegex(q), "i");
    filter.$or = [
      { firstName: pattern },
      { lastName: pattern },
      { otherNames: pattern },
      { email: pattern },
      { phone: pattern },
      { membershipNumber: pattern },
    ];
  }
  if (tier) filter.tier = tier;
  if (status) filter.status = status;

  let rows: Array<{
    member: MemberRow;
    arrearsKobo: number;
    accruing: boolean;
  }>;
  let total: number;
  let members: MemberRow[];

  if (arrearsOnly) {
    // Arrears are derived, not stored, so this branch computes across the whole
    // accruing set and paginates in memory. Fine at the Society's scale; it
    // would need a materialised balance if the register grew by an order of
    // magnitude.
    filter.status = status || { $in: ["active", "suspended"] };
    members = await fetchMembers(filter);
    const duesPaid = await duesPaidByMember();

    const computed = members
      .map((member) => {
        const position = computeDues(
          { tier: member.tier, status: member.status, joinedOn: member.joinedOn },
          duesPaid.get(String(member._id)) ?? 0,
        );
        return {
          member,
          arrearsKobo: position.arrearsKobo,
          accruing: position.accruing,
        };
      })
      .filter((row) => row.arrearsKobo > 0)
      .sort((a, b) => b.arrearsKobo - a.arrearsKobo);

    total = computed.length;
    rows = computed.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  } else {
    [members, total] = await Promise.all([
      fetchMembers(filter, (page - 1) * PAGE_SIZE, PAGE_SIZE),
      Member.countDocuments(filter),
    ]);

    const duesPaid = await duesPaidByMember(members.map((m) => String(m._id)));

    rows = members.map((member) => {
      const position = computeDues(
        { tier: member.tier, status: member.status, joinedOn: member.joinedOn },
        duesPaid.get(String(member._id)) ?? 0,
      );
      return {
        member,
        arrearsKobo: position.arrearsKobo,
        accruing: position.accruing,
      };
    });
  }

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const queryFor = (overrides: Record<string, string>) => {
    const next = new URLSearchParams();
    if (q) next.set("q", q);
    if (tier) next.set("tier", tier);
    if (status) next.set("status", status);
    if (arrearsOnly) next.set("arrears", "1");
    for (const [key, value] of Object.entries(overrides)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    const string = next.toString();
    return string ? `/admin/members?${string}` : "/admin/members";
  };

  return (
    <>
      <PageHeader
        title="Members"
        description={`${formatNumber(total)} ${arrearsOnly ? "in arrears" : "on the register"}${
          q || tier || status ? " matching this filter" : ""
        }.`}
        action={
          can(session.role, "members:write") ? (
            <ButtonLink href="/admin/members/new" variant="gold">
              Register Member
            </ButtonLink>
          ) : undefined
        }
      />

      <form
        method="GET"
        action="/admin/members"
        className="mb-8 grid gap-4 border-b border-rule pb-8 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_auto]"
      >
        <div>
          <label htmlFor="q" className="label-sm block text-ink-soft">
            Search
          </label>
          <Input
            id="q"
            name="q"
            defaultValue={q}
            placeholder="Name, email, phone or membership number"
            className="mt-2"
          />
        </div>

        <div>
          <label htmlFor="tier" className="label-sm block text-ink-soft">
            Tier
          </label>
          <Select id="tier" name="tier" defaultValue={tier} className="mt-2">
            <option value="">All tiers</option>
            {MEMBER_TIERS.map((value) => (
              <option key={value} value={value}>
                {TIER_LABEL[value]}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="status" className="label-sm block text-ink-soft">
            Status
          </label>
          <Select id="status" name="status" defaultValue={status} className="mt-2">
            <option value="">All statuses</option>
            {MEMBER_STATUSES.map((value) => (
              <option key={value} value={value}>
                {STATUS_LABEL[value]}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex items-end gap-3">
          {arrearsOnly ? (
            <input type="hidden" name="arrears" value="1" />
          ) : null}
          <button
            type="submit"
            className="label border border-forest-900/25 px-5 py-3 text-forest-900 transition-colors hover:bg-forest-900/5"
          >
            Apply
          </button>
        </div>
      </form>

      <div className="mb-6 flex flex-wrap gap-x-6 gap-y-2">
        <Link
          href={queryFor({ arrears: "", page: "" })}
          className={`label-sm underline-offset-4 ${arrearsOnly ? "text-ink-faint hover:underline" : "text-gold-700"}`}
        >
          All members
        </Link>
        <Link
          href={queryFor({ arrears: "1", page: "" })}
          className={`label-sm underline-offset-4 ${arrearsOnly ? "text-gold-700" : "text-ink-faint hover:underline"}`}
        >
          In arrears only
        </Link>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title={q || tier || status || arrearsOnly ? "No matches" : "No members yet"}
          body={
            q || tier || status || arrearsOnly
              ? "No members match this filter. Try widening it."
              : "The register is empty. Add the Society's founding members to begin."
          }
          action={
            can(session.role, "members:write") ? (
              <ButtonLink href="/admin/members/new" variant="ghost">
                Register the first member
              </ButtonLink>
            ) : undefined
          }
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Member</Th>
                <Th>Tier</Th>
                <Th align="right">Slots</Th>
                <Th align="right">Holding</Th>
                <Th>Status</Th>
                <Th align="right">Arrears</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ member, arrearsKobo, accruing }) => (
                <tr key={String(member._id)}>
                  <Td>
                    <Link
                      href={`/admin/members/${String(member._id)}`}
                      className="text-forest-900 underline-offset-4 hover:underline"
                    >
                      {member.firstName} {member.lastName}
                    </Link>
                    <span className="label-sm mt-1 block text-ink-faint">
                      {member.membershipNumber}
                    </span>
                  </Td>
                  <Td>{TIER_LABEL[member.tier]}</Td>
                  <Td align="right">
                    <span className="tnum">{formatNumber(member.slots)}</span>
                  </Td>
                  <Td align="right">
                    <span className="tnum">
                      {formatNaira(member.slots * SLOT_PRICE_KOBO)}
                    </span>
                  </Td>
                  <Td>
                    <Badge tone={STATUS_TONE[member.status]}>
                      {STATUS_LABEL[member.status]}
                    </Badge>
                  </Td>
                  <Td align="right">
                    {!accruing ? (
                      <span className="text-ink-faint">—</span>
                    ) : arrearsKobo > 0 ? (
                      <span className="tnum text-alert">
                        {formatNaira(arrearsKobo)}
                      </span>
                    ) : (
                      <span className="tnum text-ok">Up to date</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>

          {pageCount > 1 ? (
            <nav
              aria-label="Pagination"
              className="mt-8 flex items-center justify-between gap-4"
            >
              <span className="label-sm text-ink-faint">
                Page {page} of {pageCount}
              </span>
              <div className="flex gap-3">
                {page > 1 ? (
                  <Link
                    href={queryFor({ page: String(page - 1) })}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Previous
                  </Link>
                ) : null}
                {page < pageCount ? (
                  <Link
                    href={queryFor({ page: String(page + 1) })}
                    className="label-sm border border-forest-900/25 px-4 py-2.5 text-forest-900 hover:bg-forest-900/5"
                  >
                    Next
                  </Link>
                ) : null}
              </div>
            </nav>
          ) : null}
        </>
      )}
    </>
  );
}

function fetchMembers(
  filter: QueryFilter<MemberDoc>,
  skip?: number,
  limit?: number,
) {
  const query = Member.find(filter)
    .select("membershipNumber firstName lastName tier slots status joinedOn")
    .sort({ lastName: 1, firstName: 1 });

  if (typeof skip === "number") query.skip(skip);
  if (typeof limit === "number") query.limit(limit);

  return query.lean();
}
