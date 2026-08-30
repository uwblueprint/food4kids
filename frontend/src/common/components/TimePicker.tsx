import { useCallback, useState } from 'react';

import ClockIcon from '@/assets/icons/clock.svg?react';
import { cn } from '@/lib/utils';

import { Popover, PopoverContent, PopoverTrigger } from './Popover';
import {
  centeredScrollTop,
  formatDisplayTime,
  timeOptions,
} from './TimePicker.options';
import {
  type TimePickerPadding,
  timePickerPaddingClass,
} from './TimePicker.padding';

export type { TimePickerPadding };

interface TimePickerProps {
  /** Time as a 24-hour "HH:MM" string. */
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  /**
   * Side padding of the trigger, in px, which the panel's options match: 12 in
   * the route-generation table, 24 in Settings.
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

const DEFAULT_VALUE = '08:00';

export function TimePicker({
  value,
  onChange,
  disabled,
  padding = 12,
  open,
  className,
}: TimePickerProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [internalValue, setInternalValue] = useState(value ?? DEFAULT_VALUE);
  const isOpen = open ?? internalOpen;
  const currentValue = value ?? internalValue;
  const paddingClass = timePickerPaddingClass(padding);

  /**
   * Centres the selection as the panel appears. This is a callback ref rather
   * than an effect because the panel only mounts once the popover opens, so it
   * runs exactly when the option and its scroll box first have a layout. It
   * reads the list off the option rather than a ref of its own: React assigns
   * a child's ref before its parent's, so a ref on the list would still be
   * null here.
   */
  const selectedRef = useCallback((option: HTMLButtonElement | null) => {
    const list = option?.parentElement;
    if (!option || !list) return;
    list.scrollTop = centeredScrollTop({
      optionTop: option.offsetTop,
      optionHeight: option.offsetHeight,
      viewportHeight: list.clientHeight,
      contentHeight: list.scrollHeight,
    });
  }, []);

  const handleSelect = (next: string) => {
    setInternalValue(next);
    setInternalOpen(false);
    onChange?.(next);
  };

  return (
    <Popover open={isOpen} onOpenChange={setInternalOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          data-slot="time-picker-trigger"
          disabled={disabled}
          className={cn(
            'inline-flex w-40 cursor-pointer items-center justify-between rounded-xl py-2',
            paddingClass,
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
            {formatDisplayTime(currentValue)}
          </span>
          <ClockIcon
            data-slot="time-picker-icon"
            className="text-grey-400 size-4 shrink-0"
          />
        </button>
      </PopoverTrigger>

      <PopoverContent
        data-slot="time-picker-panel"
        className="w-[var(--radix-popover-trigger-width)] overflow-hidden p-0"
        align="start"
      >
        {/* `relative` makes this the offsetParent the scroll maths measures from. */}
        <div role="listbox" className="relative max-h-32 overflow-y-auto">
          {timeOptions(currentValue).map((option) => {
            const selected = option === currentValue;
            return (
              <button
                key={option}
                type="button"
                role="option"
                aria-selected={selected}
                ref={selected ? selectedRef : undefined}
                onClick={() => handleSelect(option)}
                className={cn(
                  'text-p2 flex w-full cursor-pointer items-center py-3 text-left transition-colors',
                  paddingClass,
                  selected
                    ? 'bg-blue-50 font-semibold text-blue-300'
                    : 'text-grey-500 hover:bg-blue-50'
                )}
              >
                {formatDisplayTime(option)}
              </button>
            );
          })}
        </div>
      </PopoverContent>
    </Popover>
  );
}
