import { useEffect, useRef, useState } from 'react';
import { format, isValid, parse } from 'date-fns';

import CalendarIcon from '@/assets/icons/calendar.svg?react';
import { cn } from '@/lib/utils';

import { Calendar } from './Calendar';
import {
  Popover,
  PopoverAnchor,
  PopoverContent,
  PopoverTrigger,
} from './Popover';

const DATE_FORMAT = 'MM/dd/yy';

interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function DatePicker({
  value,
  onChange,
  placeholder = 'Select a date',
  disabled,
  className,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState(
    value ? format(value, DATE_FORMAT) : ''
  );
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync input when controlled value changes externally
  useEffect(() => {
    setInputValue(value ? format(value, DATE_FORMAT) : '');
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Strip non-digits and cap at 6
    const digits = e.target.value.replace(/\D/g, '').slice(0, 6);

    // Auto-insert slashes: MM/DD/YY
    let formatted = digits;
    if (digits.length > 4)
      formatted = `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
    else if (digits.length > 2)
      formatted = `${digits.slice(0, 2)}/${digits.slice(2)}`;

    setInputValue(formatted);

    if (digits.length === 6) {
      const parsed = parse(formatted, DATE_FORMAT, new Date());
      onChange?.(isValid(parsed) ? parsed : undefined);
    } else if (digits.length === 0) {
      onChange?.(undefined);
    }
  };

  const handleCalendarSelect = (date: Date | undefined) => {
    onChange?.(date);
    setInputValue(date ? format(date, DATE_FORMAT) : '');
    setOpen(false);
    inputRef.current?.focus();
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverAnchor asChild>
        <div
          className={cn(
            'inline-flex w-40 items-center justify-between rounded-lg px-3 py-2',
            'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
            'transition-colors',
            open
              ? 'outline-2 outline-blue-300'
              : 'focus-within:outline-2 focus-within:outline-blue-300',
            disabled && 'bg-grey-150 cursor-not-allowed opacity-60',
            className
          )}
        >
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            placeholder={placeholder}
            value={inputValue}
            onChange={handleInputChange}
            disabled={disabled}
            className="font-nunito-sans text-grey-500 placeholder:text-grey-400 min-w-0 flex-1 bg-transparent text-sm font-normal outline-none"
          />
          <PopoverTrigger asChild>
            <button
              type="button"
              disabled={disabled}
              aria-label="Open calendar"
              className="text-grey-400 hover:text-grey-500 shrink-0 cursor-pointer transition-colors"
            >
              <CalendarIcon className="size-4" />
            </button>
          </PopoverTrigger>
        </div>
      </PopoverAnchor>

      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={value}
          onSelect={handleCalendarSelect}
          defaultMonth={value}
        />
      </PopoverContent>
    </Popover>
  );
}
