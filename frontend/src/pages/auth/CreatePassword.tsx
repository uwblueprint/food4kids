import axios from 'axios';
import { type FormEvent, useState } from 'react';
import { useParams } from 'react-router-dom';
import { WrapperWithLogo } from './Wrapper';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { AlertTriangleIcon, CheckIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import EyeIcon from '@/assets/icons/eye.svg?react';
import { EyeOffIcon } from 'lucide-react';

export const CreatePassword = () => {
  return (
    <WrapperWithLogo headerTitle="Create a password" subheaderTitle="Create an account to access the app">
      <CreatePasswordForm/>
    </WrapperWithLogo>
  );
}

const CreatePasswordForm = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [feedback, setFeedback] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { token } = useParams();
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
      isSatisfied: /[^A-Za-z0-9]/.test(password), // checks for any non-alphanumeric char
    },
  ];


  const submitPassword = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFeedback('Connecting...');

    try {
      // Axios handles JSON stringification automatically
      const response = await axios.post(
        'http://localhost:8080/drivers/register',
        {
          user_invite_id: token,
          password: password,
        }
      );

      console.log('Backend response:', response.data);
      setFeedback('Success: Password recorded.');
      setPassword(''); // Clear input on success
    } catch (err) {
      // Axios catches 4xx/5xx errors automatically
      let errorMessage = 'Server unreachable';
      if (axios.isAxiosError(err)) {
        errorMessage = err.response?.data?.message || errorMessage;
      }
      setFeedback(`Error: ${errorMessage}`);
    }
  };

  return (
    <>
      <div>
        {/* Form */}
        <form className="flex flex-col gap-6">
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
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-p1 absolute top-1/2 right-6 -translate-y-1/2 cursor-pointer"
                aria-label={
                  showPassword ? 'Hide password' : 'Show password'
                }
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
                <span>Incorrect email or password</span>
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
                    passwordError && 'outline-red focus:outline-red'
                  )}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setPasswordError(false);
                  }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-p1 absolute top-1/2 right-6 -translate-y-1/2 cursor-pointer"
                  aria-label={
                    showPassword ? 'Hide password' : 'Show password'
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOffIcon className="h-6 w-6" />
                  ) : (
                    <EyeIcon className="h-6 w-6" />
                  )}
                </button>
              </div>
              {passwordError && (
                <div className="text-red text-p2 flex items-center gap-1.5">
                  <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                  <span>Incorrect email or password</span>
                </div>
              )}
            </Field>
          </div>
        </form>

        {/* Password Requirements */}
        <div className="mt-2 desktop:mt-5">
          <p className="mb-[3px] text-p2 font-semibold">Password must be:</p>
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
            type="submit"
            variant="primary"
            shape="default"
            className="mt-12 w-full py-3"
          >
            Create account
          </Button>
        </div>
        
        

        {/* Footer */}
        <p className="desktop:mt-5 text-m-p2 tablet:font-medium tablet:mb-0 mt-6 mb-8 text-center">
          <a
            href="/login"
            className="text-blue-300 hover:underline"
            onClick={(e) => {
              e.preventDefault();
              // TODO: Implement get login link action
            }}
          >
            Return to login
          </a>
        </p>
      </div>
    </>
  )
};

interface PasswordRequirementProps {
  label: string;
  isSatisfied: boolean;
}

const PasswordRequirement = ({ label, isSatisfied }: PasswordRequirementProps) => {
  return (
    <li className="flex items-center gap-1 text-p2 font-semibold">
      {isSatisfied ? (
        // Green checkmark when valid
        <CheckIcon className="h-4 w-4 shrink-0 text-green-500" strokeWidth={3} />
      ) : (
        // A little custom gray dot indicator when invalid
        <div className="flex h-4 w-4 shrink-0 items-center justify-center">
          <span className="h-1 w-1 rounded-full bg-black" />
        </div>
      )}
      <span className={cn(
        "transition-colors duration-200", 
        isSatisfied ? "text-gray-500 line-through font-normal" : "text-current"
      )}>
        {label}
      </span>
    </li>
  );
};
