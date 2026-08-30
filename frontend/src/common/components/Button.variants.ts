import { cva } from 'class-variance-authority';

/* Stroke rule (design, platform-wide): a filled button on a DARK ground
 * (blue, red) carries no stroke; one on a LIGHT ground (white, grey) carries a
 * 1px stroke. Unfilled variants (textLink, ghost) have no ground and so no
 * stroke either. Exported so Button.variants.test.ts can hold every variant to
 * the rule — a new variant fails the test until it's classified there. */
export const buttonVariantClasses = {
  primary: 'bg-blue-300 text-grey-100 hover:bg-blue-400',
  secondary:
    'bg-grey-200 text-grey-500 border border-grey-300 hover:bg-grey-300',
  tertiary: 'bg-grey-100 text-grey-500 border border-grey-300',
  textLink: 'bg-transparent text-blue-300 hover:underline',
  ghost: 'bg-transparent text-grey-500 hover:bg-grey-200',
  destructive: 'bg-red text-grey-100 hover:opacity-90',
} as const;

export const buttonVariants = cva(
  /* ---- shared base ---- */
  [
    'inline-flex items-center justify-center gap-2',
    'transition-colors duration-150 ease-in-out',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300',
    'disabled:pointer-events-none disabled:opacity-50',
    'cursor-pointer',
    '[&_svg]:pointer-events-none [&_svg]:shrink-0',
  ],
  {
    variants: {
      variant: buttonVariantClasses,
      shape: {
        default: [
          'font-nunito text-button', // UI/Button: Nunito 16/20, constant

          'h-[44px] min-w-[104px] px-6 py-2 rounded-[40px]',
          'w-full tablet:w-auto',
        ],
        /* 40px on mobile, 44px from tablet up (per CTA design frame) */
        circular: 'size-[40px] tablet:size-[44px] rounded-full',
        /* The top bar's own icon button, drawn at 48 on every admin frame —
         * larger than the 44 the table toolbars use. */
        circularLarge: 'size-12 rounded-full',
        /* In-table action pill (the Routes tab's "Assign"): 34px tall with
         * 16px sides and a 14/18 SemiBold body-font label, per the Routes
         * design frame. Sized to its label — it sits inside a cell, so it
         * neither reserves a minimum width nor goes full-width on mobile. */
        compact: 'text-p2 h-[34px] rounded-full px-4 font-nunito font-medium',
      },
    },
    compoundVariants: [
      /* textLink doesn't need pill sizing — reset padding, width, and radius.
       * `leading-6` matches Figma's Text Link (16/24); the pill's own 20 would
       * leave the link shorter than the heading it sits beside. */
      {
        variant: 'textLink',
        shape: 'default',
        className: 'min-w-0 p-0 rounded-none w-auto h-auto leading-6',
      },
    ],
    defaultVariants: {
      variant: 'primary',
      shape: 'default',
    },
  }
);
