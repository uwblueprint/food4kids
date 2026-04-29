import { useState } from 'react';

import ClockIcon from '@/assets/icons/clock.svg?react';
import { cn } from '@/lib/utils';

import { Input } from './Input';

interface TimePickerProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  disabled?: boolean;
  className?: string;
}

export function TimePicker({
  value: valueProp = '08:45',
  onChange,
  disabled,
  className,
}: TimePickerProps) {
  const [value, setValue] = useState(valueProp);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
    onChange?.(e.target.value || undefined);
  };

  return (
    <div
      className={cn(
        'inline-flex w-40 items-center justify-between rounded-lg px-3 py-2',
        'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
        'transition-colors focus-within:outline-2 focus-within:outline-blue-300',
        disabled && 'bg-grey-150 cursor-not-allowed opacity-60',
        className
      )}
    >
      <Input
        type="time"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className={cn(
          'min-w-0 flex-1 w-auto bg-transparent px-0 py-0 outline-none focus:outline-0',
          'disabled:bg-transparent disabled:opacity-100',
          '[&::-webkit-calendar-picker-indicator]:hidden',
          '[&::-webkit-datetime-edit-fields-wrapper]:p-0',
        )}
      />
      <ClockIcon className="text-grey-400 size-4 shrink-0" />
    </div>
  );
}
