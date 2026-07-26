/**
 * The small print under a field on the auth screens — validation errors and the
 * password criteria.
 *
 * 14px at every width, which is why this uses the static `text-m-p3` token
 * rather than the responsive `text-p2`: that one renders 16px on mobile, and no
 * mobile style defines 16px for this. Only the weight varies by breakpoint,
 * because each ramp has its own weight at 14px — Regular on mobile
 * (`Mobile/Paragraph/P3`), SemiBold from tablet up (`Desktop/Paragraph/P2`).
 *
 * `FieldDescription` fills the same role app-wide but still carries `text-p2`.
 * Changing it would move the admin screens too, which are not part of this
 * change and have not been measured against their designs.
 */
export const fieldNote = 'text-m-p3 font-normal tablet:font-semibold';
