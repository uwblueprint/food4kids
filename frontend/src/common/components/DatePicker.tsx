import { useEffect, useRef, useState } from 'react';

import CalendarIcon from '@/assets/icons/calendar.svg?react';
import { cn } from '@/lib/utils';

import { Calendar } from './Calendar';
import { Input } from './Input';
import {
  Popover,
  PopoverAnchor,
  PopoverContent,
  PopoverTrigger,
} from './Popover';

interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date | undefined) => void;
  disabled?: boolean;
  className?: string;
}

function toInputValue(date: Date | undefined): string {
  if (!date) return '';
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function parseInputValue(raw: string): Date | undefined {
  if (!raw) return undefined;
  const parsed = new Date(raw + 'T00:00:00');
  return isNaN(parsed.getTime()) ? undefined : parsed;
}

export function DatePicker({
  value,
  onChange,
  disabled,
  className,
}: DatePickerProps) {
  const today = new Date();
  const [open, setOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    value ?? today,
  );
  const [inputValue, setInputValue] = useState(toInputValue(value ?? today));
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const next = value ?? today;
    setSelectedDate(next);
    setInputValue(toInputValue(next));
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    setInputValue(raw);
    const parsed = parseInputValue(raw);
    setSelectedDate(parsed);
    onChange?.(parsed);
  };

  const handleCalendarSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    onChange?.(date);
    setInputValue(toInputValue(date));
    setOpen(false);
    inputRef.current?.focus();
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverAnchor asChild>
        <div
          className={cn(
            'inline-flex w-40 items-center justify-between rounded-lg px-3 py-2',
            'bg-grey-100 outline outline-1 outline-offset-[-1px] outline-grey-300',
            'transition-colors',
            open
              ? 'outline-2 outline-blue-300'
              : 'focus-within:outline-2 focus-within:outline-blue-300',
            disabled && 'bg-grey-150 cursor-not-allowed opacity-60',
            className,
          )}
        >
          <Input
            ref={inputRef}
            type="date"
            value={inputValue}
            onChange={handleInputChange}
            disabled={disabled}
            className={cn(
              'min-w-0 flex-1 w-auto bg-transparent px-0 py-0 outline-none focus:outline-0',
              'disabled:bg-transparent disabled:opacity-100',
              '[&::-webkit-calendar-picker-indicator]:hidden',
              '[&::-webkit-datetime-edit-fields-wrapper]:p-0',
            )}
          />
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={disabled}
              aria-label="Open calendar"
              className="shrink-0 cursor-pointer text-grey-400 transition-colors hover:text-grey-500"
            >
              <CalendarIcon className="size-4" />
            </button>
          </PopoverTrigger>
        </div>
      </PopoverAnchor>

      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={handleCalendarSelect}
          defaultMonth={selectedDate ?? today}
        />
      </PopoverContent>
    </Popover>
  );
}
