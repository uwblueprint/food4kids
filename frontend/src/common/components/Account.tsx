import { useAuthStore } from "@/api/authStore";

export const Account = () => {
  // TODO: fetch account from global context? (name, role, avatar, or initials as profile)
  const user = useAuthStore((state) => state.user);
  const initials = `${user?.firstName?.charAt(0) || ''}${user?.lastName?.charAt(0) || ''}`.toUpperCase();

  return (
    <div className="flex items-center gap-4">
      <div className="flex size-10 items-center justify-center rounded-full bg-blue-300">
        <span className="text-p2 text-grey-100">{initials}</span>
      </div>
      <div className="inline-flex flex-col items-start">
        <p className="text-p1 font-medium">{user?.fullName}</p>
        <p className="text-p2 text-grey-400 capitalize">{user?.role}</p>
      </div>
    </div>
  );
}
