import { ChevronLeftIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useLogout } from '@/api/auth';
import { useAuthStore, type User } from '@/api/authStore';
import { useDriver, useUpdateDriver } from '@/api/drivers';
import { type DriverRead } from '@/api/generated';
import {
  Banner,
  Button,
  ConfirmModal,
  Input,
  Spinner,
} from '@/common/components';

import { UnsavedChangesModal } from './UnsavedChangesModal';

interface DriverProfileLoadedProps {
  driverDetails: DriverRead;
  driverId: string;
  user: User;
}

const DriverProfileLoaded = ({
  driverDetails,
  driverId,
  user,
}: DriverProfileLoadedProps) => {
  const navigate = useNavigate();

  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [isUnsavedModalOpen, setIsUnsavedModalOpen] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<
    (() => void) | null
  >(null);

  const logoutMutation = useLogout();
  const updateDriverMutation = useUpdateDriver(driverId);

  const [phoneInput, setPhoneInput] = useState(driverDetails.phone || '');
  const [addressInput, setAddressInput] = useState(driverDetails.address || '');

  const hasUnsavedChanges =
    phoneInput !== (driverDetails.phone || '') ||
    addressInput !== (driverDetails.address || '');

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  const firstName = user.firstName;
  const lastName = user.lastName;
  const email = user.email;
  const fullName = user.fullName;
  const initials = `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();

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

  const confirmNavigation = (action: () => void) => {
    if (hasUnsavedChanges) {
      setPendingNavigation(() => action);
      setIsUnsavedModalOpen(true);
    } else {
      action();
    }
  };

  const handleChangePassword = () => {
    confirmNavigation(() => {
      navigate('/driver/profile/update-password');
    });
  };

  const handleSaveChanges = () => {
    if (!driverId) return;
    updateDriverMutation.mutate({
      path: { driver_id: driverId },
      body: {
        phone: phoneInput,
        address: addressInput,
      },
    });
  };

  const handleDiscardChanges = () => {
    setPhoneInput(driverDetails.phone || '');
    setAddressInput(driverDetails.address || '');
    setIsUnsavedModalOpen(false);
    if (pendingNavigation) {
      pendingNavigation();
      setPendingNavigation(null);
    }
  };

  const handleKeepEditing = () => {
    setIsUnsavedModalOpen(false);
    setPendingNavigation(null);
  };

  return (
    <>
      <main className="desktop:justify-start mx-auto flex w-full flex-1 flex-col items-center justify-between gap-6">
        <div className="flex w-full flex-col items-center gap-6">
          <Link
            to="/driver/home"
            className="flex gap-1 self-start text-blue-400"
            onClick={(e) => {
              if (hasUnsavedChanges) {
                e.preventDefault();
                confirmNavigation(() => navigate('/driver/home'));
              }
            }}
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
            <div className="text-p2 w-full">{email}</div>
          </div>

          {/* 4. Phone number subheading on the left, followed by a field below it */}
          <div className="flex w-full flex-col gap-2">
            <h2>Phone number</h2>
            <Input
              className="bg-grey-150 text-p2 w-full rounded-[8px] p-3"
              value={phoneInput}
              onChange={(e) => setPhoneInput(e.target.value)}
            />
          </div>

          {/* 5. Address subheading on the left, followed by a field below it */}
          <div className="flex w-full flex-col gap-2">
            <h2>Address</h2>
            <Input
              className="bg-grey-150 text-p2 w-full rounded-[8px] p-3"
              value={addressInput}
              onChange={(e) => setAddressInput(e.target.value)}
            />
          </div>
        </div>

        {/* 6. A flex row div, inside it two buttons: left "Change password", right "Logout" */}
        <div className="flex w-full flex-col gap-4">
          {hasUnsavedChanges && (
            <Button
              variant="secondary"
              className="w-full"
              onClick={handleSaveChanges}
              disabled={updateDriverMutation.isPending}
            >
              {updateDriverMutation.isPending ? 'Saving...' : 'Save changes'}
            </Button>
          )}
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
        </div>

        <ConfirmModal
          open={isLogoutModalOpen}
          onOpenChange={setIsLogoutModalOpen}
          onConfirm={handleConfirmLogout}
          title="Log out"
          description="Are you sure you would like to log out of your account?"
          confirmLabel="Log out"
          cancelLabel="Go back"
          isLoading={logoutMutation.isPending}
        />

        <UnsavedChangesModal
          open={isUnsavedModalOpen}
          onOpenChange={setIsUnsavedModalOpen}
          onDiscard={handleDiscardChanges}
          onKeepEditing={handleKeepEditing}
        />
      </main>
    </>
  );
};

export const DriverProfile = () => {
  const user = useAuthStore((state) => state.user)!;
  const driverId = user.driverId;

  const { data: driverDetails, isLoading } = useDriver(
    driverId || '',
    !!driverId
  );

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!driverDetails) {
    return (
      <main className="mx-auto flex w-full flex-1 flex-col gap-6">
        <Link to="/driver/home" className="flex gap-1 self-start text-blue-400">
          <ChevronLeftIcon className="size-6" />
          <h2>Back to home</h2>
        </Link>
        <Banner variant="error">
          Couldn't load your driver profile. Please refresh the page.
        </Banner>
      </main>
    );
  }

  return (
    <DriverProfileLoaded
      driverDetails={driverDetails}
      driverId={driverId || ''}
      user={user}
    />
  );
};
