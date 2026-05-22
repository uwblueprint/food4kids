import { useEffect } from 'react';

import axiosClient from '@/lib/axiosClient';
import { useAuth, type UserRole } from '@/contexts/AuthContext';
import type { Announcement } from '@/types/announcement';

interface DriverApiRow {
  user_id: string;
  name: string;
  role?: string;
}

/**
 * When no user id is configured (login or VITE_DEV_USER_ID), try to infer one
 * from existing API data so local dev works after seeding.
 */
export function useBootstrapCurrentUser(role: UserRole): void {
  const { user, setUser } = useAuth();

  useEffect(() => {
    if (user.userId) return;

    let cancelled = false;

    async function bootstrap(): Promise<void> {
      try {
        const { data: drivers } =
          await axiosClient.get<DriverApiRow[]>('/drivers/');
        const driver = drivers[0];
        if (driver?.user_id && !cancelled) {
          setUser({
            userId: driver.user_id,
            name: driver.name,
            role: (driver.role as UserRole) ?? role,
          });
          return;
        }

        const { data: announcements } =
          await axiosClient.get<Announcement[]>('/announcements/');
        const announcement = announcements[0];
        if (announcement?.user_id && !cancelled) {
          setUser({
            userId: announcement.user_id,
            name: announcement.author_name || user.name,
            role,
          });
        }
      } catch {
        // Ignore — user will see a clear message on submit
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [user.userId, user.name, role, setUser]);
}
