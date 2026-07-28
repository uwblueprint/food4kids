import { useAuthStore } from '@/api/authStore';

export const Account = () => {
  // TODO: fetch account from global context? (name, role, avatar, or initials as profile)
  const user = useAuthStore((state) => state.user);
  const initials =
    `${user?.firstName?.charAt(0) || ''}${user?.lastName?.charAt(0) || ''}`.toUpperCase();

  // Sizes and styles are the admin frames' top bar: a 48px pink disc with
  // 16/22 Nunito Medium initials, then the name and role both at 16/22. The
  // design gives every avatar the same pink, so this is not per-user colour.
  return (
    <div className="flex items-center gap-4">
      <div className="bg-brand-pink flex size-12 items-center justify-center rounded-full">
        <span className="text-m-p2 font-nunito text-grey-100 leading-[22px] font-medium">
          {initials}
        </span>
      </div>
      <div className="inline-flex flex-col items-start">
        {/* The design sets this one line in Nunito and the role beneath it in
            Nunito Sans; mixing the two in a two-line block reads as a slip, so
            the name follows the role (and the rest of the body copy). */}
        <p className="text-m-p2 leading-[22px]">{user?.fullName}</p>
        <p className="text-m-p2 text-grey-400 leading-[22px] font-light capitalize">
          {user?.role}
        </p>
      </div>
    </div>
  );
};
