import { useState } from 'react';

import { useCreateRouteGroup } from '@/api/route-groups';
import CalendarIcon from '@/assets/icons/calendar.svg?react';
import {
  Button,
  Calendar,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
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
import { formatShortDate } from '@/common/utils';
import { cn } from '@/lib/utils';

function toNaiveDateString(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

interface AddRouteGroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  deliveryTypes: string[];
  /** Called with the created group's id so the table can highlight it. */
  onCreated: (routeGroupId: string) => void;
}

export function AddRouteGroupModal({
  open,
  onOpenChange,
  deliveryTypes,
  onCreated,
}: AddRouteGroupModalProps) {
  const [name, setName] = useState('');
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [deliveryType, setDeliveryType] = useState('');
  const [calendarOpen, setCalendarOpen] = useState(false);
  const {
    mutate: createRouteGroup,
    isPending,
    isError,
    reset,
  } = useCreateRouteGroup();

  const isValid = name.trim().length > 0 && !!date && deliveryType.length > 0;

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setName('');
      setDate(undefined);
      setDeliveryType('');
      setCalendarOpen(false);
      reset();
    }
  };

  const handleSubmit = () => {
    if (!isValid || !date) return;
    createRouteGroup(
      {
        body: {
          name: name.trim(),
          drive_date: `${toNaiveDateString(date)}T00:00:00`,
          delivery_type: deliveryType,
        },
      },
      {
        onSuccess: (created) => {
          onCreated(created.route_group_id);
          handleOpenChange(false);
        },
      }
    );
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Add Route Group</ModalTitle>
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel required htmlFor="route-group-name">
              Name
            </FieldLabel>
            <Input
              id="route-group-name"
              placeholder="e.g., Tuesday A - Cambridge North"
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

          <Field>
            <FieldLabel required>Delivery Type</FieldLabel>
            <Dropdown value={deliveryType} onValueChange={setDeliveryType}>
              <DropdownTrigger className="rounded-lg px-3">
                <DropdownValue placeholder="Select delivery type" />
              </DropdownTrigger>
              <DropdownContent>
                {deliveryTypes.map((type) => (
                  <DropdownItem key={type} value={type}>
                    {type}
                  </DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
          </Field>
        </div>

        <div className="flex items-center justify-end gap-4">
          {isError && (
            <FieldDescription error>
              Something went wrong adding the group. Please try again.
            </FieldDescription>
          )}
          <Button
            variant="primary"
            disabled={!isValid || isPending}
            onClick={handleSubmit}
          >
            Add Group
          </Button>
        </div>
      </ModalContent>
    </Modal>
  );
}
