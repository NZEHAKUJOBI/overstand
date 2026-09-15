import { notFound } from "next/navigation";
import { isValidObjectId } from "mongoose";
import { PageHeader } from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { Member } from "@/lib/models/Member";
import { MemberForm } from "../../MemberForm";
import { updateMember } from "../../actions";

export const metadata = { title: "Edit Member" };

export default async function EditMemberPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await requirePermission("members:write");
  const { id } = await params;

  if (!isValidObjectId(id)) notFound();

  await connectDb();
  const member = await Member.findById(id).lean();
  if (!member) notFound();

  return (
    <>
      <PageHeader
        title={`Edit ${member.firstName} ${member.lastName}`}
        description={member.membershipNumber}
      />
      <MemberForm
        action={updateMember}
        memberId={id}
        submitLabel="Save Changes"
        cancelHref={`/admin/members/${id}`}
        defaults={{
          firstName: member.firstName,
          lastName: member.lastName,
          otherNames: member.otherNames ?? "",
          email: member.email,
          phone: member.phone,
          address: member.address ?? "",
          tier: member.tier,
          slots: member.slots,
          status: member.status,
          joinedOn: member.joinedOn.toISOString().slice(0, 10),
          notes: member.notes ?? "",
        }}
      />
    </>
  );
}
