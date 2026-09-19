import type {
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import {
  Button,
  FilterChip,
  FilterChipGroup,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

import type {
  RouteFilterState,
  UseRouteFiltersReturn,
} from '../hooks/useRouteFilters';

const WEEKDAYS: DriveDaysOfWeekEnum[] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
// Group/route status is only ever Upcoming or Completed here (Archived is in
// the enum but not surfaced), matching the Figma.
const ROUTE_STATUSES: RouteStatusEnum[] = ['Upcoming', 'Completed'];
const DRIVER_STATUSES: DriverAssignmentStatusEnum[] = [
  'Assigned',
  'Unassigned',
];

interface RouteFilterModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Dialog subtitle, e.g. "Groups" or "Routes". */
  subtitle: string;
  /** Configured delivery types, for the Delivery Type chips. */
  deliveryTypes: string[];
  draftFilters: RouteFilterState;
  toggleDraft: UseRouteFiltersReturn['toggleDraft'];
  draftHasSelections: boolean;
  clearDraft: () => void;
  handleApply: () => void;
}

/**
 * Shared filter dialog for the Groups and Routes tabs: Day, Delivery Type,
 * Route Status, and Driver Status chip groups, plus Clear All / Apply.
 */
export function RouteFilterModal({
  open,
  onOpenChange,
  subtitle,
  deliveryTypes,
  draftFilters,
  toggleDraft,
  draftHasSelections,
  clearDraft,
  handleApply,
}: RouteFilterModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle variant="form">Filters</ModalTitle>
          <ModalDescription>{subtitle}</ModalDescription>
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <FilterChipGroup label="Day">
            {WEEKDAYS.map((day) => (
              <FilterChip
                key={day}
                selected={draftFilters.weekdays.has(day)}
                onClick={() => toggleDraft('weekdays', day)}
              >
                {day}
              </FilterChip>
            ))}
          </FilterChipGroup>

          <FilterChipGroup label="Delivery Type">
            {deliveryTypes.map((type) => (
              <FilterChip
                key={type}
                selected={draftFilters.deliveryTypes.has(type)}
                onClick={() => toggleDraft('deliveryTypes', type)}
              >
                {type}
              </FilterChip>
            ))}
          </FilterChipGroup>

          <FilterChipGroup label="Route Status">
            {ROUTE_STATUSES.map((status) => (
              <FilterChip
                key={status}
                selected={draftFilters.routeStatuses.has(status)}
                onClick={() => toggleDraft('routeStatuses', status)}
              >
                {status}
              </FilterChip>
            ))}
          </FilterChipGroup>

          <FilterChipGroup label="Driver Status">
            {DRIVER_STATUSES.map((status) => (
              <FilterChip
                key={status}
                selected={draftFilters.driverStatuses.has(status)}
                onClick={() => toggleDraft('driverStatuses', status)}
              >
                {status}
              </FilterChip>
            ))}
          </FilterChipGroup>
        </div>

        <ModalFooter className="mt-4">
          {/* Clear All only empties the dialog's chips; Apply persists them,
              which is also how an applied filter gets cleared. */}
          <Button
            variant="secondary"
            disabled={!draftHasSelections}
            // The base button disables pointer events entirely; re-enable them
            // so the not-allowed cursor can show over the button.
            className="disabled:pointer-events-auto disabled:cursor-not-allowed"
            onClick={clearDraft}
          >
            Clear all
          </Button>
          <Button variant="primary" onClick={handleApply}>
            Apply
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
