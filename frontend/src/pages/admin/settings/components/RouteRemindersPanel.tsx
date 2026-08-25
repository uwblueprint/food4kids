import type { EmailReminder } from '@/api/generated/types.gen';
import TrashIcon from '@/assets/icons/trash.svg?react';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Switch,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';

import {
  ADD_REMINDER_LIMIT_MESSAGE,
  createReminder,
  daysBeforeOptionsFor,
  formatDaysBefore,
  formatTimeLabel,
  MAX_REMINDERS,
  timeOptionsFor,
} from '../reminderOptions';
import { useSettingsForm } from '../useSettingsForm';

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
  const timeId = `reminder-${index}-time`;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-h3 text-grey-500 font-bold">
        Notification {index + 1}
      </h3>
      <div className="flex items-end gap-8">
        <div className="flex flex-col gap-1">
          <label htmlFor={daysId} className="text-p2 text-grey-400">
            How many days before?
          </label>
          <Dropdown
            value={String(reminder.days_before)}
            onValueChange={(value) =>
              onChange(index, { ...reminder, days_before: Number(value) })
            }
            disabled={!isEditing}
          >
            <DropdownTrigger id={daysId} className="w-[148px]">
              <DropdownValue />
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
          <label htmlFor={timeId} className="text-p2 text-grey-400">
            At what time?
          </label>
          <Dropdown
            value={reminder.time}
            onValueChange={(value) =>
              onChange(index, { ...reminder, time: value })
            }
            disabled={!isEditing}
          >
            <DropdownTrigger id={timeId} className="w-[126px]">
              <DropdownValue />
            </DropdownTrigger>
            <DropdownContent className="max-h-64 overflow-y-auto">
              {timeOptionsFor(reminder.time).map((time) => (
                <DropdownItem key={time} value={time}>
                  {formatTimeLabel(time)}
                </DropdownItem>
              ))}
            </DropdownContent>
          </Dropdown>
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

interface AnnouncementToggle {
  key: 'announcement_emails_to_admins' | 'announcement_emails_to_drivers';
  label: string;
}

const ANNOUNCEMENT_TOGGLES: AnnouncementToggle[] = [
  {
    key: 'announcement_emails_to_admins',
    label: 'Enable email notifications for admin',
  },
  {
    key: 'announcement_emails_to_drivers',
    label: 'Enable email notifications for drivers',
  },
];

/**
 * Audience filters for announcement emails.
 *
 * These do not send anything on their own -- they narrow who receives an
 * announcement that was already posted with email requested from the
 * announcements board. With both off, such a post emails no one.
 */
const AnnouncementsSection = () => {
  const { isEditing, getField, setField } = useSettingsForm();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-h2 text-grey-500 font-bold">Announcements</h2>
        <p className="text-p2 text-grey-400">
          Admins and drivers can be notified by email when announcements are
          posted.
        </p>
      </div>
      <div className="flex max-w-[420px] flex-col gap-2">
        {ANNOUNCEMENT_TOGGLES.map(({ key, label }) => {
          const switchId = `settings-${key}`;
          return (
            <div key={key} className="flex items-center justify-between gap-8">
              <label htmlFor={switchId} className="text-p1 text-grey-500">
                {label}
              </label>
              <Switch
                id={switchId}
                checked={getField(key) ?? true}
                onCheckedChange={(checked) => setField(key, checked)}
                disabled={!isEditing}
              />
            </div>
          );
        })}
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

      {isEditing &&
        /* The button stays mounted at the limit so the tooltip has a trigger to
         * hang off — a disabled button swallows pointer events, so the wrapper
         * span is what Radix listens on. */
        (isAtLimit ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="w-fit">
                <Button disabled className="w-fit">
                  Add notification
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent className="bg-grey-500 text-grey-100">
              {ADD_REMINDER_LIMIT_MESSAGE}
            </TooltipContent>
          </Tooltip>
        ) : (
          <Button onClick={addReminder} className="w-fit">
            Add notification
          </Button>
        ))}

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

      <AnnouncementsSection />
    </div>
  );
};
