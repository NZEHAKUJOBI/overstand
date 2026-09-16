# Brand assets

Source artwork for the Society's crest, and the script that derives every
rendered asset from it.

| File | What it is |
| --- | --- |
| `overstand-logo.pdf` | The original supplied lockup — crest over wordmark |
| `overstand-lockup.jpg` | The 1024×1024 raster extracted from that PDF |
| `build-brand.mjs` | Regenerates the icon set and the Open Graph card |

## Regenerating

```bash
node brand/build-brand.mjs brand/overstand-lockup.jpg
```

It writes into `src/app/`:

| Output | Size | Notes |
| --- | --- | --- |
| `logo.png` | 512×512 | The crest, masked to its circle with transparent corners — what `<Crest>` renders |
| `icon.png` | 512×512 | Browser tab icon |
| `apple-icon.png` | 180×180 | On the navy ground, since iOS composites transparency away |
| `favicon.ico` | 16/32/48 | An ICO directory wrapping PNG payloads |
| `opengraph-image.png` | 1200×630 | Crest over wordmark on navy, with the gold rule |

The crop rectangles at the top of the script were measured from the source by
scanning for blank rows and columns. If the artwork is ever resupplied at a
different size or composition, re-measure them rather than assuming.

The wordmark is dark ink on white in the source. The script inverts its
luminance into an alpha channel and tints it, so no font needs to be installed
to set the Society's name — and the same artwork can be recoloured for any
ground.
