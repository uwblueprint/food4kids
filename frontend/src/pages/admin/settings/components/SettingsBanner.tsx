import type { FunctionComponent, SVGProps } from 'react';

import CheckCircleIcon from '@/assets/icons/check-circle.svg?react';
import EditIcon from '@/assets/icons/edit.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import { cn } from '@/lib/utils';

type SettingsBannerVariant = 'editing' | 'saved';

interface VariantSpec {
  Icon: FunctionComponent<SVGProps<SVGSVGElement>>;
  message: string;
  container: string;
  icon: string;
}

const VARIANTS: Record<SettingsBannerVariant, VariantSpec> = {
  editing: {
    Icon: EditIcon,
    message: 'Editing enabled. Save changes to apply updates.',
    container: 'border-grey-300 bg-grey-100',
    icon: 'text-grey-500',
  },
  saved: {
    Icon: CheckCircleIcon,
    message: 'Changes have been successfully saved!',
    container: 'border-success-stroke bg-success-fill',
    icon: 'text-success-stroke',
  },
};

interface SettingsBannerProps {
  variant: SettingsBannerVariant;
  onDismiss: () => void;
  /** What dismissing does, which differs per variant. */
  dismissLabel: string;
}

/**
 * The pill beside the page title that reports the form's current mode.
 *
 * Deliberately not the shared {@link Banner}: that one is the full-width
 * bordered block used for error results. This is the design's compact pill.
 */
export const SettingsBanner = ({
  variant,
  onDismiss,
  dismissLabel,
}: SettingsBannerProps) => {
  const { Icon, message, container, icon } = VARIANTS[variant];

  return (
    <div
      role="status"
      className={cn(
        'flex items-center gap-4 rounded-[40px] border px-6 py-3',
        container
      )}
    >
      <Icon aria-hidden="true" className={cn('size-5 shrink-0', icon)} />
      <p className="text-p1 text-grey-500">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label={dismissLabel}
        className="text-grey-500 hover:text-grey-400 shrink-0 cursor-pointer transition-colors"
      >
        <XIcon className="size-5" />
      </button>
    </div>
  );
};
