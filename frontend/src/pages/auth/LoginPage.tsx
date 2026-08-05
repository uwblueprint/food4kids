import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { describeApiFailure, useLogin } from '@/api';
import EyeIcon from '@/assets/icons/eye.svg?react';
import EyeOffIcon from '@/assets/icons/eye-off.svg?react';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

import { ErrorNote } from './ErrorNote';
import { WrapperWithLogo } from './Wrapper';

export const LoginPage = () => {
  return (
    <WrapperWithLogo
      headerTitle="Hi there!"
      subheaderTitle="Continue to access the app"
    >
      <LoginForm />
    </WrapperWithLogo>
  );
};

/**
 * `credentials` is the only failure the fields are guilty of, so it is the only
 * one that reddens them. A login the server never answered gets a single
 * form-level note instead, because the email and password may well be correct.
 */
type LoginError = {
  scope: 'credentials' | 'form';
  message: string;
};

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<LoginError | null>(null);

  const credentialsError = error?.scope === 'credentials';

  const loginMutation = useLogin();
  const navigate = useNavigate();

  const handleLogin = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    loginMutation.mutate(
      { email, password },
      {
        onSuccess: (data) => {
          // Redirect based on user role
          if (data.role === 'driver') {
            navigate('/driver/home');
          } else {
            navigate('/admin/home');
          }
        },
        onError: (failure) => {
          const connectionMessage = describeApiFailure(failure);
          setError(
            connectionMessage
              ? { scope: 'form', message: connectionMessage }
              : {
                  scope: 'credentials',
                  message: 'Incorrect email or password',
                }
          );
        },
      }
    );
  };

  return (
    <>
      <div>
        {/* Form */}
        <form onSubmit={handleLogin} className="flex flex-col gap-6">
          {/* Email Field */}
          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              className={cn(
                'px-6',
                credentialsError && 'outline-red focus:outline-red'
              )}
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError(null);
              }}
              required
            />
            {credentialsError && <ErrorNote>{error.message}</ErrorNote>}
          </Field>

          <div className="flex flex-col gap-4">
            {/* Password Field */}
            <Field>
              <FieldLabel htmlFor="password">Password</FieldLabel>
              <div className="relative w-full">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  className={cn(
                    'px-6',
                    credentialsError && 'outline-red focus:outline-red'
                  )}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError(null);
                  }}
                  required
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
              {credentialsError && <ErrorNote>{error.message}</ErrorNote>}
            </Field>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <label className="text-m-p2 tablet:font-medium flex cursor-pointer items-center gap-2 select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="border-grey-300 h-6 w-6 cursor-pointer rounded text-blue-300 accent-blue-300 focus:ring-blue-300"
                />
                Remember me
              </label>
              <Link
                to="/forgot-password"
                className="text-m-p2 tablet:font-medium text-blue-300 hover:underline"
              >
                Forgot your password?
              </Link>
            </div>
          </div>

          {/* Failures that aren't the credentials' fault get one note for the
              whole form, not a red outline on fields that may be perfectly fine. */}
          {error?.scope === 'form' && (
            <ErrorNote className="-mb-4">{error.message}</ErrorNote>
          )}

          {/* Log In Button */}
          <Button
            type="submit"
            variant="primary"
            shape="default"
            className="mt-6 w-full py-3"
            disabled={loginMutation.isPending}
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
  );
};
