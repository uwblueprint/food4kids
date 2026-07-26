/**
 * The small print under a field on the auth screens — validation errors and the
 * password criteria.
 *
 * 14px SemiBold at every width, which is why this uses the static `text-m-p3`
 * token rather than the responsive `text-p2`: that one renders 16px on mobile,
 * and no mobile style defines 16px for this.
 *
 * The weight is flat across breakpoints. An earlier version of this token split
 * it — Regular on mobile, SemiBold from tablet up — reading the weight off the
 * ramp each size belongs to (`Mobile/Paragraph/P3` is Regular). That was
 * reading the wrong thing: every frame that renders this text sets Nunito Sans
 * 600 explicitly, at all three viewports, for both the criteria list and the
 * error rows. The ramp says what P3 is in general; the frames say what this
 * text is, and the frames win.
 *
 * `FieldDescription` fills the same role app-wide but still carries `text-p2`.
 * Changing it would move the admin screens too, which are not part of this
 * change and have not been measured against their designs.
 */
export const fieldNote = 'text-m-p3 font-semibold';
