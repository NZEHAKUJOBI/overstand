import { Badge, Notice, PageHeader, Table, Td, Th } from "@/components/admin/ui";
import { requirePermission } from "@/lib/auth";
import { connectDb } from "@/lib/db";
import { AdminUser } from "@/lib/models/AdminUser";
import { ROLE_DESCRIPTION, ROLE_LABEL } from "@/lib/rbac";
import { NewUserForm } from "./NewUserForm";
import { setUserActive } from "./actions";

export const metadata = { title: "Admin Users" };

export default async function UsersPage() {
  const session = await requirePermission("users:manage");
  await connectDb();

  const users = await AdminUser.find()
    .select("name email role active lastLoginAt createdAt")
    .sort({ name: 1 })
    .lean();

  return (
    <>
      <PageHeader
        title="Admin users"
        description="Accounts that can sign in to the Secretariat. Roles follow the Society's offices."
      />

      <section aria-labelledby="accounts-heading" className="mb-16">
        <h2
          id="accounts-heading"
          className="font-display mb-5 text-[1.25rem] text-forest-900"
        >
          Accounts
        </h2>

        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>Role</Th>
              <Th>Last signed in</Th>
              <Th>Status</Th>
              <Th align="right">Action</Th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isSelf = String(user._id) === session.sub;

              return (
                <tr key={String(user._id)}>
                  <Td>
                    {user.name}
                    <span className="label-sm mt-1 block break-all text-ink-faint">
                      {user.email}
                    </span>
                  </Td>
                  <Td>
                    {ROLE_LABEL[user.role]}
                    <span className="label-sm mt-1 block text-ink-faint">
                      {ROLE_DESCRIPTION[user.role]}
                    </span>
                  </Td>
                  <Td>
                    {user.lastLoginAt ? (
                      <span className="tnum">
                        {user.lastLoginAt.toLocaleDateString("en-NG", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })}
                      </span>
                    ) : (
                      <span className="text-ink-faint">Never</span>
                    )}
                  </Td>
                  <Td>
                    {user.active ? (
                      <Badge tone="ok">Active</Badge>
                    ) : (
                      <Badge tone="alert">Deactivated</Badge>
                    )}
                  </Td>
                  <Td align="right">
                    {isSelf ? (
                      <span className="label-sm text-ink-faint">You</span>
                    ) : (
                      <form action={setUserActive}>
                        <input
                          type="hidden"
                          name="userId"
                          value={String(user._id)}
                        />
                        <input
                          type="hidden"
                          name="active"
                          value={user.active ? "false" : "true"}
                        />
                        <button
                          type="submit"
                          className={`label-sm underline-offset-4 hover:underline ${
                            user.active ? "text-alert" : "text-ok"
                          }`}
                        >
                          {user.active ? "Deactivate" : "Reactivate"}
                        </button>
                      </form>
                    )}
                  </Td>
                </tr>
              );
            })}
          </tbody>
        </Table>

        <div className="mt-6">
          <Notice tone="info">
            Deactivating an account blocks sign-in immediately, but an existing
            session stays valid until it expires (up to eight hours).
          </Notice>
        </div>
      </section>

      <section aria-labelledby="new-heading" className="max-w-3xl">
        <h2
          id="new-heading"
          className="font-display mb-5 text-[1.25rem] text-forest-900"
        >
          Create an account
        </h2>
        <NewUserForm />
      </section>
    </>
  );
}
