import { type FormEvent, useState } from 'react';

import { useForgotPassword } from '@/api';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { WrapperWithLogo } from './Wrapper';
import { Link } from 'react-router-dom';

export const ForgotPassword = () => {
  return (
    <WrapperWithLogo 
      headerTitle="Forgot password?" 
      subheaderTitle="What email did your admin use to sign you up?"
      className="desktop:max-w-[362px]"
    >
      <ForgotPasswordForm/>
    </WrapperWithLogo>
  );
}

const ForgotPasswordForm = () => {
  const [email, setEmail] = useState('');

  const forgotPasswordMutation = useForgotPassword();

  const handleForgotPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    forgotPasswordMutation.mutate(
      { email },
      {
        onSuccess: () => {
          alert('Check your inbox for a reset link!'); 
        },
      }
    );
  };

  return (
    <>
      <div>
        {/* Form */}
        <form onSubmit={handleForgotPassword} className="flex flex-col gap-6">
          {/* Email Field */}
          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              className='px-6'
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
              required
            />
          </Field>

          {/* Send Link Button */}
          <Button
            type="submit"
            variant="primary"
            shape="default"
            className="mt-6 w-full py-3"
            disabled={forgotPasswordMutation.isPending}
          >
            Send link
          </Button>
        </form>

        {/* Footer */}
        <p className="desktop:mt-5 text-m-p2 tablet:font-medium tablet:mb-0 mt-6 mb-8 text-center">
          <Link
            to="/login"
            className="text-blue-300 hover:underline"
          >
            Return to login
          </Link>
        </p>
      </div>
    </>
  )
}
