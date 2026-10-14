import type { EmailReminder } from '@/api/generated/types.gen';
import TrashIcon from '@/assets/icons/trash.svg?react';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  FieldLabel,
  TimePicker,
} from '@/common/components';
import { fromApiTime, toApiTime } from '@/common/utils';

import {
  ADD_REMINDER_LIMIT_MESSAGE,
  createReminder,
  daysBeforeOptionsFor,
  formatDaysBefore,
  MAX_REMINDERS,
  UNSET_DAYS_BEFORE,
} from '../reminderOptions';
import { useSettingsForm } from '../useSettingsForm';
import { BlockedButton } from './BlockedButton';

interface ReminderRowProps {
  reminder: EmailReminder;
  index: number;
  isEditing: boolean;
  onChange: (index: number, next: EmailReminder) => void;
  onRemove: (index: number) => void;
}

const ReminderRow = ({
  reminder,
  index,
  isEditing,
  onChange,
  onRemove,
}: ReminderRowProps) => {
  const daysId = `reminder-${index}-days`;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-h3 text-grey-500 font-bold">
        Notification {index + 1}
      </h3>
      <div className="flex items-end gap-8">
        <div className="flex flex-col gap-1">
          <FieldLabel
            htmlFor={daysId}
            required
            className="text-p2 text-grey-400 font-normal"
          >
            How many days before?
          </FieldLabel>
          <Dropdown
            value={
              reminder.days_before === UNSET_DAYS_BEFORE
                ? ''
                : String(reminder.days_before)
            }
            onValueChange={(value) =>
              onChange(index, { ...reminder, days_before: Number(value) })
            }
            disabled={!isEditing}
          >
            <DropdownTrigger id={daysId} className="w-[148px]">
              <DropdownValue placeholder="Select" />
            </DropdownTrigger>
            <DropdownContent>
              {daysBeforeOptionsFor(reminder.days_before).map((days) => (
                <DropdownItem key={days} value={String(days)}>
                  {formatDaysBefore(days)}
                </DropdownItem>
              ))}
            </DropdownContent>
          </Dropdown>
        </div>

        <div className="flex flex-col gap-1">
          {/* No htmlFor: TimePicker takes no id, same as the other call sites. */}
          <FieldLabel required className="text-p2 text-grey-400 font-normal">
            At what time?
          </FieldLabel>
          <TimePicker
            value={fromApiTime(reminder.time)}
            onChange={(value) =>
              onChange(index, { ...reminder, time: toApiTime(value) })
            }
            disabled={!isEditing}
            padding={24}
            className="w-[126px]"
          />
        </div>

        {isEditing && (
          <Button
            variant="destructive"
            shape="circular"
            onClick={() => onRemove(index)}
            aria-label={`Remove notification ${index + 1}`}
          >
            <TrashIcon className="size-5" />
          </Button>
        )}
      </div>
    </div>
  );
};

export const RouteRemindersPanel = () => {
  const { isEditing, getField, setField } = useSettingsForm();
  const reminders = getField('email_reminders') ?? [];
  const isAtLimit = reminders.length >= MAX_REMINDERS;

  const replaceAt = (index: number, next: EmailReminder) => {
    setField(
      'email_reminders',
      reminders.map((reminder, i) => (i === index ? next : reminder))
    );
  };

  const removeAt = (index: number) => {
    setField(
      'email_reminders',
      reminders.filter((_, i) => i !== index)
    );
  };

  const addReminder = () => {
    setField('email_reminders', [...reminders, createReminder()]);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-h2 text-grey-500 font-bold">
          Automated Route Reminders
        </h2>
        <p className="text-p2 text-grey-400">
          Email reminders can be sent to drivers before their routes. Up to
          three notifications can be set.
        </p>
      </div>

      {isEditing && (
        <BlockedButton
          onClick={addReminder}
          blockedReason={isAtLimit ? ADD_REMINDER_LIMIT_MESSAGE : null}
          className="w-fit"
        >
          Add notification
        </BlockedButton>
      )}

      {reminders.map((reminder, index) => (
        <ReminderRow
          key={index}
          reminder={reminder}
          index={index}
          isEditing={isEditing}
          onChange={replaceAt}
          onRemove={removeAt}
        />
      ))}
    </div>
  );
};
