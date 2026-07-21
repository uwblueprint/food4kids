import { AlertTriangleIcon, CheckIcon, EyeOffIcon } from 'lucide-react';
import { type FormEvent, useState } from 'react';

import EyeIcon from '@/assets/icons/eye.svg?react';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

interface CreatePasswordFormProps {
  onSubmit: (password: string) => void;
  isPending: boolean;
  submitButtonText: string;
}

export const CreatePasswordForm = ({
  onSubmit,
  isPending,
  submitButtonText,
}: CreatePasswordFormProps) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState(false);

  const requirements = [
    {
      label: '8+ characters (12 or more is recommended)',
      isSatisfied: password.length >= 8,
    },
    {
      label: 'One uppercase and one lowercase letter',
      isSatisfied: /[a-z]/.test(password) && /[A-Z]/.test(password),
    },
    {
      label: 'One number',
      isSatisfied: /\d/.test(password),
    },
    {
      label: 'One special character (e.g. ! @ # $ %)',
      isSatisfied: /[^A-Za-z0-9]/.test(password),
    },
  ];

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
        <form
          id="register-form"
          className="flex flex-col gap-6"
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
              <div className="text-red text-p2 flex items-center gap-1.5">
                <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                <span>
                  {password
                    ? 'Please make sure all criteria is met'
                    : 'Please enter a password'}
                </span>
              </div>
            )}
          </Field>

          <div className="flex flex-col gap-4">
            {/* Confirm Password Field */}
            <Field>
              <FieldLabel htmlFor="password">Confirm password</FieldLabel>
              <div className="relative w-full">
                <Input
                  id="password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Enter your password"
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
                <div className="text-red text-p2 flex items-center gap-1.5">
                  <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                  <span>
                    {confirmPassword
                      ? 'Please make sure both passwords match'
                      : 'Please enter a password'}
                  </span>
                </div>
              )}
            </Field>
          </div>
        </form>

        {/* Password Requirements */}
        <div className="desktop:mt-5 mt-2">
          <p className="text-p2 mb-[3px] font-semibold">Password must be:</p>
          <ul className="space-y-[3px]">
            {requirements.map((req, index) => (
              <PasswordRequirement
                key={index}
                label={req.label}
                isSatisfied={req.isSatisfied}
              />
            ))}
          </ul>
        </div>

        {/* Create Account Button */}
        <div className="flex flex-col">
          <Button
            form="register-form"
            type="submit"
            variant="primary"
            shape="default"
            className="mt-12 w-full py-3"
            disabled={isPending}
          >
            {submitButtonText}
          </Button>
        </div>
      </div>
    </>
  );
};

interface PasswordRequirementProps {
  label: string;
  isSatisfied: boolean;
}

const PasswordRequirement = ({
  label,
  isSatisfied,
}: PasswordRequirementProps) => {
  return (
    <li className="text-p2 flex items-center gap-1 font-semibold">
      {isSatisfied ? (
        <CheckIcon
          className="h-4 w-4 shrink-0 text-green-500"
          strokeWidth={3}
        />
      ) : (
        // A little custom gray dot indicator when invalid
        <div className="flex h-4 w-4 shrink-0 items-center justify-center">
          <span className="h-1 w-1 rounded-full bg-black" />
        </div>
      )}
      <span
        className={cn(
          'transition-colors duration-200',
          isSatisfied ? 'text-success-stroke' : 'text-current'
        )}
      >
        {label}
      </span>
    </li>
  );
};
