import { EyeOffIcon } from 'lucide-react';
import { type FormEvent, useState } from 'react';

import EyeIcon from '@/assets/icons/eye.svg?react';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

import { ErrorNote } from './ErrorNote';
import { PasswordRequirementsList } from './PasswordRequirements';
import { getPasswordRequirements } from './passwordUtils';

interface CreatePasswordFormProps {
  onSubmit: (password: string) => void;
  isPending: boolean;
  submitButtonText: string;
  /** Why the last submission failed, if it did. Nothing to do with the fields. */
  submitError?: string | null;
}

export const CreatePasswordForm = ({
  onSubmit,
  isPending,
  submitButtonText,
  submitError,
}: CreatePasswordFormProps) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState(false);

  const requirements = getPasswordRequirements(password);
  const allRequirementsMet = requirements.every((req) => req.isSatisfied);

  const submitPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const isPasswordInvalid = !password || !allRequirementsMet;
    const isConfirmInvalid = !confirmPassword || password !== confirmPassword;

    if (isPasswordInvalid) {
      setPasswordError(true);
    }

    if (isConfirmInvalid) {
      setConfirmPasswordError(true);
    }

    if (isPasswordInvalid || isConfirmInvalid) {
      return;
    }

    onSubmit(password);
  };

  return (
    <>
      <div>
        {/* Form */}
        {/* Field gap / button gap: 32/40 below desktop, 24/48 at desktop. */}
        <form
          id="register-form"
          className="desktop:gap-6 flex flex-col gap-8"
          onSubmit={submitPassword}
        >
          {/* Password Field */}
          <Field>
            <FieldLabel htmlFor="password">Enter new password</FieldLabel>
            <div className="relative w-full">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
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
                  ? 'Please make sure all password criteria is met'
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

        {/* Create Account Button */}
        <div className="flex flex-col">
          {submitError && <ErrorNote className="mt-6">{submitError}</ErrorNote>}
          <Button
            form="register-form"
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
