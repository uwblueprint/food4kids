import { type FormEvent, useState } from 'react';

import loginPageIllustration from '@/assets/illustrations/login-page-illustration.png';
import loginPageIllustrationMobile from '@/assets/illustrations/login-page-illustration-mobile.png';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import logoImgMobile from '@/assets/logos/logo_mobile_one_line.png';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { Eye, EyeOff } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleLogin = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    console.log('Logging in with:', { email, password, rememberMe });
    // To be integrated with backend authentication once active
  };

  return (
    <div className="flex h-screen w-full flex-row overflow-auto lg:overflow-hidden">
      {/* Left Column: Form Section */}
      <div className="md:flex w-full lg:w-1/2 md:items-center lg:pl-30">
        <div className="flex px-5 pt-5 lg:px-0 w-full max-w-100 flex-col gap-8">
          {/* Logo and Heading */}
          <div className="flex-col">
            <div className="self-start">
              {/* Desktop Logo */}
              <img
                src={logoImg}
                alt="Food4Kids Waterloo Region Logo"
                className="hidden lg:block h-26 w-auto object-contain"
              />
              {/* Mobile Logo */}
              <img
                src={logoImgMobile}
                alt="Food4Kids Waterloo Region Logo"
                className="lg:hidden h-7 w-auto object-contain mb-4"
              />
            </div>
            {/* Mobile Login Illustration */}
            <div className="flex flex-row lg:hidden justify-center items-center px-4 mb-6">
              <img
                src={loginPageIllustrationMobile}
                alt="Food4Kids Waterloo Region Logo"
                className="w-full h-auto object-contain"
              />
            </div>
            {/* Heading */}
            <h1>
              Hi there!
            </h1>
            <p className="text-p2 lg:text-p1">
              Continue to access the app
            </p>
          </div>
          <div>
            {/* Form */}
            <form onSubmit={handleLogin} className="flex flex-col gap-6">
              {/* Email Field */}
              <Field>
                <FieldLabel htmlFor="email" className="text-h3">
                  Email
                </FieldLabel>
                <Input
                  id="email"
                  className="px-6"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </Field>

              <div className="flex flex-col gap-4">
                {/* Password Field */}
                <Field>
                  <FieldLabel htmlFor="password" className="text-h3">
                    Password
                  </FieldLabel>
                  <div className="relative w-full">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      className="px-6"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 cursor-pointer text-p1 focus:outline-none"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <EyeOff className="h-6 w-6" />
                      ) : (
                        <Eye className="h-6 w-6" />
                      )}
                    </button>
                  </div>
                </Field>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between">
                  <label className="flex cursor-pointer items-center gap-2 text-p1 font-medium select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="h-6 w-6 cursor-pointer rounded border-grey-300 text-blue-300 focus:ring-blue-300 accent-blue-300"
                    />
                    Remember me
                  </label>
                  <a
                    href="/forgot-password"
                    className="text-p1 font-medium text-blue-300 hover:underline"
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
              >
                Log in
              </Button>
            </form>

            {/* Footer */}
            <p className="mt-6 lg:mt-5 mb-8 lg:mb-0 text-center text-p1">
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
      <div className="hidden lg:block h-full w-1/2 overflow-hidden bg-[#d7f4fc]">
        <img
          src={loginPageIllustration}
          alt="Food4Kids Illustration"
          className="h-full w-full object-cover object-left-top"
        />
      </div>
    </div>
  );
};
