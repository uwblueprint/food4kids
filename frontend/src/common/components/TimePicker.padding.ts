/** The side-padding values the design system uses for dropdown triggers. */
export type TimePickerPadding = 12 | 24;

const PX_CLASSES: Record<TimePickerPadding, string> = {
  12: 'px-3',
  24: 'px-6',
};

/**
 * Side padding for one {@link TimePicker}. A dropdown's left padding follows
 * the button it opens from, so the two contexts differ: 12 in the
 * route-generation table, 24 in Settings.
 *
 * The trigger and the panel's options take the *same* class, which is what
 * puts an option's text at the same x as the trigger's text. Both boxes share
 * an origin: the trigger's ring is an `outline` drawn `outline-offset-[-1px]`
 * inwards and outlines take no layout space, so its text sits at exactly this
 * padding from its border box, and `align="start"` puts the panel's
 * border-less left edge on that same box. The designs agree — route
 * generation's trigger and menu row are both `paddingLeft: 12`, Settings'
 * both 24.
 */
export function timePickerPaddingClass(padding: TimePickerPadding): string {
  const className = PX_CLASSES[padding];
  if (!className) {
    throw new Error(`No Tailwind padding class for ${padding}px`);
  }
  return className;
}
