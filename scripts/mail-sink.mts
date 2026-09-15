/**
 * A local SMTP server that accepts everything and writes what it receives to
 * smtp-sink.log. Lets you exercise enquiry receipts without sending real mail.
 *
 *   npm run mail:sink            # leave running in its own terminal
 *
 * Then in .env.local:
 *   SMTP_HOST=127.0.0.1
 *   SMTP_PORT=2599
 *   SMTP_SECURE=false
 *   MAIL_FROM="Anchor Secretariat <secretariat@anchor.test>"
 *   SECRETARIAT_EMAIL=office@anchor.test
 *
 * Development only — never point production at this.
 */
import { appendFileSync, writeFileSync } from "node:fs";
import { SMTPServer } from "smtp-server";

const PORT = Number(process.env.MAIL_SINK_PORT ?? 2599);
const LOG = "smtp-sink.log";

writeFileSync(LOG, "");

/**
 * Subjects arrive RFC 2047 encoded when they contain non-ASCII characters.
 * The escaped bytes must be collected and decoded as UTF-8 together — decoding
 * each one on its own turns a multi-byte character into mojibake.
 */
function decodeSubject(raw: string): string {
  return raw.replace(/=\?UTF-8\?Q\?(.*?)\?=/gi, (_, encoded: string) => {
    const bytes: number[] = [];
    const text = encoded.replace(/_/g, " ");

    for (let i = 0; i < text.length; i += 1) {
      if (text[i] === "=" && /^[0-9A-F]{2}$/i.test(text.slice(i + 1, i + 3))) {
        bytes.push(parseInt(text.slice(i + 1, i + 3), 16));
        i += 2;
      } else {
        bytes.push(text.charCodeAt(i));
      }
    }

    return Buffer.from(bytes).toString("utf8");
  });
}

const server = new SMTPServer({
  authOptional: true,
  disabledCommands: ["STARTTLS", "AUTH"],
  onData(stream, session, callback) {
    const chunks: Buffer[] = [];
    stream.on("data", (chunk: Buffer) => chunks.push(chunk));
    stream.on("end", () => {
      const body = Buffer.concat(chunks).toString("utf8");
      const subject = decodeSubject(
        /^Subject: (.*)$/m.exec(body)?.[1] ?? "(no subject)",
      );
      const to = session.envelope.rcptTo.map((r) => r.address).join(", ");

      appendFileSync(
        LOG,
        `\n${"=".repeat(72)}\nTO: ${to}\nSUBJECT: ${subject}\n${"=".repeat(72)}\n${body}\n`,
      );
      console.log(`  ✉  ${to} — ${subject}`);
      callback();
    });
  },
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`\n  SMTP sink listening on 127.0.0.1:${PORT}`);
  console.log(`  Messages are appended to ${LOG}`);
  console.log("  Press Ctrl+C to stop.\n");
});
