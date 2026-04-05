// extract-tokens.ts
import { readFileSync, writeFileSync } from 'node:fs';

const css = readFileSync('./src/index.css', 'utf-8');

// Extract the first @theme block (your F4K design system tokens)
const themeMatch = css.match(/@theme\s*\{([\s\S]*?)\n\}/);

if (!themeMatch) {
  throw new Error('No @theme block found in index.css');
}

const lines = themeMatch[1].trim().split('\n');

const colors: Record<string, string> = {};
const fontFamily: Record<string, string[]> = {};
const fontSize: Record<string, [string, { lineHeight: string }]> = {};
const boxShadow: Record<string, string> = {};
const spacing: Record<string, string> = {};

for (const line of lines) {
  const match = line.match(/^\s*--([\w-]+):\s*(.+?);/);
  if (!match) continue;

  const [, key, value] = match;

  // Skip line-height entries — they get consumed by their parent text token
  if (key.endsWith('--line-height')) continue;

  // Colors: --color-*
  if (key.startsWith('color-')) {
    const name = key.replace('color-', '');
    colors[name] = value;
  }

  // Fonts: --font-*
  else if (key.startsWith('font-')) {
    const name = key.replace('font-', '');
    fontFamily[name] = value.split(',').map((f) => f.trim().replace(/'/g, ''));
  }

  // Typography: --text-* (pair with --text-*--line-height)
  else if (key.startsWith('text-')) {
    const name = key.replace('text-', '');
    const lhKey = `--${key}--line-height`;
    const lhMatch = themeMatch[1].match(
      new RegExp(`${lhKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}:\\s*(.+?);`)
    );
    const lineHeight = lhMatch ? lhMatch[1].trim() : '1.5';
    fontSize[name] = [value, { lineHeight }];
  }

  // Shadows: --shadow-*
  else if (key.startsWith('shadow-')) {
    const name = key.replace('shadow-', '');
    boxShadow[name] = value;
  }

  // Spacing: --spacing-*
  else if (key.startsWith('spacing-')) {
    const name = key.replace('spacing-', '');
    spacing[name] = value;
  }
}

const config = {
  theme: {
    extend: {
      colors,
      fontFamily,
      fontSize,
      boxShadow,
      spacing,
    },
  },
};

writeFileSync(
  './email-tailwind-config.ts',
  `// Auto-generated from index.css @theme block\n// Run: npx tsx extract-tokens.ts\n\nexport const emailTailwindConfig = ${JSON.stringify(config, null, 2)} as const;\n`
);

console.log(
  `Extracted: ${Object.keys(colors).length} colors, ${Object.keys(fontSize).length} text sizes, ${Object.keys(fontFamily).length} fonts, ${Object.keys(boxShadow).length} shadows`
);
