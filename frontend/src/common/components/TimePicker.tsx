import { useCallback, useState } from 'react';

import ClockIcon from '@/assets/icons/clock.svg?react';
import { cn } from '@/lib/utils';

import {
  Popover,
  PopoverAnchor,
  PopoverContent,
  PopoverTrigger,
} from './Popover';
import {
  centeredScrollTop,
  formatDisplayTime,
  parseTypedTime,
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
  /** What is being typed, or null when the field is showing the value. */
  const [draft, setDraft] = useState<string | null>(null);

  const isOpen = open ?? internalOpen;
  const committedValue = value ?? internalValue;
  const paddingClass = timePickerPaddingClass(padding);

  const typedValue = draft === null ? null : parseTypedTime(draft);
  /**
   * The list follows what is being typed, not only what was last committed, so
   * typing "10:0" walks the selection down to 10:05 as it becomes readable.
   */
  const listValue = typedValue ?? committedValue;
  // Blank is incomplete rather than wrong — it is what clearing the field to
  // retype looks like — so it reverts on blur without being marked in red.
  const invalid = draft !== null && draft.trim() !== '' && typedValue === null;

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

  const commit = (next: string) => {
    setInternalValue(next);
    setDraft(null);
    onChange?.(next);
  };

  /** Takes the typed time if it reads, and otherwise puts the value back. */
  const commitDraft = () => {
    if (typedValue !== null) commit(typedValue);
    else setDraft(null);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      // Unreadable input keeps the field open and marked rather than throwing
      // away what was typed.
      if (typedValue !== null) {
        commit(typedValue);
        setInternalOpen(false);
      }
    } else if (event.key === 'Escape') {
      setDraft(null);
      setInternalOpen(false);
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setInternalOpen}>
      <PopoverAnchor asChild>
        <div
          data-slot="time-picker-trigger"
          className={cn(
            'inline-flex w-40 items-center justify-between gap-2 rounded-xl py-2',
            paddingClass,
            'bg-grey-100 outline outline-offset-[-1px]',
            'transition-colors',
            // Each branch names its own width *and* colour: leaving a base
            // colour for tailwind-merge to override drops the wrong class.
            invalid
              ? 'outline-red outline-2'
              : isOpen
                ? 'outline-2 outline-blue-300'
                : 'outline-grey-300 outline-1 focus-within:outline-2 focus-within:outline-blue-300',
            disabled && 'bg-grey-150 cursor-not-allowed opacity-60',
            className
          )}
        >
          {/* A plain input, not `Input`: that component's text is 16px, which
              would break the 34px trigger height the design specifies, and
              tailwind-merge cannot be relied on to resolve two custom text
              utilities against each other. */}
          <input
            type="text"
            data-slot="time-picker-input"
            aria-label="Time"
            aria-invalid={invalid || undefined}
            disabled={disabled}
            value={draft ?? formatDisplayTime(committedValue)}
            onChange={(event) => {
              setDraft(event.target.value);
              setInternalOpen(true);
            }}
            onFocus={() => setInternalOpen(true)}
            onBlur={commitDraft}
            onKeyDown={handleKeyDown}
            className={cn(
              'text-p2 text-grey-500 w-auto min-w-0 flex-1 bg-transparent p-0',
              'outline-none focus:outline-0',
              'disabled:cursor-not-allowed disabled:opacity-100'
            )}
          />
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={disabled}
              aria-label="Open time list"
              className="text-grey-400 hover:text-grey-500 shrink-0 cursor-pointer transition-colors"
            >
              <ClockIcon data-slot="time-picker-icon" className="size-4" />
            </button>
          </PopoverTrigger>
        </div>
      </PopoverAnchor>

      <PopoverContent
        data-slot="time-picker-panel"
        className="w-[var(--radix-popover-trigger-width)] overflow-hidden p-0"
        align="start"
        // Keep the caret in the field so the list can be browsed while typing.
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        {/* `relative` makes this the offsetParent the scroll maths measures from. */}
        <div role="listbox" className="relative max-h-32 overflow-y-auto">
          {timeOptions(listValue).map((option) => {
            const selected = option === listValue;
            return (
              <button
                key={option}
                type="button"
                role="option"
                aria-selected={selected}
                ref={selected ? selectedRef : undefined}
                // onMouseDown, because the input's blur would otherwise revert
                // the draft and move the list out from under the click.
                onMouseDown={(event) => {
                  event.preventDefault();
                  commit(option);
                  setInternalOpen(false);
                }}
                // A pointer never reaches this — mousedown already closed the
                // panel — but Enter and Space on a focused option do.
                onClick={() => {
                  commit(option);
                  setInternalOpen(false);
                }}
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
