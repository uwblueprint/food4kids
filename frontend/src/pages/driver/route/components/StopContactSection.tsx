import type { RouteStopDetailRead } from '@/api/generated/types.gen';
import PhoneIcon from '@/assets/icons/phone.svg?react';
import { Button } from '@/common/components';
import { cn } from '@/lib/utils';

import { formatPhoneDisplay, telHref } from './noteUtils';

interface StopContactSectionProps {
  stop: RouteStopDetailRead;
}

interface ContactCardProps {
  name: string;
  label: string;
  phone: string;
}

// Full width on mobile, but capped from tablet up. The design fixes these at
// ~310px on both the 834 and 1440 frames rather than letting a phone number
// stretch the whole content column with dead space before the call button.
const CONTACT_CARD_WIDTH = 'tablet:max-w-[310px]';

function ContactCard({ name, label, phone }: ContactCardProps) {
  return (
    <div
      className={cn(
        'border-grey-300 flex items-center gap-3 rounded-xl border bg-white p-3',
        CONTACT_CARD_WIDTH
      )}
    >
      <div className="flex min-w-0 flex-1 flex-col">
        <p className="text-p1 text-grey-500 font-semibold break-words">
          {name} <span className="text-grey-400 font-normal">({label})</span>
        </p>
        <p className="text-p2 text-grey-500">{formatPhoneDisplay(phone)}</p>
      </div>
      <Button
        asChild
        type="button"
        variant="primary"
        shape="circular"
        className="size-11 shrink-0"
        aria-label={`Call ${name}`}
      >
        <a href={telHref(phone)}>
          <PhoneIcon className="size-5" />
        </a>
      </Button>
    </div>
  );
}

export function StopContactSection({ stop }: StopContactSectionProps) {
  const contacts: ContactCardProps[] = [
    {
      name: stop.contact_name,
      label: 'Home',
      phone: stop.phone_primary,
    },
  ];
  if (stop.phone_secondary) {
    contacts.push({
      name: stop.contact_name,
      label: 'Phone',
      phone: stop.phone_secondary,
    });
  }

  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-h3 font-nunito-sans text-grey-500 font-bold">
        Contact
      </h3>
      <div className="flex flex-col gap-2">
        {contacts.map((contact) => (
          <ContactCard key={`${contact.label}-${contact.phone}`} {...contact} />
        ))}
      </div>
    </section>
  );
}
