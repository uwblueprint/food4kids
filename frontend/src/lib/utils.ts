import { type ClassValue, clsx } from 'clsx';
import { extendTailwindMerge } from 'tailwind-merge';

/**
 * Custom tailwind-merge config for F4K design tokens.
 *
 * Our @theme defines text-h1…h3, text-p1…p3 (font-size tokens) which
 * collide with Tailwind's text-<color> utilities in tailwind-merge's
 * default grouping. Registering them explicitly as font-size classes
 * prevents twMerge from stripping color utilities like text-grey-100.
 *
 * If you add new custom text-* font-size tokens to index.css,
 * add them here too.
 */
const twMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      'font-size': [
        'text-h1',
        'text-h2',
        'text-h3',
        'text-p1',
        'text-p2',
        'text-p3',
        'text-m-h1',
        'text-m-h2',
        'text-m-h3',
        'text-m-p1',
        'text-m-p2',
        'text-m-p3',
      ],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
