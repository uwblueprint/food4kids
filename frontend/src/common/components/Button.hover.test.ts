import { type VariantProps } from 'class-variance-authority';
import { describe, expect, it } from 'vitest';

import { buttonVariants } from './Button.variants';

type VariantName = NonNullable<VariantProps<typeof buttonVariants>['variant']>;
type ShapeName = NonNullable<VariantProps<typeof buttonVariants>['shape']>;

/* Every button variant must give hover feedback — one that renders identically
 * at rest and on hover reads as non-interactive. Figma spells the states out as
 * `Type=<variant>, State=Hover` on the Button and Circular Button sets. Typing
 * this as a total Record makes tsc fail when a variant is added but not
 * classified here. */
const HOVER_CLASSES: Record<VariantName, string[]> = {
  primary: ['hover:bg-blue-400'],
  secondary: ['hover:bg-grey-300'],
  // Figma keeps tertiary's fill and stroke and adds only the shadow.
  tertiary: ['hover:shadow-light'],
  textLink: ['hover:underline'],
  ghost: ['hover:bg-grey-200'],
  destructive: ['hover:opacity-90'],
};

const SHAPE_CLASSES: Record<ShapeName, true> = {
  default: true,
  circular: true,
  circularLarge: true,
  compact: true,
};

const VARIANTS = Object.keys(HOVER_CLASSES) as VariantName[];
const SHAPES = Object.keys(SHAPE_CLASSES) as ShapeName[];

function hoverClassesFor(variant: VariantName, shape?: ShapeName): string[] {
  return buttonVariants({ variant, ...(shape ? { shape } : {}) })
    .split(/\s+/)
    .filter((c) => c.startsWith('hover:'));
}

describe('buttonVariants hover states', () => {
  it.each(VARIANTS)('%s emits at least one hover: utility', (variant) => {
    expect(hoverClassesFor(variant).length).toBeGreaterThan(0);
  });

  it.each(VARIANTS)('%s emits exactly its Figma hover utilities', (variant) => {
    expect(hoverClassesFor(variant).sort()).toEqual(
      [...HOVER_CLASSES[variant]].sort()
    );
  });

  it.each(VARIANTS)(
    '%s keeps its hover utilities in every shape',
    (variant) => {
      for (const shape of SHAPES) {
        expect(hoverClassesFor(variant, shape).sort()).toEqual(
          [...HOVER_CLASSES[variant]].sort()
        );
      }
    }
  );

  it('tertiary hover changes neither fill nor stroke', () => {
    const hover = hoverClassesFor('tertiary');
    expect(hover.some((c) => c.startsWith('hover:bg-'))).toBe(false);
    expect(hover.some((c) => c.startsWith('hover:border'))).toBe(false);
  });

  it('no variant relies on a colour shift the disabled state would keep', () => {
    // disabled:pointer-events-none means hover never fires when disabled; the
    // base must carry it so a variant can't opt out.
    expect(buttonVariants({ variant: 'tertiary' })).toContain(
      'disabled:pointer-events-none'
    );
  });
});
