# Overstand Multipurpose Cooperative Society

Public site and Secretariat admin dashboard for **Overstand Multi-Purpose
Cooperative Society Limited** (Reg. No. 3591), a registered and duly certified
multipurpose cooperative society at 1004 Ameh Ebute Street, Suite D-18, Boya
Place Plaza, Wuye, Abuja–FCT.

The Society pools member contributions and deploys them across real estate,
agriculture, member lending, wealth management and travel services.

Two surfaces, one Next.js app:

| Route | Purpose |
| --- | --- |
| `/` | Public landing page — static, no authentication |
| `/join` | Membership application — personal and next-of-kin details |
| `/login` | Officer sign-in |
| `/admin/*` | Secretariat dashboard — members, payments, contributions, audit trail |

## Running it

```bash
npm install
cp .env.example .env.local     # then fill both values in
npm run dev                    # http://localhost:3000
```

No MongoDB installed? Run one locally in its own terminal — it keeps its data in
`.mongo-data`, so it survives restarts:

```bash
npm run mongo:dev              # then MONGODB_URI=mongodb://127.0.0.1:27017/overstand
```

To exercise application emails without sending real mail, run a local SMTP sink
and point `SMTP_HOST`/`SMTP_PORT` at it. Captured messages land in
`smtp-sink.log`:

```bash
npm run mail:sink              # 127.0.0.1:2599
```

Create your first administrator (or use default autodeployment credentials
`admin` / `123456789`), then sign in at `/login`:

```bash
# Runs with defaults (admin@overstandcooperative.ng / 123456789):
npm run seed:admin

# Or customize credentials:
npm run seed:admin -- --name "Secretary" --email sec@example.org \
                      --password "123456789" --role admin
```

Re-running the seed with the same email resets that account's password and
role, which is also how you recover a locked-out administrator. On autodeployment
(e.g., Render), the administrator is seeded automatically on startup.

Other scripts:

```bash
npm run build   # production build
npm run start   # serve the production build
npm run lint
```

## Environment

Both variables are required; the app fails with a clear message if either is
missing.

| Variable | Notes |
| --- | --- |
| `MONGODB_URI` | Atlas SRV string or `mongodb://127.0.0.1:27017/overstand`. URL-encode the password if it contains `@ : / ? # [ ] %`. |
| `SESSION_SECRET` | At least 32 characters — `openssl rand -base64 32`. Rotating it signs every officer out immediately. |

## Stack

Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · MongoDB via
Mongoose 9 · bcryptjs · jose · zod.

The landing page is fully static. Admin pages are server-rendered per request,
mutate through server actions, and ship only the small amount of client
JavaScript the forms and navigation need.

## Structure

```
src/
  app/
    page.tsx              public landing page
    join/                 membership application + submission action
    login/                sign-in page + auth actions
    admin/                dashboard (layout guards the whole subtree)
      members/            register, create, detail, edit
      payments/           ledger, record payment
      applications/       review queue, approve into the register
      users/              admin accounts (admin role only)
      activity/           audit trail
  components/
    admin/                admin UI kit
  lib/
    constants.ts          Society figures — fees, tiers, caps
    content.ts            every word on the public site
    models/               Mongoose schemas + atomic membership counter
    auth.ts / session.ts  password hashing, cookies, route guards
    rbac.ts               roles and the permission matrix
    contributions.ts      monthly contribution accrual and arrears
    money.ts              kobo arithmetic and naira formatting
    validation.ts         zod schemas for every form
    reporting.ts          dashboard aggregates
  proxy.ts                redirects signed-out traffic away from /admin
scripts/
  seed-admin.ts           create or reset an administrator
  verify.mts              data-layer checks against a throwaway mongod
brand/
  overstand-logo.pdf      supplied artwork; build-brand.mjs derives the icon set
```

## How the money is modelled

Every amount is an **integer number of kobo** (₦1 = 100 kobo). Naira exist only
as display strings and as user input being parsed. No float ever touches a
monetary value, so ₦10,000.50 cannot drift.

The Society's figures live in `src/lib/constants.ts` and nowhere else:

| | |
| --- | --- |
| Application fee | ₦20,000 one-time, non-refundable |
| Registration fee | **Amount not yet supplied** — `null` in constants |
| Annual membership fee | **Amount not yet supplied** — `null` in constants |
| Tier 1 contribution | ₦25,000 per month |
| Tier 2 contribution | ₦50,000 per month |
| Tailored contribution | Above ₦50,000, agreed member by member |

### Invariants and how they are enforced

- **The contribution tier** — in the zod schema, shared by the public
  application and the admin form, so both enforce it identically. A tailored
  amount must be strictly above Tier 2; the standard tiers carry no custom
  figure at all.
- **Minimum age** — 18, checked from the date of birth on the public
  application rather than left for the Secretariat to catch on the paper form.
- **Next of kin** — required by the Membership Application Form, so name,
  relationship and phone are mandatory in both the zod schema and the Mongoose
  subdocument.
- **Membership numbers** — allocated by an atomic `$inc` on a counter document,
  not `count() + 1`, so simultaneous registrations cannot collide.
- **One contribution payment per member per month** — a partial unique index in
  MongoDB, so a double-submitted form is rejected by the database rather than
  by a read-then-write check.

There are **no multi-document transactions**, deliberately: they require a
replica set, and this way the app runs identically on Atlas and on a standalone
mongod. Every write that must be atomic is a single-document operation.

### Contribution accrual

Contributions accrue from the member's `joinedOn` month inclusive, while the
member is `active` or `suspended`. `pending` members have not been admitted and
`exited` members have left, so neither accrues. Suspension deliberately keeps
accruing — it usually follows arrears, and zeroing the balance would erase the
debt. Overpayment shows as credit; arrears never go negative.

A tailored member accrues at their own agreed rate. Where no rate has been
recorded for one, accrual falls back to the Tier 2 floor, so a missing figure
can never under-bill.

Arrears are **derived, not stored**. That keeps them correct by construction,
at the cost of computing across the accruing set for the arrears view. Fine at
a few hundred members; it would want a materialised balance well before tens of
thousands.

## Roles

Roles mirror the Society's offices, so access matches responsibility.

| Role | Members | Payments | Admin users | Audit |
| --- | --- | --- | --- | --- |
| Administrator | read/write | read/write | yes | yes |
| Treasurer | read/write | read/write | — | yes |
| Financial Secretary | read | read/write | — | — |
| Secretary | read/write | read | — | — |
| Viewer | read | read | — | — |

`proxy.ts` redirects signed-out traffic away from `/admin`, but that is a
convenience layer — server actions are reachable without matching a route. The
real boundary is `requireSession` / `requirePermission` / `checkPermission`,
called by every admin page and every action.

Every change to the register, to payments and to admin accounts is written to
an audit log with the officer who made it, visible at `/admin/activity`.

## Deploying to Vercel

1. Import the repository into your Vercel dashboard.
2. In **Project Settings → Environment Variables**, configure:
   - `MONGODB_URI`: MongoDB Atlas connection string.
   - `SESSION_SECRET`: Random string of at least 32 characters (e.g., generate with `openssl rand -base64 32`).
   - `SEED_ADMIN_EMAIL`: (Optional, defaults to `admin@overstandcooperative.ng`)
   - `SEED_ADMIN_PASSWORD`: (Optional, defaults to `123456789`)
3. On MongoDB Atlas, allow access from anywhere (`0.0.0.0/0`) under **Network Access**, since Vercel uses dynamic serverless IPs.
4. Deploy. The administrator account is provisioned on first login at `/login`.

## Deploying to Render

`render.yaml` is a blueprint for a Node web service. After creating it:

1. Set `MONGODB_URI` in the Render dashboard (it is marked `sync: false`, so it
   is never stored in the repo). `SESSION_SECRET` is generated by Render.
2. On MongoDB Atlas, allow the service's outbound IPs under **Network Access**.
   Atlas rejects the connection silently-ish otherwise — the dashboard will show
   a server-selection timeout.
3. Seed the first administrator by running the seed command against the
   production `MONGODB_URI` from your machine, or from a Render shell.

Mongoose autocreates indexes on first use in development. Before going live,
confirm the contribution uniqueness index exists in production — a single
`npm run seed:admin` connection is enough to register the models, or call
`syncIndexes()` from a one-off script.

## Verifying

`scripts/verify.mts` spins up a throwaway mongod and exercises the data layer —
money parsing, the contribution tiers, the minimum age, the next-of-kin
requirement, atomic membership numbering, the duplicate-contribution index,
accrual across statuses, dashboard aggregates, session signing and the role
matrix.

```bash
npm run verify
```

It also stands up a real SMTP server on an ephemeral port and asserts that both
application emails are delivered, correctly addressed, and that
applicant-supplied text is HTML-escaped before it reaches the message body.

The first run downloads a MongoDB binary (~780MB, cached afterwards), so allow
a few minutes. 46 checks; all passing as of the last run.

## Content provenance

Landing-page content derives from the Society's Official Update. All copy lives
in [`src/lib/content.ts`](src/lib/content.ts), not in components, so it can be
checked against the Society's own documents in one place.

Two constraints follow and should be preserved:

- **Nothing on the page goes beyond the Official Update.** It states a mission
  but no vision, core values, roster of offices, target-market breakdown or
  social-responsibility programme, so the site has no sections for those. Add
  them back when the Society supplies the source material, not before.
- **No investment-return language.** Fees, tiers and the contribution structure
  are facts and belong on the page. Yield, ROI or "guaranteed returns" framing
  does not — it is unsupported by the source material and creates regulatory
  exposure for a cooperative soliciting member capital.

## Known gaps

- **The registration and annual fee amounts are unknown.** The Official Update
  names both without stating a figure. They are `null` in
  `src/lib/constants.ts` and render as "confirm at the office" on the public
  page. Fill them in when the Society confirms them.
- **No phone number or email address.** `phones` is an empty array and
  `email.address` an empty string in `src/lib/content.ts`; the footer, the
  application page and the structured data all omit the contact block rather
  than publishing a placeholder. Supply them before launch.
- **Bank details are a generic list.** `BANKS` in `src/lib/constants.ts` should
  be narrowed to the accounts the Society actually receives through.
- `metadataBase` in `src/app/layout.tsx` is a placeholder domain — set it to
  the real one before launch.
- Loans, savings, agricultural projects and travel services are advertised on
  the public page but are not administered in the dashboard. Only membership,
  contributions and fees are.
- Payments can be recorded but not edited or reversed. A correction currently
  means a compensating entry; a void/reversal flow is the obvious next step.
- The application takes no payment. The ₦20,000 fee is collected at the office
  and recorded by an officer, and the page says so.
- Application email is best-effort: the application is saved first, then mail
  is attempted, and the outcome is shown in the admin. A failed receipt is
  visible but is not retried automatically.
- Spam protection on the public form is a honeypot, a per-email repeat window
  and a per-IP ceiling. There is no CAPTCHA; if the form is targeted, that is
  the next lever.
- Admin accounts cannot change their own password from the UI — an
  administrator re-seeds or recreates the account.
- The record-payment form lists every member in one `<select>`. That is fine at
  a few hundred and should become a search field well before a few thousand.
