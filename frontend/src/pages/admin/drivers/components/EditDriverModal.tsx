import { type FormEvent, useState } from 'react';

import { useUpdateDriver } from '@/api/drivers';
import type { DriverRead } from '@/api/generated/types.gen';
import {
  Button,
  Field,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

const DAYS = ['M', 'Tu', 'W', 'Th', 'F'];

interface EditDriverModalProps {
  driver: DriverRead;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditDriverModal({
  driver,
  open,
  onOpenChange,
}: EditDriverModalProps) {
  const update = useUpdateDriver();
  const [availability, setAvailability] = useState(
    driver.availability ?? [false, false, false, false, false]
  );

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const optional = (name: string) => String(data.get(name) ?? '').trim() || null;
    update.mutate(
      {
        path: { driver_id: driver.driver_id },
        body: {
          first_name: String(data.get('first_name') ?? '').trim(),
          last_name: String(data.get('last_name') ?? '').trim(),
          phone: optional('phone'),
          partner_driver_name: optional('partner_driver_name'),
          address: optional('address'),
          car_make_model: optional('car_make_model'),
          license_plate: optional('license_plate'),
          availability,
        },
      },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="max-h-[90vh] max-w-[560px] overflow-y-auto">
        <form onSubmit={submit} className="flex flex-col gap-4">
          <ModalHeader>
            <ModalTitle variant="confirmation">Edit Driver Information</ModalTitle>
          </ModalHeader>
          <div className="grid grid-cols-2 gap-4">
            <Field>
              <FieldLabel required>First Name</FieldLabel>
              <Input name="first_name" defaultValue={driver.first_name} required />
            </Field>
            <Field>
              <FieldLabel required>Last Name</FieldLabel>
              <Input name="last_name" defaultValue={driver.last_name} required />
            </Field>
          </div>
          <Field>
            <FieldLabel>Email</FieldLabel>
            <Input value={driver.email} disabled />
          </Field>
          <Field>
            <FieldLabel>Phone Number</FieldLabel>
            <Input name="phone" defaultValue={driver.phone ?? ''} />
          </Field>
          <Field>
            <FieldLabel>Address</FieldLabel>
            <Input name="address" defaultValue={driver.address ?? ''} />
          </Field>
          <Field>
            <FieldLabel>Partner Driver Name</FieldLabel>
            <Input
              name="partner_driver_name"
              defaultValue={driver.partner_driver_name ?? ''}
            />
          </Field>
          <div className="grid grid-cols-2 gap-4">
            <Field>
              <FieldLabel>Vehicle</FieldLabel>
              <Input
                name="car_make_model"
                defaultValue={driver.car_make_model ?? ''}
              />
            </Field>
            <Field>
              <FieldLabel>License Plate</FieldLabel>
              <Input
                name="license_plate"
                defaultValue={driver.license_plate ?? ''}
              />
            </Field>
          </div>
          <Field>
            <FieldLabel>Availability</FieldLabel>
            <div className="flex gap-3">
              {DAYS.map((day, index) => (
                <button
                  key={day}
                  type="button"
                  aria-pressed={availability[index]}
                  onClick={() =>
                    setAvailability((current) =>
                      current.map((value, i) => (i === index ? !value : value))
                    )
                  }
                  className={`flex size-9 items-center justify-center rounded-full text-sm font-semibold ${
                    availability[index]
                      ? 'bg-blue-50 text-blue-300'
                      : 'bg-grey-150 text-grey-400'
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
          </Field>
          {update.isError && (
            <p className="text-p2 text-red">Couldn&apos;t save this driver.</p>
          )}
          <ModalFooter className="pt-2">
            <Button type="button" variant="tertiary" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={update.isPending}>
              Save
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
