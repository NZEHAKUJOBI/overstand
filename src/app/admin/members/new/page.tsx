import { PageHeader } from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { MemberForm } from "../MemberForm";
import { createMember } from "../actions";

export const metadata = { title: "Register Member" };

export default async function NewMemberPage() {
  await requirePermission("members:write");

  return (
    <>
      <PageHeader
        title="Register a member"
        description="A membership number is allocated automatically once the record is saved."
      />
      <MemberForm
        action={createMember}
        submitLabel="Register Member"
        cancelHref="/admin/members"
      />
    </>
  );
}
