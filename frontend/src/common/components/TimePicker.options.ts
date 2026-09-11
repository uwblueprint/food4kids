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

/**
 * A time as typed into the trigger. Deliberately forgiving wherever the intent
 * is unambiguous — `9`, `09`, `9:00`, `9am`, `9 AM`, `9 a.m.` are all 09:00 —
 * because the field displays "9:00 AM" and never tells the user which shapes
 * it accepts. Hour and minute may each be one or two digits, the separator and
 * the meridiem are optional, and the meridiem may be spaced, capitalised or
 * dotted however the user likes.
 */
const TYPED = /^(\d{1,2})(?::(\d{1,2}))?\s*(?:([ap])\.?\s*(?:m\.?)?)?$/i;

/** The delivery day a bare hour is assumed to fall in: 08:00 to 19:59. */
const DAY_START_HOUR = 8;

/**
 * Resolves a bare hour into the delivery day, which is when these times
 * actually happen: 8 through 12 are morning, 1 through 7 are afternoon. 13 to
 * 23 already say which half they mean, and 0 has only the one reading.
 */
function assumeDeliveryDay(hour: number): number {
  return hour >= 1 && hour < DAY_START_HOUR ? hour + 12 : hour;
}

/**
 * Reads a typed time, or null when it cannot be read.
 *
 * **Without a meridiem the hour is taken to be in the delivery day**, 08:00 to
 * 19:59, so `9` is 09:00 and `1` is 13:00. An explicit meridiem always wins, so
 * `1am` is still 01:00, and the trigger redisplays what was understood either
 * way.
 *
 * Any time of day is accepted, not only times on the half-hour step — route
 * start times are staggered, and the designs show 8:45 and 10:05 sitting in
 * this very field.
 */
export function parseTypedTime(raw: string): string | null {
  const match = TYPED.exec(raw.trim());
  if (!match) return null;

  const hour = Number(match[1]);
  const minute = match[2] === undefined ? 0 : Number(match[2]);
  const meridiem = match[3]?.toLowerCase();

  if (minute > 59) return null;

  if (meridiem === undefined) {
    if (hour > 23) return null;
    return toHhMm(assumeDeliveryDay(hour) * 60 + minute);
  }
  // With a meridiem the hour is a 12-hour clock, so "13pm" and "0am" are not
  // times the user could have meant.
  if (hour < 1 || hour > 12) return null;
  const base = hour % 12;
  return toHhMm((meridiem === 'p' ? base + 12 : base) * 60 + minute);
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
