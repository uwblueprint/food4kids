import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useLogin } from '@/api';
import AlertTriangleIcon from '@/assets/icons/alert-triangle.svg?react';
import EyeIcon from '@/assets/icons/eye.svg?react';
import EyeOffIcon from '@/assets/icons/eye-off.svg?react';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

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

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loginError, setLoginError] = useState(false);

  const loginMutation = useLogin();
  const navigate = useNavigate();

  const handleLogin = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoginError(false);
    loginMutation.mutate(
      { email, password },
      {
        onSuccess: () => {
          navigate('/'); // 3. Navigate to base route on success
        },
        onError: () => {
          setLoginError(true);
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
                loginError && 'outline-red focus:outline-red'
              )}
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setLoginError(false);
              }}
              required
            />
            {loginError && (
              <div className="text-red text-p2 flex items-center gap-1.5">
                <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                <span>Incorrect email or password</span>
              </div>
            )}
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
                    loginError && 'outline-red focus:outline-red'
                  )}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setLoginError(false);
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
              {loginError && (
                <div className="text-red text-p2 flex items-center gap-1.5">
                  <AlertTriangleIcon className="h-4 w-4 shrink-0" />
                  <span>Incorrect email or password</span>
                </div>
              )}
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
