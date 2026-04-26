import { Outlet } from 'react-router-dom';

export const AdminLayout = () => {
  return (
    <div className="bg-grey-200 min-h-screen px-20 py-10">
      <Outlet />
    </div>
  );
};
