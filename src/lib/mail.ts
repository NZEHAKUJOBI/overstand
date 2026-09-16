import nodemailer, { type Transporter } from "nodemailer";
import type { ApplicationDoc } from "./models/Application";
import { APPLICATION_FEE_KOBO, TIER_INTEREST_LABEL, contributionRateKobo } from "./constants";
import { formatNaira } from "./money";

/**
 * Outbound mail over SMTP.
 *
 * If SMTP is not configured the app still works — sending is skipped and the
 * application records that, rather than failing the submission. Losing an application
 * because a mail server is down would be worse than not sending the receipt.
 *
 * Render blocks outbound port 25, so use 587 (STARTTLS) or 465 (implicit TLS).
 */

let cached: Transporter | null = null;

function cleanHost(host: string | undefined): string | undefined {
  if (!host) return undefined;
  let cleaned = host.trim().replace(/^https?:\/\//i, "").replace(/^\/\//, "").replace(/\/.*$/, "");
  if (cleaned.toLowerCase() === "resend.com") {
    cleaned = "smtp.resend.com";
  }
  return cleaned;
}

export function resendApiKey(): string | undefined {
  if (process.env.RESEND_API_KEY?.trim()) return process.env.RESEND_API_KEY.trim();
  if (process.env.SMTP_PASS?.trim().startsWith("re_")) return process.env.SMTP_PASS.trim();
  return undefined;
}

export function isMailConfigured(): boolean {
  return Boolean(
    (resendApiKey() && process.env.MAIL_FROM) ||
      (process.env.SMTP_HOST && process.env.MAIL_FROM),
  );
}

function transporter(): Transporter {
  if (cached) return cached;

  const host = cleanHost(process.env.SMTP_HOST);
  const port = Number(process.env.SMTP_PORT ?? 587);

  cached = nodemailer.createTransport({
    host,
    port,
    // 465 is implicit TLS; 587 upgrades via STARTTLS.
    secure: process.env.SMTP_SECURE
      ? process.env.SMTP_SECURE === "true"
      : port === 465,
    auth: process.env.SMTP_USER
      ? { user: process.env.SMTP_USER.trim(), pass: process.env.SMTP_PASS?.trim() }
      : undefined,
    connectionTimeout: 10_000,
    greetingTimeout: 10_000,
    socketTimeout: 20_000,
  });

  return cached;
}

export function cleanFromAddress(raw: string | undefined): string {
  const FALLBACK = "Overstand Cooperative <onboarding@resend.dev>";
  if (!raw) return FALLBACK;

  // Strip ALL quote characters everywhere, then trim
  const s = raw.replace(/["""''`]/g, "").trim();

  // Extract email from angle brackets: Name <email@domain>
  const angleMatch = s.match(/^(.*?)\s*<\s*([^<>\s]+@[^<>\s]+)\s*>$/);
  if (angleMatch) {
    const name = angleMatch[1].trim();
    const email = angleMatch[2].trim();
    return name ? `${name} <${email}>` : email;
  }

  // Bare email: user@domain.com
  if (/^[^\s<>]+@[^\s<>]+\.[^\s<>]+$/.test(s)) {
    return s;
  }

  // Nothing valid — return the fallback
  return FALLBACK;
}

export function cleanEmailAddress(addr: string | undefined): string | undefined {
  if (!addr) return undefined;
  const s = addr.replace(/["""''`]/g, "").trim();
  const match = s.match(/<\s*([^<>\s]+@[^<>\s]+)\s*>/);
  if (match) return match[1].trim();
  if (/^[^\s<>]+@[^\s<>]+$/.test(s)) return s;
  return undefined;
}

function cleanReplyTo(addr: string | undefined): string | undefined {
  if (!addr) return undefined;
  return addr.replace(/["""''`]/g, "").trim() || undefined;
}

type SendParams = {
  from: string;
  to: string;
  replyTo?: string;
  subject: string;
  text: string;
  html: string;
};

async function sendMailMessage(params: SendParams): Promise<void> {
  const from = cleanFromAddress(params.from);
  const to = params.to.trim();
  const replyTo = cleanReplyTo(params.replyTo);

  console.log("[mail] sending — raw from:", JSON.stringify(params.from), "→ cleaned:", JSON.stringify(from), "to:", to);

  const apiKey = resendApiKey();
  if (apiKey) {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from,
        to: [to],
        reply_to: replyTo ? [replyTo] : undefined,
        subject: params.subject,
        text: params.text,
        html: params.html,
      }),
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Resend HTTP ${res.status}: ${body}`);
    }
    return;
  }

  await transporter().sendMail({
    from,
    to,
    replyTo,
    subject: params.subject,
    text: params.text,
    html: params.html,
  });
}

/** Only used by tests, which stand up a throwaway SMTP server per run. */
export function resetMailTransport(): void {
  cached = null;
}

export function siteUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://overstandcooperative.ng"
  ).replace(/\/$/, "");
}

export function secretariatAddress(): string | undefined {
  const raw = process.env.SECRETARIAT_EMAIL ?? process.env.MAIL_FROM;
  return cleanEmailAddress(raw);
}

type Mail = { subject: string; text: string; html: string };

/* ── Presentation ─────────────────────────────────────────────────── */

const BRAND = {
  navy: "#0a2240",
  gold: "#c9a961",
  paper: "#f6f5f0",
  ink: "#16202c",
  soft: "#4a5663",
  rule: "#d7d3c8",
};

/** Email clients strip <style>, so everything here is inlined. */
function shell(heading: string, body: string): string {
  return `<!doctype html>
<html lang="en"><body style="margin:0;padding:0;background:${BRAND.paper};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:${BRAND.paper};padding:32px 16px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid ${BRAND.rule};">
  <tr><td style="background:${BRAND.navy};padding:28px 32px;border-top:3px solid ${BRAND.gold};">
    <div style="font:600 11px/1.4 'Helvetica Neue',Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:${BRAND.gold};">Overstand Cooperative</div>
    <div style="font:400 20px/1.3 Georgia,'Times New Roman',serif;color:${BRAND.paper};margin-top:8px;">${heading}</div>
  </td></tr>
  <tr><td style="padding:32px;font:400 15px/1.65 'Helvetica Neue',Arial,sans-serif;color:${BRAND.ink};">
    ${body}
  </td></tr>
  <tr><td style="padding:20px 32px;border-top:1px solid ${BRAND.rule};font:400 12px/1.6 'Helvetica Neue',Arial,sans-serif;color:${BRAND.soft};">
    Overstand Multi-Purpose Cooperative Society Limited<br>
    1004 Ameh Ebute Street, Suite D-18, Boya Place Plaza, Wuye, Abuja–FCT<br>
    Reg. No. 3591
  </td></tr>
</table>
</td></tr></table></body></html>`;
}

function rows(pairs: Array<[string, string]>): string {
  return `<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;margin:20px 0;">
${pairs
  .map(
    ([term, value]) =>
      `<tr><td style="padding:9px 0;border-bottom:1px solid ${BRAND.rule};font:600 11px/1.4 'Helvetica Neue',Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:${BRAND.soft};width:42%;vertical-align:top;">${escapeHtml(term)}</td>
<td style="padding:9px 0;border-bottom:1px solid ${BRAND.rule};font:400 15px/1.5 'Helvetica Neue',Arial,sans-serif;color:${BRAND.ink};">${escapeHtml(value)}</td></tr>`,
  )
  .join("\n")}
</table>`;
}

/** Application fields are attacker-controlled; never interpolate them raw. */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}



function summaryPairs(application: ApplicationDoc): Array<[string, string]> {
  const pairs: Array<[string, string]> = [
    ["Reference", application.reference],
    ["Name", `${application.firstName} ${application.lastName}`],
    ["Email", application.email],
    ["Phone", application.phone],
    ["Contribution tier", TIER_INTEREST_LABEL[application.tierInterest]],
    [
      "Monthly contribution",
      formatNaira(
        contributionRateKobo(
          application.tierInterest,
          application.customContributionKobo,
        ),
      ),
    ],
  ];

  pairs.push(["Next of kin", `${application.nextOfKin.name} (${application.nextOfKin.relationship})`]);
  pairs.push(["Next-of-kin phone", application.nextOfKin.phone]);
  if (application.occupation) pairs.push(["Occupation", application.occupation]);
  if (application.address) pairs.push(["Address", application.address]);
  if (application.heardFrom) pairs.push(["Heard about us via", application.heardFrom]);

  return pairs;
}

function plainPairs(pairs: Array<[string, string]>): string {
  return pairs.map(([term, value]) => `${term}: ${value}`).join("\n");
}

/* ── Messages ─────────────────────────────────────────────────────── */

export function applicantReceipt(application: ApplicationDoc): Mail {
  const pairs = summaryPairs(application);

  const text = `Dear ${application.firstName},

Thank you for applying for membership of Overstand Multi-Purpose Cooperative Society Limited, a registered multipurpose cooperative society in Wuye, Abuja.

We have recorded your application under reference ${application.reference}. A member of the Secretariat will be in touch.

What you submitted
${plainPairs(pairs)}

What happens next
The Secretariat will contact you with the Membership/Entrance Form and instructions for the ${formatNaira(APPLICATION_FEE_KOBO)} application fee, which is non-refundable and covers the form, your ID card and administrative processing. Submitting this form does not admit you to membership, and no payment has been taken.

If any detail above is wrong, reply to this message and we will correct it.

Overstand Multi-Purpose Cooperative Society Limited
1004 Ameh Ebute Street, Suite D-18, Boya Place Plaza, Wuye, Abuja–FCT`;

  const html = shell(
    "We have your application",
    `<p style="margin:0 0 16px;">Dear ${escapeHtml(application.firstName)},</p>
<p style="margin:0 0 16px;">Thank you for applying for membership of Overstand Multi-Purpose Cooperative Society Limited, a registered multipurpose cooperative society in Wuye, Abuja. Your application is recorded under reference <strong>${escapeHtml(application.reference)}</strong>, and a member of the Secretariat will be in touch.</p>
<p style="margin:24px 0 0;font:600 11px/1.4 'Helvetica Neue',Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:${BRAND.gold};">What you submitted</p>
${rows(pairs)}
<p style="margin:24px 0 0;font:600 11px/1.4 'Helvetica Neue',Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:${BRAND.gold};">What happens next</p>
<p style="margin:12px 0 16px;">The Secretariat will contact you with the Membership/Entrance Form and instructions for the ${formatNaira(APPLICATION_FEE_KOBO)} application fee, which is non-refundable and covers the form, your ID card and administrative processing. <strong>Submitting this form does not admit you to membership, and no payment has been taken.</strong></p>
<p style="margin:0;color:${BRAND.soft};">If any detail above is wrong, reply to this message and we will correct it.</p>`,
  );

  return {
    subject: `Your application — ${application.reference}`,
    text,
    html,
  };
}

export function secretariatNotice(application: ApplicationDoc): Mail {
  const pairs = summaryPairs(application);
  const link = `${siteUrl()}/admin/applications/${String(application._id)}`;

  const text = `New membership application — ${application.reference}

${plainPairs(pairs)}
${application.message ? `\nMessage:\n${application.message}\n` : ""}
Review it: ${link}`;

  const html = shell(
    "New membership application",
    `<p style="margin:0 0 16px;">A new application was submitted through the public site.</p>
${rows(pairs)}
${
  application.message
    ? `<p style="margin:20px 0 6px;font:600 11px/1.4 'Helvetica Neue',Arial,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:${BRAND.gold};">Message</p>
<p style="margin:0 0 16px;white-space:pre-wrap;">${escapeHtml(application.message)}</p>`
    : ""
}
<p style="margin:24px 0 0;"><a href="${escapeHtml(link)}" style="display:inline-block;background:${BRAND.navy};color:${BRAND.paper};text-decoration:none;padding:13px 22px;font:600 11px/1 'Helvetica Neue',Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;">Review in the Secretariat</a></p>`,
  );

  return {
    subject: `New application — ${application.firstName} ${application.lastName} (${application.reference})`,
    text,
    html,
  };
}

/* ── Sending ──────────────────────────────────────────────────────── */

export type SendOutcome = { applicant: string; secretariat: string; error?: string };

/**
 * Sends both messages. Never throws: the caller has already saved the application,
 * and a mail failure must not lose it. Outcomes are recorded on the document
 * so the Secretariat can see when a receipt did not go out.
 */
export async function sendApplicationMail(application: ApplicationDoc): Promise<SendOutcome> {
  if (!isMailConfigured()) {
    console.warn("[mail] SMTP not configured — skipping application mail");
    return { applicant: "skipped", secretariat: "skipped" };
  }

  const from = process.env.MAIL_FROM as string;
  const secretariat = secretariatAddress();
  const outcome: SendOutcome = { applicant: "pending", secretariat: "pending" };

  const results = await Promise.allSettled([
    (async () => {
      const message = applicantReceipt(application);
      await sendMailMessage({
        from,
        to: application.email,
        replyTo: secretariat,
        subject: message.subject,
        text: message.text,
        html: message.html,
      });
    })(),
    (async () => {
      if (!secretariat) return "skipped";
      const message = secretariatNotice(application);
      await sendMailMessage({
        from,
        to: secretariat,
        replyTo: `${application.firstName} ${application.lastName} <${application.email}>`,
        subject: message.subject,
        text: message.text,
        html: message.html,
      });
      return "sent";
    })(),
  ]);

  const errors: string[] = [];

  if (results[0].status === "fulfilled") {
    outcome.applicant = "sent";
  } else {
    outcome.applicant = "failed";
    errors.push(`applicant: ${reasonOf(results[0].reason)}`);
  }

  if (results[1].status === "fulfilled") {
    outcome.secretariat = results[1].value === "skipped" ? "skipped" : "sent";
  } else {
    outcome.secretariat = "failed";
    errors.push(`secretariat: ${reasonOf(results[1].reason)}`);
  }

  if (errors.length) {
    outcome.error = errors.join("; ");
    console.error("[mail] application mail problem", outcome.error);
  }

  return outcome;
}

function reasonOf(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}
