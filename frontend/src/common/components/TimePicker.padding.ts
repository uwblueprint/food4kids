/** The side-padding values the design system uses for dropdown triggers. */
export type TimePickerPadding = 12 | 24;

/**
 * How much of the option's inset the option itself already supplies: the
 * `px-3` on an option pill. The panel makes up only the difference.
 */
const OPTION_OWN_INSET_PX = 12;

const PX_CLASSES: Record<number, string> = {
  0: 'px-0',
  12: 'px-3',
  24: 'px-6',
};

export interface TimePickerPaddingClasses {
  /** Side padding of the closed trigger. */
  trigger: string;
  /** Side padding of the open panel. */
  panel: string;
}

/**
 * Trigger and panel padding for a given trigger padding, chosen so an option's
 * text lands at the same x as the trigger's text.
 *
 * The two edges line up because neither box adds anything of its own: the
 * trigger's ring is an `outline` drawn `outline-offset-[-1px]` inwards, and
 * outlines never take layout space, so its text sits at exactly `padding` from
 * the border box. `align="start"` then puts the panel's (border-less) left edge
 * on that same border box. Inside the panel the option pill contributes its own
 * `px-3`, so the panel supplies `padding - 12`.
 *
 * This only holds while the option's text is left-aligned in its pill. The
 * pills are `min-w-12` and every label is narrower than that, so centering them
 * would float the text right by half the leftover width — a different offset
 * for "9" than for "12", which is why no single panel padding could line them
 * up before.
 */
export function timePickerPaddingClasses(
  padding: TimePickerPadding
): TimePickerPaddingClasses {
  const panelPx = padding - OPTION_OWN_INSET_PX;
  const trigger = PX_CLASSES[padding];
  const panel = PX_CLASSES[panelPx];
  if (!trigger || !panel) {
    throw new Error(
      `No Tailwind padding class for trigger ${padding}px / panel ${panelPx}px`
    );
  }
  return { trigger, panel };
}
