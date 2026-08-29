import { describe, expect, it } from 'vitest';

import {
  buttonVariantClasses,
  buttonVariants,
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
