import { cn } from '@/lib/utils';

interface ToggleProps {
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
  /** Labels shown beside the switch for the on/off states. */
  onLabel?: string;
  offLabel?: string;
  className?: string;
}

/**
 * Yes/No switch. The knob is always Grey/100 — it does not change with the
 * track, which is blue when on and grey when off.
 */
function Toggle({
  checked,
  disabled = false,
  onChange,
  onLabel = 'Yes',
  offLabel = 'No',
  className,
}: ToggleProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3',
        disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
        className
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-5 w-9 rounded-full transition-colors',
          checked ? 'bg-blue-300' : 'bg-grey-300'
        )}
      >
        <span
          className={cn(
            'bg-grey-100 absolute top-0.5 left-0 size-4 rounded-full transition-transform',
            checked ? 'translate-x-[18px]' : 'translate-x-0.5'
          )}
        />
      </button>
      <span className="text-p2">{checked ? onLabel : offLabel}</span>
    </div>
  );
}

export { Toggle };
