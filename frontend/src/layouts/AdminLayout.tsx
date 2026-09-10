import { Outlet } from 'react-router-dom';

import HomeIcon from '@/assets/icons/home.svg?react';
import MapIcon from '@/assets/icons/map.svg?react';
import SettingsIcon from '@/assets/icons/settings.svg?react';
import UsersIcon from '@/assets/icons/users.svg?react';
import logoImg from '@/assets/logos/logo_desktop_two_lines.png';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuItem,
  SidebarProvider,
} from '@/common/components/Sidebar';

// Home and Routes are drawn on 20x22 and 24x22 artboards in the design; the
// other two are square. Sizing them all `size-6` scaled the first two up and
// out of proportion, so each carries its own.
const NAV_ITEMS = [
  {
    label: 'Home',
    to: '/admin/home',
    icon: HomeIcon,
    iconClassName: 'h-[22px] w-5',
    end: true,
  },
  {
    label: 'Routes',
    to: '/admin/routes',
    icon: MapIcon,
    iconClassName: 'h-[22px] w-6',
  },
  { label: 'Drivers', to: '/admin/drivers', icon: UsersIcon },
  { label: 'Settings', to: '/admin/settings', icon: SettingsIcon },
] as const;

export const AdminLayout = () => {
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader>
          <img src={logoImg} alt="Food4Kids" className="w-22 object-contain" />
        </SidebarHeader>

        <SidebarContent>
          <SidebarMenu>
            {NAV_ITEMS.map((item) => (
              <SidebarMenuItem key={item.to} {...item} />
            ))}
          </SidebarMenu>
        </SidebarContent>
      </Sidebar>

      <SidebarInset>
        <div className="admin-page-margins">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
};
