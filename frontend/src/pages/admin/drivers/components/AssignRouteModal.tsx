import { useState } from 'react';

import {
  Button,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Dropdown,
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
          <Dropdown
            label="Route"
            placeholder="Select a Route"
            options={ROUTE_OPTIONS}
            value={route}
            onValueChange={setRoute}
          />
          <Dropdown
            label="Driver"
            placeholder="Dropdown Selection"
            options={DRIVER_OPTIONS}
            value={driver}
            onValueChange={setDriver}
            helperText="Last Driven By: LAST_DRIVER_NAME"
          />
          <Dropdown
            label="Start Time"
            placeholder="9:00 AM"
            options={START_TIME_OPTIONS}
            value={startTime}
            onValueChange={setStartTime}
          />
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
