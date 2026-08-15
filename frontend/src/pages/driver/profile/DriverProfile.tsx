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

  const { data: driverDetails } = useDriver(driverId || '', !!driverId);

  const firstName = user?.firstName || driverDetails?.first_name || '';
  const lastName = user?.lastName || driverDetails?.last_name || '';
  const email = user?.email || driverDetails?.email || '';
  const phone = driverDetails?.phone || 'Not provided';
  const address = driverDetails?.address || 'Not provided';

  const fullName = user?.fullName || 'Driver Profile';

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
    navigate('/driver/profile/update-password');
  };

  return (
    <>
      <main className="desktop:justify-start mx-auto flex w-full flex-1 flex-col items-center justify-between gap-6">
        <div className="flex w-full flex-col items-center gap-6">
          <Link
            to="/driver/home"
            className="flex gap-1 self-start text-blue-400"
          >
            <ChevronLeftIcon className="size-6" />
            <h2>Back to home</h2>
          </Link>

          <div className="tablet:mt-0 mt-3 flex flex-col items-center gap-1">
            {/* 1. Profile circle showing initials */}
            <div className="desktop:size-26 flex size-16 items-center justify-center rounded-full bg-blue-300 text-white">
              <h1 className="desktop:text-[42.545px] text-[26.182px]">
                {initials}
              </h1>
            </div>

            {/* 2. Full name properly capitalized */}
            <h1 className="text-grey-500 text-center font-bold">{fullName}</h1>
          </div>

          {/* 3. Email subheading on the left, followed by a field */}
          <div className="flex w-full flex-col gap-2">
            <h2>Email</h2>
            <div className="bg-grey-150 text-p1 w-full rounded-[8px] p-3">
              {email || 'No email specified'}
            </div>
          </div>

          {/* 4. Phone number subheading on the left, followed by a field below it */}
          <div className="flex w-full flex-col gap-2">
            <h2>Phone number</h2>
            <div className="bg-grey-150 text-p1 w-full rounded-[8px] p-3">
              {phone}
            </div>
          </div>

          {/* 5. Address subheading on the left, followed by a field below it */}
          <div className="flex w-full flex-col gap-2">
            <h2>Address</h2>
            <div className="bg-grey-150 text-p1 w-full rounded-[8px] p-3">
              {address}
            </div>
          </div>
        </div>

        {/* 6. A flex row div, inside it two buttons: left "Change password", right "Logout" */}
        <div className="desktop:flex-row flex w-full flex-col gap-4">
          <Button
            variant="secondary"
            className="desktop:flex-1"
            onClick={handleChangePassword}
          >
            Change password
          </Button>
          <Button className="desktop:flex-1" onClick={handleLogoutClick}>
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
    </>
  );
};
