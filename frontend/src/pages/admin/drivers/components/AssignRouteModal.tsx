import { useState } from 'react';

import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Field,
  FieldDescription,
  FieldLabel,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

// TODO: replace with API data
const ROUTE_OPTIONS = [
  { label: 'Route A', value: 'route-a' },
  { label: 'Route B', value: 'route-b' },
  { label: 'Route C', value: 'route-c' },
];

const DRIVER_OPTIONS = [
  { label: 'Marcus Smith', value: 'marcus-smith' },
  { label: 'Sarah Lee', value: 'sarah-lee' },
  { label: 'James Park', value: 'james-park' },
];

const START_TIME_OPTIONS = [
  { label: '8:00 AM', value: '08:00' },
  { label: '8:30 AM', value: '08:30' },
  { label: '9:00 AM', value: '09:00' },
  { label: '9:30 AM', value: '09:30' },
  { label: '10:00 AM', value: '10:00' },
];

interface AssignRouteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssignRouteModal({
  open,
  onOpenChange,
}: AssignRouteModalProps) {
  const [route, setRoute] = useState('');
  const [driver, setDriver] = useState('');
  const [startTime, setStartTime] = useState('');

  const handleClose = () => onOpenChange(false);

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Assign a Route</ModalTitle>
          <ModalDescription>Assign a route to DRIVER_NAME</ModalDescription>
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel>Route</FieldLabel>
            <Dropdown value={route} onValueChange={setRoute}>
              <DropdownTrigger>
                <DropdownValue placeholder="Select a Route" />
              </DropdownTrigger>
              <DropdownContent>
                {ROUTE_OPTIONS.map((opt) => (
                  <DropdownItem key={opt.value} value={opt.value}>{opt.label}</DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
          </Field>

          <Field>
            <FieldLabel>Driver</FieldLabel>
            <Dropdown value={driver} onValueChange={setDriver}>
              <DropdownTrigger>
                <DropdownValue placeholder="Dropdown Selection" />
              </DropdownTrigger>
              <DropdownContent>
                {DRIVER_OPTIONS.map((opt) => (
                  <DropdownItem key={opt.value} value={opt.value}>{opt.label}</DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
            <FieldDescription>Last Driven By: LAST_DRIVER_NAME</FieldDescription>
          </Field>

          <Field>
            <FieldLabel>Start Time</FieldLabel>
            <Dropdown value={startTime} onValueChange={setStartTime}>
              <DropdownTrigger>
                <DropdownValue placeholder="9:00 AM" />
              </DropdownTrigger>
              <DropdownContent>
                {START_TIME_OPTIONS.map((opt) => (
                  <DropdownItem key={opt.value} value={opt.value}>{opt.label}</DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
          </Field>
        </div>

        <ModalFooter className="justify-between pt-4">
          <Button variant="tertiary" onClick={handleClose}>
            Cancel
          </Button>
          <div className="flex items-center gap-2.5">
            <Button variant="secondary">View Route</Button>
            <Button variant="primary">Assign</Button>
          </div>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
