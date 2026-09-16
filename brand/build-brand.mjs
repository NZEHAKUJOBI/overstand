import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
const require = createRequire(process.cwd() + "/package.json");
const sharp = require("sharp");

const SRC = process.argv[2];
const OUT = "src/app";

/* Measured from the source lockup by scanning for blank rows and columns. */
const CREST = { left: 272, top: 199, width: 480, height: 480 };
const WORD = { left: 192, top: 704, width: 640, height: 120 };

const NAVY = { r: 5, g: 20, b: 42 };
const PAPER = { r: 246, g: 245, b: 240 };

/** The crest cropped square and masked to its circle, corners transparent. */
async function crestPng(size) {
  const mask = Buffer.from(
    `<svg width="${size}" height="${size}"><circle cx="${size / 2}" cy="${size / 2}" r="${size / 2}" fill="#fff"/></svg>`,
  );

  return sharp(SRC)
    .extract(CREST)
    .resize(size, size, { fit: "fill" })
    .ensureAlpha()
    .composite([{ input: mask, blend: "dest-in" }])
    .png()
    .toBuffer();
}

/**
 * The wordmark is dark ink on white in the source. Rather than depend on a
 * font being installed, its inverted luminance becomes an alpha channel, so it
 * can be tinted any colour and dropped onto the navy ground cleanly.
 *
 * The scaling happens before the alpha is built, not after: resizing a raw
 * buffer that has just had a channel joined onto it loses the join.
 */
async function wordmarkPng(color, width) {
  const { data, info } = await sharp(SRC)
    .extract(WORD)
    .resize({ width })
    .greyscale()
    .raw()
    .toBuffer({ resolveWithObject: true });

  const px = info.width * info.height;
  const alpha = Buffer.alloc(px);
  for (let i = 0; i < px; i++) alpha[i] = 255 - data[i * info.channels];

  const solid = await sharp({
    create: {
      width: info.width,
      height: info.height,
      channels: 3,
      background: color,
    },
  })
    .raw()
    .toBuffer();

  const png = await sharp(solid, {
    raw: { width: info.width, height: info.height, channels: 3 },
  })
    .joinChannel(alpha, {
      raw: { width: info.width, height: info.height, channels: 1 },
    })
    .png()
    .toBuffer();

  return { png, width: info.width, height: info.height };
}

/* ── The crest, as used by <Crest> and the tab icons ── */

writeFileSync(`${OUT}/logo.png`, await crestPng(512));
writeFileSync(`${OUT}/icon.png`, await crestPng(512));

/* iOS composites away transparency, so the Apple icon gets the navy ground. */
writeFileSync(
  `${OUT}/apple-icon.png`,
  await sharp({
    create: { width: 180, height: 180, channels: 4, background: NAVY },
  })
    .composite([{ input: await crestPng(150), left: 15, top: 15 }])
    .png()
    .toBuffer(),
);

/* ── favicon.ico — an ICO directory wrapping PNG payloads ── */

const icoSizes = [16, 32, 48];
const pngs = await Promise.all(icoSizes.map((s) => crestPng(s)));

const header = Buffer.alloc(6);
header.writeUInt16LE(0, 0);
header.writeUInt16LE(1, 2); // type: icon
header.writeUInt16LE(icoSizes.length, 4);

let offset = 6 + 16 * icoSizes.length;
const entries = icoSizes.map((s, i) => {
  const e = Buffer.alloc(16);
  e.writeUInt8(s, 0);
  e.writeUInt8(s, 1);
  e.writeUInt16LE(1, 4); // colour planes
  e.writeUInt16LE(32, 6); // bits per pixel
  e.writeUInt32LE(pngs[i].length, 8);
  e.writeUInt32LE(offset, 12);
  offset += pngs[i].length;
  return e;
});
writeFileSync(`${OUT}/favicon.ico`, Buffer.concat([header, ...entries, ...pngs]));

/* ── Open Graph card — crest over wordmark on the navy ground ── */

const OG = { w: 1200, h: 630 };
const ogCrest = await crestPng(240);
const word = await wordmarkPng(PAPER, 520);

writeFileSync(
  `${OUT}/opengraph-image.png`,
  await sharp({
    create: { width: OG.w, height: OG.h, channels: 4, background: NAVY },
  })
    .composite([
      {
        input: Buffer.from(
          `<svg width="${OG.w}" height="6"><rect width="${OG.w}" height="6" fill="#c9a961"/></svg>`,
        ),
        left: 0,
        top: 0,
      },
      { input: ogCrest, left: Math.round((OG.w - 240) / 2), top: 130 },
      {
        input: word.png,
        left: Math.round((OG.w - word.width) / 2),
        top: 415,
      },
    ])
    .png()
    .toBuffer(),
);

console.log("wrote logo.png, icon.png, apple-icon.png, favicon.ico, opengraph-image.png");
