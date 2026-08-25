import EditIcon from '@/assets/icons/edit.svg?react';
import XIcon from '@/assets/icons/x.svg?react';

interface EditingBannerProps {
  onDismiss: () => void;
}

/**
 * The "editing enabled" pill that sits beside the page title while the settings
 * form is unlocked.
 *
 * Deliberately not the shared {@link Banner}: that one is the full-width
 * bordered block used for success/error/warning results. This is the design's
 * compact neutral pill — it reports a mode, not an outcome, so it carries no
 * status colour.
 */
export const EditingBanner = ({ onDismiss }: EditingBannerProps) => {
  return (
    <div
      role="status"
      className="border-grey-300 bg-grey-100 flex items-center gap-4 rounded-[40px] border px-6 py-3"
    >
      <EditIcon aria-hidden="true" className="text-grey-500 size-5 shrink-0" />
      <p className="text-p1 text-grey-500">
        Editing enabled. Save changes to apply updates.
      </p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Stop editing"
        className="text-grey-500 hover:text-grey-400 shrink-0 cursor-pointer transition-colors"
      >
        <XIcon className="size-5" />
      </button>
    </div>
  );
};
