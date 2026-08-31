import { describe, expect, it } from 'vitest';

import {
  buttonVariantClasses,
  buttonVariants,
  SELECTED_BUTTON_STROKE,
} from '@/common/components/Button.variants';

/**
 * Design rule: a button on a DARK ground (blue, red) has no stroke; a button on
 * a LIGHT ground (white, grey) has a 1px stroke. Unfilled buttons (transparent
 * ground) have neither a fill nor a stroke.
 */
type Ground = 'dark' | 'light' | 'none';

const GROUND_BY_VARIANT: Record<keyof typeof buttonVariantClasses, Ground> = {
  primary: 'dark',
  destructive: 'dark',
  secondary: 'light',
  tertiary: 'light',
  textLink: 'none',
  ghost: 'none',
};

const SHAPES = ['default', 'circular', 'circularLarge', 'compact'] as const;

/**
 * Tailwind's bare `border` is the 1px stroke; `border-<n>` sets another width
 * and `border-0` removes it. `focus-visible:`/`focus-within:` outlines and
 * rings are focus affordances, not the resting stroke, so they don't count.
 */
function strokeClasses(className: string): string[] {
  return className
    .split(/\s+/)
    .filter(Boolean)
    .filter((token) => !token.includes(':'))
    .filter((token) => token === 'border' || token.startsWith('border-'));
}

function hasOnePixelStroke(className: string): boolean {
  const tokens = strokeClasses(className);
  // A width-bearing token: bare `border`, or `border-2` / `border-0` etc.
  const widths = tokens.filter((t) => t === 'border' || /^border-\d+$/.test(t));
  return widths.length === 1 && widths[0] === 'border';
}

describe('button stroke rule', () => {
  it('classifies every variant the component ships', () => {
    expect(Object.keys(GROUND_BY_VARIANT).sort()).toEqual(
      Object.keys(buttonVariantClasses).sort()
    );
  });

  const variants = Object.keys(
    buttonVariantClasses
  ) as (keyof typeof GROUND_BY_VARIANT)[];

  for (const variant of variants) {
    const ground = GROUND_BY_VARIANT[variant];

    for (const shape of SHAPES) {
      const className = buttonVariants({ variant, shape });

      if (ground === 'dark') {
        it(`${variant}/${shape}: dark ground has no stroke`, () => {
          expect(strokeClasses(className)).toEqual([]);
        });
      } else if (ground === 'light') {
        it(`${variant}/${shape}: light ground has a 1px stroke`, () => {
          expect(hasOnePixelStroke(className)).toBe(true);
          // and a stroke colour, not just a width
          expect(
            strokeClasses(className).some((t) => /^border-[a-z]/.test(t))
          ).toBe(true);
        });
      } else {
        it(`${variant}/${shape}: unfilled button has no stroke`, () => {
          expect(strokeClasses(className)).toEqual([]);
        });
      }
    }
  }

  it('keeps the default variant strokeless (primary is blue)', () => {
    expect(strokeClasses(buttonVariants())).toEqual([]);
  });

  it('does not let a caller className be mistaken for the variant stroke', () => {
    // Sanity check on the helper itself: an explicit override is still seen.
    expect(
      strokeClasses(buttonVariants({ className: 'border border-red' }))
    ).toEqual(['border', 'border-red']);
  });
});

/**
 * Design rule: every filled button carries the same near-white label, so the
 * destructive button reads as a peer of the primary one rather than a tinted
 * special case.
 */
describe('filled button label colour', () => {
  const filled = (
    Object.keys(GROUND_BY_VARIANT) as (keyof typeof GROUND_BY_VARIANT)[]
  ).filter((variant) => GROUND_BY_VARIANT[variant] === 'dark');

  for (const variant of filled) {
    it(`${variant}: label is grey-100`, () => {
      expect(buttonVariantClasses[variant].split(/\s+/)).toContain(
        'text-grey-100'
      );
    });
  }
});

/**
 * The same stroke, applied by hand outside the Button component. The ledger is
 * the guard: a new call site fails until it's listed, and a call site that
 * drops the constant fails too.
 */
describe('SELECTED_BUTTON_STROKE', () => {
  const DEFINITION = '/src/common/components/Button.variants.ts';
  const THIS_TEST = '/src/common/components/Button.variants.test.ts';

  const CALL_SITES = [
    '/src/common/components/Sidebar.tsx',
    '/src/pages/admin/home/components/UnassignedRoutesCard.tsx',
    '/src/pages/driver/home/DriverHomePage.tsx',
  ];

  const sources = Object.entries(
    import.meta.glob<string>('/src/**/*.{ts,tsx}', {
      query: '?raw',
      import: 'default',
      eager: true,
    })
  )
    .filter(([file]) => file !== DEFINITION && file !== THIS_TEST)
    .sort(([a], [b]) => a.localeCompare(b));

  it('is a 1px stroke in the light-ground blue', () => {
    expect(SELECTED_BUTTON_STROKE.split(/\s+/)).toEqual([
      'outline',
      'outline-1',
      'outline-offset-[-1px]',
      'outline-blue-100',
    ]);
  });

  it('finds the source tree to scan', () => {
    expect(sources.length).toBeGreaterThan(50);
  });

  it('is used by exactly the call sites listed here', () => {
    const users = sources
      .filter(([, code]) => code.includes('SELECTED_BUTTON_STROKE'))
      .map(([file]) => file);
    expect(users).toEqual([...CALL_SITES].sort());
  });

  it('is never written out as a literal instead', () => {
    const inlined = sources
      .filter(([, code]) => code.includes('outline-blue-100'))
      .map(([file]) => file);
    expect(inlined).toEqual([]);
  });
});
