/**
 * Option list and formatting for {@link TimePicker}.
 *
 * Both designs model the picker as one scrollable list of whole times on a
 * half-hour step — Settings' "At what time?" lists 8:30 / 9:00 / 9:30, route
 * generation's Start Time lists 9:00 / 9:30 / 10:00 — so the step is shared
 * rather than a per-call-site prop.
 */

/** Minutes between consecutive options. */
const STEP_MINUTES = 30;

const MINUTES_IN_DAY = 24 * 60;

/** A 24-hour "HH:MM" time. */
const HH_MM = /^([01]\d|2[0-3]):([0-5]\d)$/;

function assertTime(value: string): void {
  if (!HH_MM.test(value)) {
    throw new Error(
      `Expected a 24-hour "HH:MM" time, got ${JSON.stringify(value)}`
    );
  }
}

function toHhMm(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/**
 * Every half hour of the day, plus `current` when it does not fall on the
 * step. Route generation's start times are staggered per route, so a stored
 * value like 8:45 has to stay selectable and stay visible as the selection —
 * the designs show exactly that: 8:45 and 10:05 sitting in the same column
 * whose menu offers half hours.
 */
export function timeOptions(current?: string): string[] {
  const options: string[] = [];
  for (let m = 0; m < MINUTES_IN_DAY; m += STEP_MINUTES) {
    options.push(toHhMm(m));
  }
  if (current === undefined) return options;
  assertTime(current);
  if (options.includes(current)) return options;
  // Zero-padded HH:MM sorts lexicographically in chronological order.
  return [...options, current].sort();
}

/** Renders a 24-hour "HH:MM" as the 12-hour form the trigger and list show. */
export function formatDisplayTime(value: string): string {
  assertTime(value);
  const [hours, minutes] = value.split(':');
  const h = Number(hours);
  const period = h >= 12 ? 'PM' : 'AM';
  const hour = h % 12 === 0 ? 12 : h % 12;
  return `${hour}:${minutes} ${period}`;
}

interface CenteredScrollArgs {
  /** Offset of the selected option from the top of the scrolling content. */
  optionTop: number;
  optionHeight: number;
  /** Visible height of the scrolling box. */
  viewportHeight: number;
  /** Total height of the scrolling content. */
  contentHeight: number;
}

/**
 * Where to scroll so the selected option sits in the middle of the list.
 *
 * Clamped at both ends, which is what makes the first and last options behave:
 * there is nothing to scroll past, so they settle flush at the top or bottom
 * rather than leaving the list blank.
 */
export function centeredScrollTop({
  optionTop,
  optionHeight,
  viewportHeight,
  contentHeight,
}: CenteredScrollArgs): number {
  const centered = optionTop - (viewportHeight - optionHeight) / 2;
  const furthest = Math.max(0, contentHeight - viewportHeight);
  return Math.min(Math.max(centered, 0), furthest);
}
