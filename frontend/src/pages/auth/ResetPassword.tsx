import { useRegisterDriver } from '@/api/auth';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { WrapperWithLogo } from './Wrapper';
import { Navigate, useNavigate } from 'react-router-dom';
import { CreatePasswordForm } from './CreatePasswordForm';

export const ResetPassword = () => {
  const headerTitle = "Rest your password";
  const subheaderTitle = "Create an password to access the app";

  const { token } = useParams();

  if (!token) {
    return <Navigate to="/404" replace />;
  }

  const { mutate, isPending } = useRegisterDriver();

  const handleRegister = (password: string) => {
    mutate(
      {
        user_invite_id: token,
        password: password,
      },
      {
        onSuccess: () => {},
      }
    );
  };

  return (
    <WrapperWithLogo headerTitle={headerTitle} subheaderTitle={subheaderTitle} className="desktop:max-w-[362px]">
      <CreatePasswordForm 
        onSubmit={handleRegister} 
        isPending={isPending} 
        submitButtonText="Create account"
      />
    </WrapperWithLogo>
  );
}
