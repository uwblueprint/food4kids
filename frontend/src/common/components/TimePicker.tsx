import { useState } from 'react';

import ClockIcon from '@/assets/icons/clock.svg?react';
import { cn } from '@/lib/utils';

import { Popover, PopoverContent, PopoverTrigger } from './Popover';
import {
  type TimePickerPadding,
  timePickerPaddingClasses,
} from './TimePicker.padding';

export type { TimePickerPadding };

interface TimePickerProps {
  /** Time as a 24-hour "HH:MM" string. */
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  /**
   * Side padding of the trigger, in px. A dropdown's left padding follows the
   * button it opens from, which differs by context: 12 in the route-generation
   * table, 24 in Settings.
   */
  padding?: TimePickerPadding;
  /**
   * Forces the panel open or closed. Left undefined the picker manages its own
   * open state; the style guide pins it so both padding variants can show
   * their panel at once, which Radix would otherwise not allow — a non-modal
   * popover closes as soon as focus lands in the other one.
   */
  open?: boolean;
  className?: string;
}

const HOURS = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] as const;
const MINUTES = Array.from({ length: 12 }, (_, i) => i * 5);
const PERIODS = ['AM', 'PM'] as const;
type Period = (typeof PERIODS)[number];

function parseTime(value: string): {
  hour: number;
  minute: number;
  period: Period;
} {
  const [hRaw = 0, mRaw = 0] = value.split(':').map(Number);
  const period: Period = hRaw >= 12 ? 'PM' : 'AM';
  const hour = hRaw % 12 === 0 ? 12 : hRaw % 12;
  const minute = (Math.round(mRaw / 5) * 5) % 60;
  return { hour, minute, period };
}

function formatTime(hour: number, minute: number, period: Period): string {
  let h = hour % 12;
  if (period === 'PM') h += 12;
  return `${String(h).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

function formatDisplay(value: string): string {
  const { hour, minute, period } = parseTime(value);
  return `${hour}:${String(minute).padStart(2, '0')} ${period}`;
}

export function TimePicker({
  value,
  onChange,
  disabled,
  padding = 12,
  open,
  className,
}: TimePickerProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen = open ?? internalOpen;
  const { trigger: triggerPadding, panel: panelPadding } =
    timePickerPaddingClasses(padding);
  const [internalValue, setInternalValue] = useState(value ?? '08:00');
  const currentValue = value ?? internalValue;
  const { hour, minute, period } = parseTime(currentValue);

  const handleSelect = (next: {
    hour?: number;
    minute?: number;
    period?: Period;
  }) => {
    const newValue = formatTime(
      next.hour ?? hour,
      next.minute ?? minute,
      next.period ?? period
    );
    setInternalValue(newValue);
    onChange?.(newValue);
  };

  return (
    <Popover open={isOpen} onOpenChange={setInternalOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          data-slot="time-picker-trigger"
          disabled={disabled}
          className={cn(
            'inline-flex w-40 cursor-pointer items-center justify-between rounded-sm py-2',
            triggerPadding,
            'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
            'transition-colors',
            isOpen
              ? 'outline-2 outline-blue-300'
              : 'focus-visible:outline-2 focus-visible:outline-blue-300',
            disabled && 'bg-grey-150 cursor-not-allowed opacity-60',
            className
          )}
        >
          <span className="text-p2 text-grey-500">
            {formatDisplay(currentValue)}
          </span>
          <ClockIcon
            data-slot="time-picker-icon"
            className="text-grey-400 size-4 shrink-0"
          />
        </button>
      </PopoverTrigger>

      <PopoverContent
        data-slot="time-picker-panel"
        className={cn('w-auto py-0', panelPadding)}
        align="start"
      >
        <div className="flex">
          <Column
            items={HOURS}
            selected={hour}
            onSelect={(v) => handleSelect({ hour: v })}
          />
          <Column
            items={MINUTES}
            selected={minute}
            format={(v) => String(v).padStart(2, '0')}
            onSelect={(v) => handleSelect({ minute: v })}
          />
          <Column
            items={PERIODS}
            selected={period}
            onSelect={(v) => handleSelect({ period: v })}
            noBorder
          />
        </div>
      </PopoverContent>
    </Popover>
  );
}

interface ColumnProps<T extends string | number> {
  items: readonly T[];
  selected: T;
  format?: (v: T) => string;
  onSelect: (v: T) => void;
  noBorder?: boolean;
}

function Column<T extends string | number>({
  items,
  selected,
  format,
  onSelect,
  noBorder,
}: ColumnProps<T>) {
  return (
    <div
      className={cn(
        'flex max-h-[200px] flex-col items-start gap-0.5 overflow-y-auto py-1',
        !noBorder && 'border-grey-300 border-r'
      )}
    >
      {items.map((item) => (
        <button
          key={String(item)}
          type="button"
          onClick={() => onSelect(item)}
          className={cn(
            // Hugs its label rather than a fixed min-width: the pill's own
            // px-3 is what puts the label at the panel's inset, so a wider
            // pill would push a short label off its own centre.
            'text-p2 flex h-10 shrink-0 cursor-pointer items-center justify-start rounded-full px-3 transition-colors',
            item === selected
              ? 'bg-blue-300 text-white'
              : 'text-grey-500 hover:bg-blue-50'
          )}
        >
          {format ? format(item) : item}
        </button>
      ))}
    </div>
  );
}
