import { ChevronLeftIcon } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useLogout } from '@/api/auth';
import { useAuthStore } from '@/api/authStore';
import { useDriver } from '@/api/drivers';
import { Button } from '@/common/components';

import { LogoutConfirmModal } from './LogoutConfirmModal';

export const DriverProfile = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const driverId = user?.driverId;

  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const logoutMutation = useLogout();

  const { data: driverDetails } = useDriver(driverId || '');

  const firstName = user?.firstName || driverDetails?.first_name || '';
  const lastName = user?.lastName || driverDetails?.last_name || '';
  const email = user?.email || driverDetails?.email || '';
  const phone = driverDetails?.phone || 'Not provided';
  const address = driverDetails?.address || 'Not provided';

  const capitalize = (s: string) =>
    s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : '';
  const fullName =
    user?.fullName ||
    `${capitalize(firstName)} ${capitalize(lastName)}`.trim() ||
    'Driver Profile';

  const initials =
    `${firstName.charAt(0) || ''}${lastName.charAt(0) || ''}`.toUpperCase() ||
    'D';

  const handleLogoutClick = () => {
    setIsLogoutModalOpen(true);
  };

  const handleConfirmLogout = () => {
    logoutMutation.mutate(undefined, {
      onSettled: () => {
        setIsLogoutModalOpen(false);
        navigate('/login');
      },
    });
  };

  const handleChangePassword = () => {
    navigate('/forgot-password');
  };

  return (
    <main className="flex flex-col items-center gap-6 mx-auto w-full">
      <Link
        to="/driver/home"
        className="flex items-center gap-1 text-blue-400 self-start"
      >
        <ChevronLeftIcon className="size-6" />
        <h2>Back to home</h2>
      </Link>

      <div className="flex flex-col items-center gap-1">
        {/* 1. Profile circle showing initials */}
        <div className="flex size-26 items-center justify-center rounded-full bg-blue-300 text-white">
          <h1 className="text-[42.545px]">{initials}</h1>
        </div>

        {/* 2. Full name properly capitalized */}
        <h1 className="font-bold text-grey-500 text-center">
          {fullName}
        </h1>
      </div>
      

      {/* 3. Email subheading on the left, followed by a field */}
      <div className="flex flex-col gap-2 w-full">
        <h2>Email</h2>
        <div className="w-full bg-grey-150 rounded-[8px] p-3 text-p1">
          {email || 'No email specified'}
        </div>
      </div>

      {/* 4. Phone number subheading on the left, followed by a field below it */}
      <div className="flex flex-col gap-2 w-full">
        <h2>Phone number</h2>
        <div className="w-full bg-grey-150 rounded-[8px] p-3 text-p1">
          {phone}
        </div>
      </div>

      {/* 5. Address subheading on the left, followed by a field below it */}
      <div className="flex flex-col gap-2 w-full">
        <h2>Address</h2>
        <div className="w-full bg-grey-150 rounded-[8px] p-3 text-p1">
          {address}
        </div>
      </div>

      {/* 6. A flex row div, inside it two buttons: left "Change password", right "Logout" */}
      <div className="flex flex-row gap-4 w-full">
        <Button
          variant="secondary"
          className="flex-1"
          onClick={handleChangePassword}
        >
          Change password
        </Button>
        <Button
          className="flex-1"
          onClick={handleLogoutClick}
        >
          Logout
        </Button>
      </div>

      <LogoutConfirmModal
        open={isLogoutModalOpen}
        onOpenChange={setIsLogoutModalOpen}
        onConfirm={handleConfirmLogout}
        isLoading={logoutMutation.isPending}
      />
    </main>
  );
};
