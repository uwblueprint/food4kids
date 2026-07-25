/**
 * Dev-only: pull the auth-flow design frames out of Figma into
 * `public/design-exports/` so the overlay harness (/dev/overlay) can switch
 * between screens and viewports without hand-pasting images.
 *
 * Usage:
 *   pnpm run design:fetch -- <figma-file-key-or-url>
 *
 * Token: $FIGMA_TOKEN, else ~/.config/figma/credentials.json {"token": "figd_…"}.
 *
 * Exports are gitignored — design PNGs never enter the repo.
 */

import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const OUT_DIR = path.resolve(import.meta.dirname, '../public/design-exports');
const API = 'https://api.figma.com/v1';

/** Sections to pull, keyed by the viewport prefix in their Figma name. */
const VIEWPORTS = {
  mobile: { label: 'Mobile', width: 375 },
  tablet: { label: 'Tablet', width: 834 },
  desktop: { label: 'Desktop', width: 1440 },
};

/** Only sections whose name matches this are pulled. */
const SECTION_PATTERN = /log in/i;

/**
 * The file carries older copies of these sections on other pages, so scope to
 * the canonical page. Override with `--page <name>`.
 */
const DEFAULT_PAGE_PATTERN = /finalized/i;

/** Frames that are exploration or annotation, not screens to review. */
const SKIP_FRAMES = [/^Developer Notes$/, /^Could do sum like$/];

/**
 * Frame name → app route. Exact names, because a fuzzy match here silently
 * points the overlay at the wrong screen, which is worse than no route at all.
 * Unmapped frames are exported with route: null and reported at the end.
 */
const DEMO_TOKEN = '00000000-0000-4000-8000-000000000000';
const ROUTES = {
  // Mobile + Tablet sections
  'Login | Admin': '/login',
  'Login | Error': '/login',
  'No Account Yet | Get Link': '/login',
  'Forgot Password': '/forgot-password',
  'Forgot Password Link Sent': '/forgot-password',
  'Resend Link': '/forgot-password',
  'Creation Link Sent': '/forgot-password',
  'Driver | Create Password': `/create-password/${DEMO_TOKEN}`,
  'Driver | Create Password Filled': `/create-password/${DEMO_TOKEN}`,
  'Account Created': `/create-password/${DEMO_TOKEN}`,
  // Desktop section
  'Default Log In - All Users': '/login',
  'Default Login - All Users': '/login',
  'Default Log In - Error States': '/login',
  'No Account Yet - Get Login Link': '/login',
  'Redo Log in Driver': '/login',
  'Forgot Password | Driver Create Password Section': '/forgot-password',
  'First Time Login - Driver - Through Invite link': `/create-password/${DEMO_TOKEN}`,
  'First Time Login - Criteria Not Met': `/create-password/${DEMO_TOKEN}`,
  "First Time Login - Passwords Don't Match": `/create-password/${DEMO_TOKEN}`,
  'First Time Login - Empty State': `/create-password/${DEMO_TOKEN}`,
  'Create Password - New Drivers': `/create-password/${DEMO_TOKEN}`,
};

async function readToken() {
  if (process.env.FIGMA_TOKEN) return process.env.FIGMA_TOKEN;
  const file = path.join(os.homedir(), '.config/figma/credentials.json');
  const raw = await fs.readFile(file, 'utf8').catch(() => {
    throw new Error(`No $FIGMA_TOKEN and could not read ${file}`);
  });
  const { token } = JSON.parse(raw);
  if (!token) throw new Error(`${file} has no "token" field`);
  return token;
}

/** Accepts a bare key or any figma.com/{design,file}/<key>/… URL. */
function parseFileKey(input) {
  if (!input) {
    throw new Error(
      'Missing Figma file key.\n' +
        '  pnpm run design:fetch -- https://www.figma.com/design/<key>/<name>'
    );
  }
  const url = input.match(/figma\.com\/(?:design|file)\/([A-Za-z0-9]+)/);
  return url ? url[1] : input;
}

async function figma(token, url) {
  const res = await fetch(url, { headers: { 'X-Figma-Token': token } });
  if (!res.ok) {
    throw new Error(`Figma ${res.status} ${res.statusText} for ${url}`);
  }
  return res.json();
}

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

function viewportOf(sectionName) {
  const key = Object.keys(VIEWPORTS).find((v) =>
    sectionName.toLowerCase().startsWith(v)
  );
  if (!key) {
    throw new Error(
      `Section "${sectionName}" does not start with a known viewport ` +
        `(${Object.keys(VIEWPORTS).join(', ')}). Rename it or extend VIEWPORTS.`
    );
  }
  return key;
}

async function main() {
  const token = await readToken();
  // `pnpm run x -- <arg>` forwards the `--` too, so skip it.
  const fileKey = parseFileKey(process.argv.slice(2).find((a) => a !== '--'));

  console.log(`Reading file ${fileKey} …`);
  // depth=2 → pages and their direct children (the sections), no frame internals.
  const file = await figma(token, `${API}/files/${fileKey}?depth=2`);

  const pageArg = process.argv[process.argv.indexOf('--page') + 1];
  const pagePattern =
    process.argv.includes('--page') && pageArg
      ? new RegExp(pageArg, 'i')
      : DEFAULT_PAGE_PATTERN;

  const pages = file.document.children.filter((p) => pagePattern.test(p.name));
  if (pages.length !== 1) {
    throw new Error(
      `Expected exactly one page matching ${pagePattern}, got ${pages.length}.\n` +
        `Pages in "${file.name}": ${file.document.children
          .map((p) => p.name)
          .join(', ')}\n` +
        `Pass --page <name> to pick one.`
    );
  }
  const page = pages[0];

  const sections = (page.children ?? []).filter(
    (n) => n.type === 'SECTION' && SECTION_PATTERN.test(n.name)
  );
  if (sections.length === 0) {
    throw new Error(
      `No SECTION matching ${SECTION_PATTERN} on page "${page.name}". ` +
        `Sections there: ${(page.children ?? [])
          .filter((c) => c.type === 'SECTION')
          .map((c) => c.name)
          .join(', ')}`
    );
  }
  console.log(
    `Page "${page.name}" → sections: ${sections.map((s) => s.name).join(', ')}`
  );

  // Section children come back empty at depth=2, so fetch each section's frames.
  const ids = sections.map((s) => s.id).join(',');
  const detail = await figma(
    token,
    `${API}/files/${fileKey}/nodes?ids=${encodeURIComponent(ids)}&depth=1`
  );

  const frames = [];
  const unmapped = [];
  for (const section of sections) {
    const viewport = viewportOf(section.name);
    const children = detail.nodes[section.id].document.children ?? [];
    const seen = new Map();
    for (const frame of children) {
      if (frame.type !== 'FRAME') continue;
      // Figma names carry stray whitespace; trim before matching anything.
      const name = frame.name.trim().replace(/\s+/g, ' ');
      if (SKIP_FRAMES.some((re) => re.test(name))) continue;

      // Figma allows duplicate frame names; disambiguate so files don't collide.
      const n = (seen.get(name) ?? 0) + 1;
      seen.set(name, n);
      const slug = slugify(name) + (n > 1 ? `-${n}` : '');

      const route = ROUTES[name] ?? null;
      if (!route) unmapped.push(`${viewport}/${name}`);

      const box = frame.absoluteBoundingBox ?? {};
      frames.push({
        id: `${viewport}/${slug}`,
        nodeId: frame.id,
        label: name + (n > 1 ? ` (${n})` : ''),
        viewport,
        route,
        width: Math.round(box.width ?? VIEWPORTS[viewport].width),
        height: Math.round(box.height ?? 0),
        image: `/design-exports/${viewport}/${slug}.png`,
      });
    }
  }
  console.log(`Exporting ${frames.length} frames …`);

  // Figma caps the ids per image request; batch conservatively.
  const urls = {};
  const BATCH = 20;
  for (let i = 0; i < frames.length; i += BATCH) {
    const batch = frames.slice(i, i + BATCH);
    const res = await figma(
      token,
      `${API}/images/${fileKey}?ids=${batch
        .map((f) => encodeURIComponent(f.nodeId))
        .join(',')}&format=png&scale=2`
    );
    if (res.err) throw new Error(`Figma image render failed: ${res.err}`);
    Object.assign(urls, res.images);
  }

  await fs.rm(OUT_DIR, { recursive: true, force: true });
  for (const viewport of Object.keys(VIEWPORTS)) {
    await fs.mkdir(path.join(OUT_DIR, viewport), { recursive: true });
  }

  let written = 0;
  for (const frame of frames) {
    const url = urls[frame.nodeId];
    if (!url) throw new Error(`Figma returned no image for ${frame.label}`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Download failed for ${frame.label}: ${res.status}`);
    const dest = path.join(OUT_DIR, `${frame.id}.png`);
    await fs.writeFile(dest, Buffer.from(await res.arrayBuffer()));
    written += 1;
    process.stdout.write(`\r  ${written}/${frames.length}`);
  }
  process.stdout.write('\n');

  const manifest = {
    fileKey,
    fileName: file.name,
    fetchedAt: new Date().toISOString(),
    viewports: VIEWPORTS,
    frames: frames.sort(
      (a, b) =>
        Object.keys(VIEWPORTS).indexOf(a.viewport) -
          Object.keys(VIEWPORTS).indexOf(b.viewport) ||
        a.label.localeCompare(b.label)
    ),
  };
  await fs.writeFile(
    path.join(OUT_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2)
  );

  console.log(`\nWrote ${written} frames + manifest.json to public/design-exports/`);
  if (unmapped.length) {
    console.log(
      `\n${unmapped.length} frame(s) have no route mapping — pick a route in the ` +
        `harness UI, or add them to ROUTES in this script:\n  ` +
        unmapped.join('\n  ')
    );
  }
  console.log('\nOpen http://localhost:3000/dev/overlay');
}

main().catch((err) => {
  console.error(`\n${err.message}`);
  process.exit(1);
});
