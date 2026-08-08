import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '@/api/authStore';
import { useDriver } from '@/api/drivers';
import { Button } from '@/common/components';

export const DriverProfile = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const driverId = user?.driverId;

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

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  const handleChangePassword = () => {
    navigate('/forgot-password');
  };

  return (
    <main className="flex flex-col items-center gap-8 mx-auto w-full max-w-[770px] py-8 px-4">
      <div className="flex flex-col items-center gap-4 w-full">
        {/* 1. Profile circle showing initials */}
        <div className="flex size-24 items-center justify-center rounded-full bg-blue-300 font-bold text-white text-3xl shadow-sm">
          {initials}
        </div>

        {/* 2. Full name properly capitalized */}
        <h1 className="font-bold text-grey-500 text-center">
          {fullName}
        </h1>
      </div>

      <div className="flex flex-col gap-6 w-full">
        {/* 3. Email subheading on the left, followed by a field */}
        <div className="flex flex-col gap-1.5 w-full">
          <h2>Email</h2>
          <div className="w-full bg-grey-100 border border-grey-300 rounded-[12px] px-4 py-3 text-p2 text-grey-500">
            {email || 'No email specified'}
          </div>
        </div>

        {/* 4. Phone number subheading on the left, followed by a field below it */}
        <div className="flex flex-col gap-1.5 w-full">
          <h2>Phone Number</h2>
          <div className="w-full bg-grey-100 border border-grey-300 rounded-[12px] px-4 py-3 text-p2 text-grey-500">
            {phone}
          </div>
        </div>

        {/* 5. Address subheading on the left, followed by a field below it */}
        <div className="flex flex-col gap-1.5 w-full">
          <h2>Address</h2>
          <div className="w-full bg-grey-100 border border-grey-300 rounded-[12px] px-4 py-3 text-p2 text-grey-500">
            {address}
          </div>
        </div>
      </div>

      {/* 6. A flex row div, inside it two buttons: left "Change password", right "Logout" */}
      <div className="flex flex-row gap-4 w-full mt-4">
        <Button
          variant="secondary"
          className="flex-1"
          onClick={handleChangePassword}
        >
          Change password
        </Button>
        <Button
          className="flex-1"
          onClick={handleLogout}
        >
          Logout
        </Button>
      </div>
    </main>
  );
};
