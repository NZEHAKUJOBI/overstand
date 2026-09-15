import { EmptyState, ButtonLink, PageHeader } from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { PaymentForm, type MemberOption } from "../PaymentForm";

export const metadata = { title: "Record Payment" };

export default async function NewPaymentPage({
  searchParams,
}: {
  searchParams: Promise<{ member?: string }>;
}) {
  await requirePermission("payments:write");
  const { member: selectedMemberId } = await searchParams;

  await connectDb();

  const members = await Member.find({ status: { $ne: "exited" } })
    .select("membershipNumber firstName lastName tier")
    .sort({ lastName: 1, firstName: 1 })
    .lean();

  const options: MemberOption[] = members.map((member) => ({
    id: String(member._id),
    label: `${member.lastName}, ${member.firstName} — ${member.membershipNumber}`,
    tier: member.tier,
  }));

  return (
    <>
      <PageHeader
        title="Record a payment"
        description="Enter the sum actually received. Amounts are stored to the kobo."
      />

      {options.length === 0 ? (
        <EmptyState
          title="No members to credit"
          body="Register a member before recording payments against the Society's accounts."
          action={
            <ButtonLink href="/admin/members/new" variant="ghost">
              Register a member
            </ButtonLink>
          }
        />
      ) : (
        <PaymentForm members={options} selectedMemberId={selectedMemberId} />
      )}
    </>
  );
}
