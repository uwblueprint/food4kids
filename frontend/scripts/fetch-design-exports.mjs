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

/**
 * Viewports, in tab order. `max` is the app's breakpoint ceiling, used to infer
 * a viewport for sections whose name doesn't announce one (see viewportOf).
 * Keep in sync with --breakpoint-* in src/index.css.
 */
const VIEWPORTS = {
  mobile: { label: 'Mobile', width: 375, max: 499 },
  tablet: { label: 'Tablet', width: 834, max: 1023 },
  desktop: { label: 'Desktop', width: 1440, max: Infinity },
};

/**
 * Sections are named "<Viewport> - <Flow>", e.g. "Mobile - Drivers Screens".
 * Every section on the page is pulled by default so one fetch covers every
 * flow; narrow with `--sections <regex>`.
 */
const DEFAULT_SECTION_PATTERN = /./;

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

/**
 * Some sections name every frame "Desktop (2)" / "Tablet (7)", which is both
 * useless in the picker and impossible to key a route off. These override by
 * frame id (`<flow>/<viewport>/<slug>`) and win over ROUTES.
 *
 * Identify a frame by opening public/design-exports/<id>.png.
 */
const BY_ID = {
  // PR #211 — driver individual route page
  'drivers-screen/mobile/routes-individual-driver': {
    label: 'Individual Route',
    route: '/driver/route',
  },
  'drivers-screen/tablet/tablet-2': {
    label: 'Individual Route',
    route: '/driver/route',
  },
  'drivers-screen/desktop/desktop-2': {
    label: 'Individual Route',
    route: '/driver/route',
  },
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

/**
 * Viewport for a section: from its name prefix when it has one, else inferred
 * from the frame width against the app's breakpoints.
 */
function viewportOf(sectionName, frameWidth) {
  const named = Object.keys(VIEWPORTS).find((v) =>
    sectionName.toLowerCase().startsWith(v)
  );
  if (named) return named;
  return (
    Object.keys(VIEWPORTS).find((v) => frameWidth <= VIEWPORTS[v].max) ??
    'desktop'
  );
}

/**
 * Flow for a section: its name with any "<Viewport> - " prefix stripped.
 * Returns a grouping key plus the label to show. The key ignores a trailing
 * "s" because the sections are named inconsistently — "Mobile - Drivers
 * Screens" vs "Desktop - Drivers Screen" are the same flow.
 */
function flowOf(sectionName) {
  const label = sectionName
    .replace(new RegExp(`^(${Object.keys(VIEWPORTS).join('|')})\\s*-\\s*`, 'i'), '')
    .replace(/\s+/g, ' ')
    .trim();
  return { key: label.toLowerCase().replace(/s$/, ''), label };
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

  const sectionArg = process.argv[process.argv.indexOf('--sections') + 1];
  const sectionPattern =
    process.argv.includes('--sections') && sectionArg
      ? new RegExp(sectionArg, 'i')
      : DEFAULT_SECTION_PATTERN;

  const sections = (page.children ?? []).filter(
    (n) => n.type === 'SECTION' && sectionPattern.test(n.name)
  );
  if (sections.length === 0) {
    throw new Error(
      `No SECTION matching ${sectionPattern} on page "${page.name}". ` +
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
  const flows = new Map();
  for (const section of sections) {
    const flow = flowOf(section.name);
    flows.set(flow.key, flow.label);
    const children = detail.nodes[section.id].document.children ?? [];
    const seen = new Map();
    for (const frame of children) {
      if (frame.type !== 'FRAME') continue;
      // Figma names carry stray whitespace; trim before matching anything.
      const name = frame.name.trim().replace(/\s+/g, ' ');
      if (SKIP_FRAMES.some((re) => re.test(name))) continue;

      const viewport = viewportOf(
        section.name,
        frame.absoluteBoundingBox?.width ?? 0
      );

      // Figma allows duplicate frame names; disambiguate so files don't collide.
      const n = (seen.get(name) ?? 0) + 1;
      seen.set(name, n);
      const slug = slugify(name) + (n > 1 ? `-${n}` : '');

      const box = frame.absoluteBoundingBox ?? {};
      // Flow-qualified so the same frame name in two flows can't collide.
      const id = `${slugify(flow.key)}/${viewport}/${slug}`;
      const override = BY_ID[id] ?? {};

      const route = override.route ?? ROUTES[name] ?? null;
      if (!route) unmapped.push(id);

      frames.push({
        id,
        nodeId: frame.id,
        label: override.label ?? name + (n > 1 ? ` (${n})` : ''),
        flow: flow.key,
        viewport,
        route,
        width: Math.round(box.width ?? VIEWPORTS[viewport].width),
        height: Math.round(box.height ?? 0),
        image: `/design-exports/${id}.png`,
      });
    }
  }
  // `--reuse-images` re-derives the manifest from frames already on disk, for
  // when only the label/route tables changed. Re-renders anything missing.
  const reuse = process.argv.includes('--reuse-images');
  const onDisk = new Set();
  if (reuse) {
    await Promise.all(
      frames.map(async (f) => {
        try {
          await fs.access(path.join(OUT_DIR, `${f.id}.png`));
          onDisk.add(f.nodeId);
        } catch {
          /* needs rendering */
        }
      })
    );
  }
  const toRender = frames.filter((f) => !onDisk.has(f.nodeId));
  console.log(
    `Exporting ${frames.length} frames` +
      (reuse ? ` (${onDisk.size} reused, ${toRender.length} to render)` : '') +
      ' …'
  );

  // Figma caps the ids per image request; batch conservatively.
  const urls = {};
  const BATCH = 20;
  for (let i = 0; i < toRender.length; i += BATCH) {
    const batch = toRender.slice(i, i + BATCH);
    const res = await figma(
      token,
      `${API}/images/${fileKey}?ids=${batch
        .map((f) => encodeURIComponent(f.nodeId))
        .join(',')}&format=png&scale=2`
    );
    if (res.err) throw new Error(`Figma image render failed: ${res.err}`);
    Object.assign(urls, res.images);
  }

  // A full run starts clean so frames deleted in Figma don't linger.
  if (!reuse) await fs.rm(OUT_DIR, { recursive: true, force: true });

  let written = 0;
  for (const frame of toRender) {
    const url = urls[frame.nodeId];
    if (!url) throw new Error(`Figma returned no image for ${frame.label}`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Download failed for ${frame.label}: ${res.status}`);
    const dest = path.join(OUT_DIR, `${frame.id}.png`);
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.writeFile(dest, Buffer.from(await res.arrayBuffer()));
    written += 1;
    process.stdout.write(`\r  ${written}/${toRender.length}`);
  }
  process.stdout.write('\n');

  const manifest = {
    fileKey,
    fileName: file.name,
    fetchedAt: new Date().toISOString(),
    viewports: VIEWPORTS,
    flows: Object.fromEntries([...flows].map(([key, label]) => [key, { label }])),
    frames: frames.sort(
      (a, b) =>
        a.flow.localeCompare(b.flow) ||
        Object.keys(VIEWPORTS).indexOf(a.viewport) -
          Object.keys(VIEWPORTS).indexOf(b.viewport) ||
        a.label.localeCompare(b.label)
    ),
  };
  await fs.writeFile(
    path.join(OUT_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2)
  );

  console.log(
    `\nWrote ${written} new + ${frames.length - written} reused frames ` +
      `and manifest.json to public/design-exports/`
  );
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
