import { EyeOffIcon } from 'lucide-react';
import { type FormEvent, useState } from 'react';

import EyeIcon from '@/assets/icons/eye.svg?react';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

import { ErrorNote } from './ErrorNote';
import { PasswordRequirementsList } from './PasswordRequirements';
import { getPasswordRequirements } from './passwordUtils';

interface UpdatePasswordFormProps {
  onSubmit: (currentPassword: string, newPassword: string) => void;
  isPending: boolean;
  submitButtonText: string;
  /** Why the last submission failed, if it did. Nothing to do with the fields. */
  submitError?: string | null;
}

export const UpdatePasswordForm = ({
  onSubmit,
  isPending,
  submitButtonText,
  submitError,
}: UpdatePasswordFormProps) => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [currentPasswordError, setCurrentPasswordError] = useState(false);
  const [passwordError, setPasswordError] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState(false);

  const requirements = getPasswordRequirements(password);
  const allRequirementsMet = requirements.every((req) => req.isSatisfied);

  const submitPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const isCurrentInvalid = !currentPassword;
    const isPasswordInvalid = !password || !allRequirementsMet;
    const isConfirmInvalid = !confirmPassword || password !== confirmPassword;

    if (isCurrentInvalid) {
      setCurrentPasswordError(true);
    }

    if (isPasswordInvalid) {
      setPasswordError(true);
    }

    if (isConfirmInvalid) {
      setConfirmPasswordError(true);
    }

    if (isCurrentInvalid || isPasswordInvalid || isConfirmInvalid) {
      return;
    }

    onSubmit(currentPassword, password);
  };

  return (
    <>
      <div>
        {/* Form */}
        {/* Field gap / button gap: 32/40 below desktop, 24/48 at desktop. */}
        <form
          id="update-password-form"
          className="desktop:gap-6 flex flex-col gap-8"
          onSubmit={submitPassword}
        >
          {/* Current Password Field */}
          <Field>
            <FieldLabel htmlFor="current-password">Enter current password</FieldLabel>
            <div className="relative w-full">
              <Input
                id="current-password"
                type={showCurrentPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Enter your current password"
                className={cn(
                  'px-6',
                  currentPasswordError && 'outline-red focus:outline-red'
                )}
                value={currentPassword}
                onChange={(e) => {
                  setCurrentPassword(e.target.value);
                  setCurrentPasswordError(false);
                }}
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="text-p1 absolute top-1/2 right-6 -translate-y-1/2 cursor-pointer"
                aria-label={
                  showCurrentPassword ? 'Hide password' : 'Show password'
                }
              >
                {showCurrentPassword ? (
                  <EyeOffIcon className="h-6 w-6" />
                ) : (
                  <EyeIcon className="h-6 w-6" />
                )}
              </button>
            </div>
            {currentPasswordError && (
              <ErrorNote>Please enter your current password</ErrorNote>
            )}
          </Field>

          {/* New Password Field */}
          <Field>
            <FieldLabel htmlFor="password">Enter new password</FieldLabel>
            <div className="relative w-full">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="Enter your password"
                className={cn(
                  'px-6',
                  passwordError && 'outline-red focus:outline-red'
                )}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setPasswordError(false);
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-p1 absolute top-1/2 right-6 -translate-y-1/2 cursor-pointer"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOffIcon className="h-6 w-6" />
                ) : (
                  <EyeIcon className="h-6 w-6" />
                )}
              </button>
            </div>
            {passwordError && (
              <ErrorNote>
                {password
                  ? 'Please make sure all criteria is met'
                  : 'Please enter a password'}
              </ErrorNote>
            )}
          </Field>

          <div className="flex flex-col gap-4">
            {/* Confirm Password Field */}
            <Field>
              <FieldLabel htmlFor="confirm-password">
                Confirm password
              </FieldLabel>
              <div className="relative w-full">
                <Input
                  id="confirm-password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="Confirm your password"
                  className={cn(
                    'px-6',
                    confirmPasswordError && 'outline-red focus:outline-red'
                  )}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setConfirmPasswordError(false);
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-p1 absolute top-1/2 right-6 -translate-y-1/2 cursor-pointer"
                  aria-label={
                    showConfirmPassword ? 'Hide password' : 'Show password'
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOffIcon className="h-6 w-6" />
                  ) : (
                    <EyeIcon className="h-6 w-6" />
                  )}
                </button>
              </div>
              {confirmPasswordError && (
                <ErrorNote>
                  {confirmPassword
                    ? 'Please make sure both passwords match'
                    : 'Please enter a password'}
                </ErrorNote>
              )}
            </Field>
          </div>
        </form>

        {/* Password Requirements */}
        <PasswordRequirementsList password={password} />

        {/* Submit Button */}
        <div className="flex flex-col">
          {submitError && <ErrorNote className="mt-6">{submitError}</ErrorNote>}
          <Button
            form="update-password-form"
            type="submit"
            variant="primary"
            shape="default"
            className={cn(
              'w-full py-3',
              submitError ? 'mt-4' : 'desktop:mt-12 mt-10'
            )}
            disabled={isPending}
          >
            {submitButtonText}
          </Button>
        </div>
      </div>
    </>
  );
};
