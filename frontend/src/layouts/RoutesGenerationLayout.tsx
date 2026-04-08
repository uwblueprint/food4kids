import { Outlet } from 'react-router-dom';

export const RoutesGenerationLayout = () => {
  return (
    <div className="page-margins flex min-h-screen flex-col gap-8 pb-16">
      <div className="flex flex-col gap-1">
        <h1>Route Generation</h1>
        <p className="text-p1 text-grey-400">
          Choose how you'd like to proceed with your delivery routes.
        </p>
      </div>
      <Outlet />
    </div>
  );
};
