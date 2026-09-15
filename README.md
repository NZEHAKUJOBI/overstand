# Anchor Real Estate Group

Public site and Secretariat admin dashboard for **Anchor Real Estate Group**, a
multipurpose cooperative society limited in Abuja, Federal Capital Territory (Tier 1
Cooperative, FCTA By-Laws No. R11913).

The Society is not a developer or an estate agency. It mobilises member capital
in ₦5,000 ownership slots and deploys it across housing, tourism, warehousing,
financing and a digital cooperative platform.

Two surfaces, one Next.js app:

| Route | Purpose |
| --- | --- |
| `/` | Public landing page — static, no authentication |
| `/login` | Officer sign-in |
| `/admin/*` | Secretariat dashboard — members, payments, dues, audit trail |

## Running it

```bash
npm install
cp .env.example .env.local     # then fill both values in
npm run dev                    # http://localhost:3000
```

No MongoDB installed? Run one locally in its own terminal — it keeps its data in
`.mongo-data`, so it survives restarts:

```bash
npm run mongo:dev              # then MONGODB_URI=mongodb://127.0.0.1:27017/anchor
```

To exercise enquiry emails without sending real mail, run a local SMTP sink and
point `SMTP_HOST`/`SMTP_PORT` at it. Captured messages land in `smtp-sink.log`:

```bash
npm run mail:sink              # 127.0.0.1:2599
```

Create your first administrator (or use default autodeployment credentials `admin` / `123456789`), then sign in at `/login`:

```bash
# Runs with defaults (admin@anchorrealestategroup.ng / 123456789):
npm run seed:admin

# Or customize credentials:
npm run seed:admin -- --name "TPL Lami" --email lami@example.org \
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
| `MONGODB_URI` | Atlas SRV string or `mongodb://127.0.0.1:27017/anchor`. URL-encode the password if it contains `@ : / ? # [ ] %`. |
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
    login/                sign-in page + auth actions
    admin/                dashboard (layout guards the whole subtree)
      members/            register, create, detail, edit
      payments/           ledger, record payment
      users/              admin accounts (admin role only)
      activity/           audit trail
  components/
    admin/                admin UI kit
  lib/
    constants.ts          Society figures — slot price, fees, caps, targets
    models/               Mongoose schemas + atomic membership counter
    auth.ts / session.ts  password hashing, cookies, route guards
    rbac.ts               roles and the permission matrix
    dues.ts               monthly dues accrual and arrears
    money.ts              kobo arithmetic and naira formatting
    validation.ts         zod schemas for every form
    reporting.ts          dashboard aggregates
  proxy.ts                redirects signed-out traffic away from /admin
scripts/
  seed-admin.ts           create or reset an administrator
  verify.mts              data-layer checks against a throwaway mongod
```

## How the money is modelled

Every amount is an **integer number of kobo** (₦1 = 100 kobo). Naira exist only
as display strings and as user input being parsed. No float ever touches a
monetary value, so ₦10,000.50 cannot drift.

The Society's figures live in `src/lib/constants.ts` and nowhere else:

| | |
| --- | --- |
| Slot price | ₦5,000 |
| Slot pool | 1,000,000 (₦5bn) |
| Holding band | 100–10,000 slots (₦500,000–₦50,000,000) |
| Registration fee | ₦20,000 one-time |
| Monthly dues | ₦10,000 investor · ₦50,000 non-investor |

### Invariants and how they are enforced

- **Holding band and the 1% ceiling** — in the zod schema, so both create and
  edit go through the same rule. A non-investor member holds exactly 0 slots.
- **Pool capacity** — checked against the live sum of allocated slots before a
  member is saved, since it depends on every other member's holding.
- **Membership numbers** — allocated by an atomic `$inc` on a counter document,
  not `count() + 1`, so simultaneous registrations cannot collide.
- **One dues payment per member per month** — a partial unique index in MongoDB,
  so a double-submitted form is rejected by the database rather than by a
  read-then-write check.

There are **no multi-document transactions**, deliberately: they require a
replica set, and this way the app runs identically on Atlas and on a standalone
mongod. Every write that must be atomic is a single-document operation.

### Dues accrual

Dues accrue from the member's `joinedOn` month inclusive, while the member is
`active` or `suspended`. `pending` members have not been admitted and `exited`
members have left, so neither accrues. Suspension deliberately keeps accruing —
it usually follows arrears, and zeroing the balance would erase the debt.
Overpayment shows as credit; arrears never go negative.

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

When deploying to Vercel:

1. Import the repository into your Vercel dashboard.
2. In **Project Settings → Environment Variables**, configure:
   - `MONGODB_URI`: MongoDB Atlas connection string.
   - `SESSION_SECRET`: Random string of at least 32 characters (e.g., generate with `openssl rand -base64 32`).
   - `SEED_ADMIN_EMAIL`: (Optional, defaults to `admin@anchorrealestategroup.ng`)
   - `SEED_ADMIN_PASSWORD`: (Optional, defaults to `123456789`)
3. On MongoDB Atlas, allow access from anywhere (`0.0.0.0/0`) under **Network Access**, since Vercel uses dynamic serverless IPs.
4. Deploy! The administrator account will automatically be provisioned upon first login at `/login` with:
   - **Email**: `admin@anchorrealestategroup.ng`
   - **Password**: `123456789`

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
confirm the dues uniqueness index exists in production — `npm run seed:admin`
connecting once is enough to register the models, or call `syncIndexes()` from a
one-off script.

## Verifying

`scripts/verify.mts` spins up a throwaway mongod and exercises the data layer —
money parsing, the slot band, atomic membership numbering, the duplicate-dues
index, dues accrual across statuses, pool accounting, dashboard aggregates,
session signing and the role matrix.

```bash
npm run verify
```

It also stands up a real SMTP server on an ephemeral port and asserts that both
enquiry emails are delivered, correctly addressed, and that applicant-supplied
text is HTML-escaped before it reaches the message body.

The first run downloads a MongoDB binary (~780MB, cached afterwards), so allow
a few minutes. 37 checks; all passing as of the last run.

The HTTP layer was exercised separately against a running production build:

- Unauthenticated `/admin/*` redirects to `/login` with the `next` target kept.
- A viewer-role session is redirected off every write page to
  `/admin/no-access`.
- Member creation and payment recording driven through the real server actions,
  confirming the slot band, duplicate-email rejection, the duplicate-dues index
  and arrears arithmetic.
- The public enquiry form: valid submission, out-of-band slot figure, malformed
  email, the repeat-submission window and the honeypot — with exactly two
  emails delivered for the one valid submission and none for the rest.
- Approving an enquiry seeds a pending member (investor and non-investor tiers
  both checked); declining records the note and creates no member.
- The session cookie is `Secure` only when the request arrives over HTTPS.

## Content provenance

Landing-page content derives from the Society's infographic, which cites the
Minutes of Meeting of 20 August 2026 and the Strategic Meeting Report &
Implementation Brief of 15 August 2026. All copy lives in
[`src/lib/content.ts`](src/lib/content.ts), not in components, so it can be
checked against the Society's own documents in one place.

Two constraints follow and should be preserved:

- **Vision, Mission and Core Values are proposed, pending Board adoption.** The
  page says so next to them.
- **No investment-return language.** Slot prices, dues and the 1% holding cap
  are facts and belong on the page. Yield, ROI or "guaranteed returns" framing
  does not — it is unsupported by the source material and creates regulatory
  exposure for a cooperative soliciting member capital.

## Known gaps

- The published contact address is a personal Gmail account. On a page inviting
  ₦500,000 minimum commitments this undercuts the other trust signals; a domain
  mailbox should replace it. It is marked `provisional` in the content file.
- Financial Secretary and Assistant Secretary are unfilled and render as dashed
  offices in the org chart.
- `metadataBase` in `src/app/layout.tsx` is a placeholder domain — set it to the
  real one before launch, and add an Open Graph image.
- Payments can be recorded but not edited or reversed. A correction currently
  means a compensating entry; a void/reversal flow is the obvious next step.
- Eligibility criteria and the formal membership forms do not exist yet, so
  `/join` collects a **registration of interest** rather than an application.
  It creates no membership and takes no payment, and the page says so.
- Enquiry email is best-effort: the enquiry is saved first, then mail is
  attempted, and the outcome is shown in the admin. A failed receipt is visible
  but is not retried automatically.
- Spam protection on the public form is a honeypot, a per-email repeat window
  and a per-IP ceiling. There is no CAPTCHA; if the form is targeted, that is
  the next lever.
- Admin accounts cannot change their own password from the UI — an
  administrator re-seeds or recreates the account.
- The record-payment form lists every member in one `<select>`. That is fine at
  a few hundred and should become a search field well before a few thousand.
