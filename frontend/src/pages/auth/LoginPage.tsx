import { AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { type FormEvent, useState } from 'react';

import { useLogin } from '@/api';
import loginPageIllustration from '@/assets/illustrations/login-page-illustration.png';
import loginPageIllustrationMobile from '@/assets/illustrations/login-page-illustration-mobile.png';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import logoImgMobile from '@/assets/logos/logo_mobile_one_line.svg';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { cn } from '@/lib/utils';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loginError, setLoginError] = useState(false);

  const loginMutation = useLogin();

  const handleLogin = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoginError(false);
    loginMutation.mutate(
      { email, password },
      {
        onError: () => {
          setLoginError(true);
        },
      }
    );
  };

  return (
    <div className="desktop:overflow-hidden relative flex h-screen w-full flex-row overflow-auto">
      {/* Left Column: Form Section */}
      <div className="tablet:flex desktop:w-1/2 tablet:items-center tablet:justify-center desktop:justify-start desktop:pl-[8.5vw] w-full">
        <div className="tablet:pt-0 tablet:px-0 tablet:max-w-126 desktop:max-w-100 flex w-full flex-col gap-8 px-5 pt-16">
          {/* Logo and Heading */}
          <div className="flex-col">
            <div className="self-start">
              {/* Desktop Logo */}
              <img
                src={logoImg}
                alt="Food4Kids Waterloo Region Logo"
                className="desktop:block hidden h-26 w-auto object-contain"
              />
              {/* Mobile Logo */}
              <img
                src={logoImgMobile}
                alt="Food4Kids Waterloo Region Logo"
                className="desktop:hidden absolute top-5 left-5 h-7 w-auto"
              />
            </div>
            {/* Mobile Login Illustration */}
            <div className="desktop:hidden mb-6 flex flex-row items-center justify-center">
              <img
                src={loginPageIllustrationMobile}
                alt="Food4Kids Waterloo Region Illustration"
                className="h-[212px] w-[307px] object-contain"
              />
            </div>
            {/* Heading */}
            <h1>Hi there!</h1>
            <p className="text-m-p2 tablet:font-medium">
              Continue to access the app
            </p>
          </div>
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
                    <AlertTriangle className="h-4 w-4 shrink-0" />
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
                      className="text-p1 absolute top-1/2 right-4 -translate-y-1/2 cursor-pointer"
                      aria-label={
                        showPassword ? 'Hide password' : 'Show password'
                      }
                    >
                      {showPassword ? (
                        <EyeOff className="h-6 w-6" />
                      ) : (
                        <Eye className="h-6 w-6" />
                      )}
                    </button>
                  </div>
                  {loginError && (
                    <div className="text-red text-p2 flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
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
                  <a
                    href="/forgot-password"
                    className="text-m-p2 tablet:font-medium text-blue-300 hover:underline"
                    onClick={(e) => {
                      e.preventDefault();
                      // TODO: Implement forgot password action
                    }}
                  >
                    Forgot your password?
                  </a>
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
        </div>
      </div>

      {/* Right Column: Illustration Section */}
      <div className="desktop:block hidden h-full w-1/2 overflow-hidden">
        <img
          src={loginPageIllustration}
          alt="Food4Kids Illustration"
          className="h-full w-full object-cover"
        />
      </div>
    </div>
  );
};
