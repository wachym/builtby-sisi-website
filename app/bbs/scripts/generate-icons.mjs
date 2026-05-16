import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const source = path.join(root, "public", "BBS.png");
const iconsDir = path.join(root, "public", "icons");

const BRAND_BG = { r: 43, g: 45, b: 87, alpha: 1 };

async function resizeIcon(size, outputName, { maskable = false } = {}) {
  const outPath = path.join(iconsDir, outputName);
  const logoSize = maskable ? Math.round(size * 0.62) : Math.round(size * 0.88);

  const logo = await sharp(source)
    .resize(logoSize, logoSize, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer();

  await sharp({
    create: {
      width: size,
      height: size,
      channels: 4,
      background: BRAND_BG,
    },
  })
    .composite([{ input: logo, gravity: "centre" }])
    .png()
    .toFile(outPath);

  console.log(`Wrote ${outputName}`);
}

async function main() {
  await mkdir(iconsDir, { recursive: true });

  await resizeIcon(192, "icon-192.png");
  await resizeIcon(512, "icon-512.png");
  await resizeIcon(512, "icon-512-maskable.png", { maskable: true });
  await resizeIcon(180, "apple-touch-icon.png");

  await sharp(source).resize(32, 32).png().toFile(path.join(root, "public", "favicon-32.png"));
  await sharp(source).resize(16, 16).png().toFile(path.join(root, "public", "favicon-16.png"));

  console.log("Icons generated.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
