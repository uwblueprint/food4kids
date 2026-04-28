import { useState } from 'react';

import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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

interface AssignRouteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssignRouteDialog({
  open,
  onOpenChange,
}: AssignRouteDialogProps) {
  const [route, setRoute] = useState('');
  const [driver, setDriver] = useState('');
  const [startTime, setStartTime] = useState('');

  const handleClose = () => onOpenChange(false);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Assign a Route</DialogTitle>
          <DialogDescription>Assign a route to DRIVER_NAME</DialogDescription>
        </DialogHeader>

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

        <DialogFooter className="justify-between pt-4">
          <Button variant="tertiary" onClick={handleClose}>
            Cancel
          </Button>
          <div className="flex items-center gap-2.5">
            <Button variant="secondary">View Route</Button>
            <Button variant="primary">Assign</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
