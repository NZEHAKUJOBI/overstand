import { ButtonLink, Notice, PageHeader } from "@/components/admin/ui";
import { requireSession } from "@/lib/auth";
import { ROLE_DESCRIPTION, ROLE_LABEL } from "@/lib/rbac";

export default async function NoAccessPage({
  searchParams,
}: {
  searchParams: Promise<{ need?: string }>;
}) {
  const { need } = await searchParams;
  const session = await requireSession();

  return (
    <>
      <PageHeader
        title="Not permitted"
        description="Your account does not carry the permission this page requires."
      />

      <div className="max-w-2xl space-y-6">
        <Notice tone="error">
          {need
            ? `This page requires the “${need}” permission.`
            : "You do not have permission to view that page."}
        </Notice>

        <div className="border-t border-rule pt-6">
          <p className="label-sm text-ink-faint">Your role</p>
          <p className="font-display mt-2 text-[1.25rem] text-forest-900">
            {ROLE_LABEL[session.role]}
          </p>
          <p className="mt-2 text-[0.9375rem] text-ink-soft">
            {ROLE_DESCRIPTION[session.role]}
          </p>
        </div>

        <p className="text-[0.9375rem] text-ink-soft">
          If you need this access, ask an administrator to change your role.
        </p>

        <ButtonLink href="/admin" variant="ghost">
          Back to overview
        </ButtonLink>
      </div>
    </>
  );
}
