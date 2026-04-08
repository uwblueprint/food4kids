// extract-tokens.ts
import { readFileSync, writeFileSync } from 'node:fs';

const css = readFileSync('./src/index.css', 'utf-8');

const themeMatch = css.match(/@theme\s*\{([\s\S]*?)\n\}/);

if (!themeMatch) {
  throw new Error('No @theme block found in index.css');
}

const lines = themeMatch[1].trim().split('\n');

const flatColors: Record<string, string> = {};
const fontFamily: Record<string, string[]> = {};
const fontSize: Record<string, [string, { lineHeight: string }]> = {};
const boxShadow: Record<string, string> = {};
const spacing: Record<string, string> = {};

for (const line of lines) {
  const match = line.match(/^\s*--([\w-]+):\s*(.+?);/);
  if (!match) continue;

  const [, key, value] = match;

  if (key.endsWith('--line-height')) continue;

  if (key.startsWith('color-')) {
    flatColors[key.replace('color-', '')] = value;
  } else if (key.startsWith('font-')) {
    const name = key.replace('font-', '');
    fontFamily[name] = value.split(',').map((f) => f.trim());
  } else if (key.startsWith('text-')) {
    const name = key.replace('text-', '');
    const lhKey = `--${key}--line-height`;
    const lhMatch = themeMatch[1].match(
      new RegExp(`${lhKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:\\s*(.+?);`)
    );
    const lineHeight = lhMatch ? lhMatch[1].trim() : '1.5';
    fontSize[name] = [value, { lineHeight }];
  } else if (key.startsWith('shadow-')) {
    boxShadow[key.replace('shadow-', '')] = value;
  } else if (key.startsWith('spacing-')) {
    spacing[key.replace('spacing-', '')] = value;
  }
}

// ── Nest colors that share a prefix ──
// e.g. "grey-100", "grey-200" → grey: { 100: "...", 200: "..." }
// e.g. "brand-green", "brand-pink" → brand: { green: "...", pink: "..." }
// e.g. "red" (no dash-suffix with a nestable group) → stays flat
function nestColors(
  flat: Record<string, string>
): Record<string, string | Record<string, string>> {
  const groups: Record<string, Record<string, string>> = {};
  const standalone: Record<string, string> = {};

  // First pass: figure out which prefixes have multiple entries
  const prefixCounts: Record<string, number> = {};
  for (const key of Object.keys(flat)) {
    const dashIndex = key.indexOf('-');
    if (dashIndex === -1) {
      // No dash at all, e.g. "red"
      standalone[key] = flat[key];
      continue;
    }
    const prefix = key.substring(0, dashIndex);
    prefixCounts[prefix] = (prefixCounts[prefix] || 0) + 1;
  }

  // Second pass: nest groups with 2+ entries, keep the rest flat
  for (const key of Object.keys(flat)) {
    const dashIndex = key.indexOf('-');
    if (dashIndex === -1) continue; // already handled

    const prefix = key.substring(0, dashIndex);
    const suffix = key.substring(dashIndex + 1);

    if (prefixCounts[prefix] >= 2) {
      if (!groups[prefix]) groups[prefix] = {};
      groups[prefix][suffix] = flat[key];
    } else {
      standalone[key] = flat[key];
    }
  }

  // Merge and sort alphabetically
  const result: Record<string, string | Record<string, string>> = {};
  const allKeys = [...Object.keys(groups), ...Object.keys(standalone)].sort();

  for (const k of allKeys) {
    if (groups[k]) {
      result[k] = sortObj(groups[k]);
    } else {
      result[k] = standalone[k];
    }
  }

  return result;
}

// ── Sort an object's keys alphabetically ──
function sortObj<T>(obj: Record<string, T>): Record<string, T> {
  return Object.fromEntries(
    Object.entries(obj).sort(([a], [b]) => a.localeCompare(b))
  );
}

const colors = nestColors(flatColors);

const config = {
  theme: {
    extend: {
      colors,
      fontFamily: sortObj(fontFamily),
      fontSize: sortObj(fontSize),
      boxShadow: sortObj(boxShadow),
      spacing: sortObj(spacing),
    },
  },
};

writeFileSync(
  './emails/email-tailwind-config.ts',
  `// Auto-generated from index.css @theme block\n// Run: pnpm tsx extract-tokens.ts\n\nexport const emailTailwindConfig = ${JSON.stringify(config, null, 2)} as const;\n`
);

console.log(
  `Extracted: ${Object.keys(flatColors).length} colors (${Object.keys(nestColors(flatColors)).length} groups), ${Object.keys(fontSize).length} text sizes, ${Object.keys(fontFamily).length} fonts, ${Object.keys(boxShadow).length} shadows`
);