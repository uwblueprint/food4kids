import { useState } from 'react';

import type { LocationRead } from '@/api/generated/types.gen';
import { useLocations } from '@/api/locations';
import { useUpdateRoute } from '@/api/routes';
import { useSystemSettings } from '@/api/system-settings';
import SearchIcon from '@/assets/icons/search.svg?react';
import {
  Button,
  Field,
  FieldDescription,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';
import { useDebouncedValue } from '@/common/hooks';
import { formatPhone, orDash } from '@/common/utils';
import { cn } from '@/lib/utils';

interface AddStopModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  routeId: string;
  /** The route's current stops in order, as location ids. */
  locationIds: string[];
  /** Route's delivery type — scopes the picker to matching locations. */
  deliveryType?: string | null;
  /** Called with the added stop's location id after a successful add. */
  onAdded?: (locationId: string) => void;
}

/**
 * One auto-filled stop detail shown as read-only label/value text (a <dt>/<dd>
 * pair), so it reads as information about the location rather than an editable
 * field.
 */
function ReadOnlyDetail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-p2 text-grey-400 font-semibold">{label}</dt>
      <dd className="text-p2 text-grey-500 font-semibold">{value}</dd>
    </div>
  );
}

/**
 * Searchable location picker for adding a stop to a route. Picking an address
 * fills the stop's details (contact, phone, boxes, notes) automatically from
 * that location — read-only, since the details live on the location and the
 * add-stop endpoint only takes the location id. Confirming appends the chosen
 * location to the route's ordered stops and PATCHes it (re-runs routing).
 */
export function AddStopModal({
  open,
  onOpenChange,
  routeId,
  locationIds,
  deliveryType,
  onAdded,
}: AddStopModalProps) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<LocationRead | null>(null);
  const debouncedSearch = useDebouncedValue(search).trim();
  const { mutate: updateRoute, isPending, isError, reset } = useUpdateRoute();
  // Boxes aren't stored on a location — they're derived the same way the
  // backend and stops table do: ceil(num_children / children_per_box). The
  // divisor defaults to 2 (matching SystemSettings) until settings load.
  const { data: settings } = useSystemSettings();
  const childrenPerBox = settings?.children_per_box ?? 2;

  const { data } = useLocations({
    search: debouncedSearch || undefined,
    delivery_type: deliveryType ? [deliveryType] : undefined,
    page_size: 20,
  });
  // Don't offer locations already on this route.
  const results = (data?.items ?? []).filter(
    (loc) => !locationIds.includes(loc.location_id)
  );

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setSearch('');
      setSelected(null);
      reset();
    }
  };

  // Typing again clears the selection so the results list comes back and the
  // auto-filled details hide until a new address is chosen.
  const handleSearchChange = (value: string) => {
    setSearch(value);
    setSelected(null);
  };

  const handleSelect = (loc: LocationRead) => {
    setSelected(loc);
    setSearch(loc.address);
  };

  const handleConfirm = () => {
    if (!selected) return;
    updateRoute(
      {
        path: { route_id: routeId },
        body: { location_ids: [...locationIds, selected.location_id] },
      },
      {
        onSuccess: () => {
          onAdded?.(selected.location_id);
          handleOpenChange(false);
        },
      }
    );
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      {/* 32px between sections (wider than the shared 16px default), per Figma. */}
      <ModalContent className="gap-8">
        {/* Figma: 32px between title and description (not the shared 8px). */}
        <ModalHeader className="gap-8">
          {/* Figma: "Add Delivery Stop" at 20px (text-h2), not the 32px form h1. */}
          <ModalTitle variant="form" className="text-h2">
            Add Delivery Stop
          </ModalTitle>
          {/* The intro only applies before an address is chosen; once the
              details fill in it drops away (matches Figma's filled state). */}
          {!selected && (
            <ModalDescription>
              Start typing to search for an address. Stop details will fill in
              automatically.
            </ModalDescription>
          )}
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel required htmlFor="add-stop-search">
              Address
            </FieldLabel>
            <div className="relative">
              <SearchIcon className="text-grey-400 pointer-events-none absolute top-1/2 left-3 size-5 -translate-y-1/2" />
              <Input
                id="add-stop-search"
                className="pl-10"
                placeholder="Search by address, school, or family name"
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>

            {/* Results appear only while searching with nothing picked yet. */}
            {debouncedSearch && !selected && (
              <div className="border-grey-300 max-h-64 overflow-y-auto rounded-lg border">
                {results.length === 0 ? (
                  <p className="text-p2 text-grey-400 px-3 py-4 text-center">
                    No matching locations
                  </p>
                ) : (
                  results.map((loc) => (
                    <button
                      key={loc.location_id}
                      type="button"
                      onClick={() => handleSelect(loc)}
                      className={cn(
                        'flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left transition-colors',
                        'hover:bg-grey-150'
                      )}
                    >
                      <span className="text-p2 text-grey-500 font-medium">
                        {loc.address}
                      </span>
                      <span className="text-p2 text-grey-400">
                        {loc.contact_name}
                      </span>
                    </button>
                  ))
                )}
              </div>
            )}
          </Field>

          {/* Auto-filled stop details from the chosen location. Rendered as
              plain label/value text — not inputs — so it's unmistakable that
              these come from the location and can't be edited here. */}
          {selected && (
            <dl className="flex flex-col gap-4">
              <ReadOnlyDetail
                label="Contact Name"
                value={selected.contact_name}
              />
              <ReadOnlyDetail
                label="Phone Number"
                value={orDash(
                  selected.phone_primary && formatPhone(selected.phone_primary)
                )}
              />
              <ReadOnlyDetail
                label="Number of Boxes"
                value={String(
                  Math.ceil((selected.num_children ?? 0) / childrenPerBox)
                )}
              />
              <ReadOnlyDetail
                label="Driver Notes"
                value={selected.latest_note ?? '—'}
              />
            </dl>
          )}
        </div>

        {isError && (
          <FieldDescription error>
            Something went wrong adding the stop. Please try again.
          </FieldDescription>
        )}
        <ModalFooter className="shrink-0 grow basis-0 flex-col items-end justify-end gap-2.5 self-stretch">
          <Button
            variant="primary"
            disabled={!selected || isPending}
            onClick={handleConfirm}
          >
            Add stop
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
