import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useLogout } from '@/api/auth';
import { useAuthStore } from '@/api/authStore';
import { cn } from '@/lib/utils';

import { ConfirmModal } from './ConfirmModal';
import { Popover, PopoverContent, PopoverTrigger } from './Popover';

const MENU_ITEM =
  'text-p2 flex w-full cursor-pointer items-center rounded-lg px-3 py-2 whitespace-nowrap';

export const Account = () => {
  const navigate = useNavigate();
  const logoutMutation = useLogout();
  const user = useAuthStore((state) => state.user);
  const initials =
    `${user?.firstName?.charAt(0) || ''}${user?.lastName?.charAt(0) || ''}`.toUpperCase();

  const [menuOpen, setMenuOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);

  const handleConfirmLogout = () => {
    logoutMutation.mutate(undefined, {
      onSettled: () => {
        setLogoutOpen(false);
        navigate('/login');
      },
    });
  };

  // Sizes and styles are the admin frames' top bar: a 48px pink disc with
  // 16/22 Nunito Medium initials, then the name and role both at 16/22. The
  // design gives every avatar the same pink, so this is not per-user colour.
  return (
    <>
      <Popover open={menuOpen} onOpenChange={setMenuOpen}>
        <PopoverTrigger asChild>
          {/* -mr-3/pr-3 gives the hover pill room past the name without
              shifting the block off the page's right edge. */}
          <button
            type="button"
            aria-label="Account menu"
            className={cn(
              '-mr-3 flex cursor-pointer items-center gap-4 rounded-full pr-3 text-left',
              'transition-colors hover:bg-blue-50 data-[state=open]:bg-blue-50'
            )}
          >
            <span className="bg-brand-pink flex size-12 items-center justify-center rounded-full">
              <span className="text-m-p2 font-nunito text-grey-100 leading-[22px] font-medium">
                {initials}
              </span>
            </span>
            <span className="inline-flex flex-col items-start">
              {/* The design sets this one line in Nunito and the role beneath it in
                  Nunito Sans; mixing the two in a two-line block reads as a slip, so
                  the name follows the role (and the rest of the body copy). */}
              <span className="text-m-p2 leading-[22px]">{user?.fullName}</span>
              <span className="text-m-p2 text-grey-400 leading-[22px] font-light capitalize">
                {user?.role}
              </span>
            </span>
          </button>
        </PopoverTrigger>
        <PopoverContent
          align="end"
          className="w-auto min-w-44 p-1"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <button
            type="button"
            className={cn(MENU_ITEM, 'text-grey-500 hover:bg-blue-50')}
            onClick={() => {
              setMenuOpen(false);
              navigate('/admin/update-password');
            }}
          >
            Change password
          </button>
          <button
            type="button"
            className={cn(MENU_ITEM, 'text-red hover:bg-light-red')}
            onClick={() => {
              setMenuOpen(false);
              setLogoutOpen(true);
            }}
          >
            Log out
          </button>
        </PopoverContent>
      </Popover>

      <ConfirmModal
        open={logoutOpen}
        onOpenChange={setLogoutOpen}
        onConfirm={handleConfirmLogout}
        title="Log out"
        description="Are you sure you would like to log out of your account?"
        confirmLabel="Log out"
        cancelLabel="Go back"
        isLoading={logoutMutation.isPending}
      />
    </>
  );
};
