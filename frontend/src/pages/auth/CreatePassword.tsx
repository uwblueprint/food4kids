import axios from 'axios';
import { type FormEvent, useState } from 'react';
import { useParams } from 'react-router-dom';
import { WrapperWithLogo } from './Wrapper';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { AlertTriangleIcon } from 'lucide-react';
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
  const [createPasswordError, setCreatePasswordError] = useState(false);


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
            <FieldLabel htmlFor="email">Enter new password</FieldLabel>
            <Input
              id="email"
              className={cn(
                'px-6',
                createPasswordError && 'outline-red focus:outline-red'
              )}
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setCreatePasswordError(false);
              }}
              required
            />
            {createPasswordError && (
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
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  className={cn(
                    'px-6',
                    createPasswordError && 'outline-red focus:outline-red'
                  )}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setCreatePasswordError(false);
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
              {createPasswordError && (
                <div className="text-red text-p2 flex items-center gap-1.5">
                  <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                  <span>Incorrect email or password</span>
                </div>
              )}
            </Field>
          </div>

          {/* Log In Button */}
          <Button
            type="submit"
            variant="primary"
            shape="default"
            className="mt-6 w-full py-3"
          >
            Log in
          </Button>
        </form>

        {/* Footer */}
        <p className="desktop:mt-5 text-m-p2 tablet:font-medium tablet:mb-0 mt-6 mb-8 text-center">
          Don't have an account?{' '}
          <a
            href="/get-login-link"
            className="text-blue-300 hover:underline"
            onClick={(e) => {
              e.preventDefault();
              // TODO: Implement get login link action
            }}
          >
            Get your login link
          </a>
        </p>
      </div>
    </>
  )
};
