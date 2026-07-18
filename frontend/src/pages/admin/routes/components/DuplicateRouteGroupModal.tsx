import { useState } from 'react';

import type { RouteGroupRead } from '@/api/generated/types.gen';
import { useDuplicateRouteGroup } from '@/api/route-groups';
import CalendarIcon from '@/assets/icons/calendar.svg?react';
import {
  Button,
  Calendar,
  Field,
  FieldDescription,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components';
import { formatShortDate, toNaiveDateString } from '@/common/utils';
import { cn } from '@/lib/utils';

interface DuplicateRouteGroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The group being duplicated; its routes/stops are copied server-side. */
  routeGroup: RouteGroupRead;
  /** Called with the copy's id so the table can highlight and scroll to it. */
  onDuplicated: (routeGroupId: string) => void;
}

/** What the copy inherits from the original, shown in the summary block. */
function CopiedField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-p2 text-grey-400">{label}</span>
      <span className="text-p2 text-grey-500">{value}</span>
    </div>
  );
}

export function DuplicateRouteGroupModal({
  open,
  onOpenChange,
  routeGroup,
  onDuplicated,
}: DuplicateRouteGroupModalProps) {
  const defaultName = `${routeGroup.name} (Copy)`;
  const [name, setName] = useState(defaultName);
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const {
    mutate: duplicateRouteGroup,
    isPending,
    isError,
    reset,
  } = useDuplicateRouteGroup();

  const isValid = name.trim().length > 0 && !!date;

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setName(defaultName);
      setDate(undefined);
      setCalendarOpen(false);
      reset();
    }
  };

  const handleSubmit = () => {
    if (!isValid || !date) return;
    duplicateRouteGroup(
      {
        path: { route_group_id: routeGroup.route_group_id },
        body: {
          name: name.trim(),
          drive_date: `${toNaiveDateString(date)}T00:00:00`,
        },
      },
      {
        onSuccess: (copy) => {
          onDuplicated(copy.route_group_id);
          handleOpenChange(false);
        },
      }
    );
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Duplicate Route Group</ModalTitle>
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel required htmlFor="duplicate-route-group-name">
              Name
            </FieldLabel>
            <Input
              id="duplicate-route-group-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </Field>

          <Field>
            <FieldLabel required>Date</FieldLabel>
            <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className={cn(
                    'flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-3',
                    'text-m-p2 tablet:font-medium text-left font-normal',
                    'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
                    'transition-colors focus:outline-2 focus:outline-blue-300',
                    'data-[state=open]:outline-2 data-[state=open]:outline-blue-300',
                    date ? 'text-grey-500' : 'text-grey-400'
                  )}
                >
                  {date
                    ? formatShortDate(toNaiveDateString(date))
                    : 'Select delivery date'}
                  <CalendarIcon className="text-grey-400 size-4 shrink-0" />
                </button>
              </PopoverTrigger>
              <PopoverContent align="start" className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(next) => {
                    setDate(next);
                    setCalendarOpen(false);
                  }}
                  defaultMonth={date ?? new Date()}
                />
              </PopoverContent>
            </Popover>
          </Field>

          <div className="flex flex-col gap-3">
            <p className="text-p2 text-grey-500 font-semibold">
              The following will be copied from the original group:
            </p>
            <div className="border-grey-300 grid grid-cols-2 gap-x-8 gap-y-4 border-l-2 pl-4">
              <CopiedField
                label="Delivery Type"
                value={routeGroup.delivery_type ?? '-'}
              />
              <CopiedField
                label="Locations"
                value={String(routeGroup.num_locations)}
              />
              <CopiedField label="Boxes" value={String(routeGroup.num_boxes)} />
              <CopiedField
                label="Routes"
                value={String(routeGroup.num_routes)}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-4">
          {isError && (
            <FieldDescription error>
              Something went wrong duplicating the group. Please try again.
            </FieldDescription>
          )}
          <Button
            variant="primary"
            disabled={!isValid || isPending}
            onClick={handleSubmit}
          >
            Duplicate Group
          </Button>
        </div>
      </ModalContent>
    </Modal>
  );
}
