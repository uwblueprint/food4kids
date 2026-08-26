import { Field, FieldLabel, Input } from '@/common/components';
import { formatPhone } from '@/common/utils';
import { cn } from '@/lib/utils';

import {
  isBlank,
  REQUIRED_SETTING_KEYS,
  type StringSettingKey,
} from '../settingsFields';
import { useSettingsForm } from '../useSettingsForm';

interface ContactField {
  /* Narrowed to string-valued settings: `keyof SystemSettingsUpdate` would also
   * admit numeric, boolean and array columns, and widen the value type enough
   * that writing a string to one of them would still type-check. */
  key: StringSettingKey;
  label: string;
  placeholder: string;
  type?: string;
  /** Display transform for a stored value that is not human-readable. */
  format?: (value: string) => string;
}

/* Order follows the design, which is also the order these appear in the email
 * footer: the ways to reach the org first, then its social links. */
const CONTACT_FIELDS: ContactField[] = [
  {
    key: 'f4k_wr_email',
    label: 'Email',
    placeholder: 'Enter email address',
    type: 'email',
  },
  {
    key: 'contact_phone',
    label: 'Phone Number',
    placeholder: 'Enter phone number',
    type: 'tel',
    /* Stored RFC 3966 ("tel:+1-519-576-3443;ext=1") is not what the design
     * shows. formatPhone renders it as "(519) 576-3443 Ext. 1" and returns
     * anything it does not recognise untouched, so text the admin is midway
     * through typing passes through unchanged. The backend re-normalises on
     * save, so only the display needs this. */
    format: formatPhone,
  },
  {
    key: 'f4k_wr_website',
    label: 'Website',
    placeholder: 'Enter website URL',
    type: 'url',
  },
  {
    key: 'f4k_wr_address',
    label: 'Address',
    placeholder: 'Enter address',
  },
  {
    key: 'f4k_wr_instagram',
    label: 'Instagram',
    placeholder: 'Paste Instagram page URL',
    type: 'url',
  },
  {
    key: 'f4k_wr_facebook',
    label: 'Facebook',
    placeholder: 'Paste Facebook page URL',
    type: 'url',
  },
  {
    key: 'f4k_wr_twitter',
    label: 'Twitter',
    placeholder: 'Paste Twitter page URL',
    type: 'url',
  },
];

export const ContactInformationPanel = () => {
  const { isEditing, getField, setField } = useSettingsForm();

  return (
    <div className="flex max-w-[600px] flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-h2 text-grey-500 font-bold">
          Food4Kids Waterloo Region
        </h2>
        <p className="text-p2 text-grey-400">
          Contact details entered here appear in the footer of every automated
          email to drivers.
        </p>
      </div>

      {CONTACT_FIELDS.map(({ key, label, placeholder, type, format }) => {
        const inputId = `settings-${key}`;
        // No cast: a StringSettingKey narrows the value to `string | null`.
        const stored = getField(key) ?? '';
        const required = (REQUIRED_SETTING_KEYS as readonly string[]).includes(
          key
        );
        // Only nag once they have actually emptied it, not on arrival.
        const error =
          isEditing && required && isBlank(stored)
            ? `${label} is required.`
            : undefined;
        return (
          <Field key={key}>
            <FieldLabel htmlFor={inputId} required={required}>
              {label}
            </FieldLabel>
            <Input
              id={inputId}
              type={type}
              /* readOnly rather than disabled: the saved value still needs to
               * read as content (and stay selectable / announced by screen
               * readers) outside edit mode. `disabled` would also dim it to
               * opacity-60, which the design does not do -- grey-150 on
               * grey-400 is the whole uneditable treatment. */
              readOnly={!isEditing}
              className={cn(
                !isEditing &&
                  // cursor-not-allowed is on `disabled:` in the shared
                  // Input, which readOnly never triggers -- so the
                  // "you cannot type here" cue has to be set explicitly.
                  'bg-grey-150 text-grey-400 cursor-not-allowed'
              )}
              /* Figma dev note: "Empty fields display nothing in the text
               * field." A placeholder prompts you to type, so it belongs to
               * edit mode only -- outside it an unset field stays blank
               * instead of looking pre-filled. */
              placeholder={isEditing ? placeholder : undefined}
              error={error}
              value={format ? format(stored) : stored}
              onChange={(event) =>
                // An emptied optional field clears the column rather than
                // storing "", which the model's min_length=1 would reject.
                setField(key, event.target.value || null)
              }
            />
          </Field>
        );
      })}
    </div>
  );
};
