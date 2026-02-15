import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AdminLayout, DriverLayout } from './layouts';
import {
  AdminDriversPage,
  AdminHomePage,
  AdminRoutesPage,
  AdminSettingsPage,
} from './pages/admin';
import { DriverHomePage } from './pages/driver';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Redirect root to admin home */}
        <Route path="/" element={<Navigate to="/admin/home" replace />} />

        {/* Admin Routes */}
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/home" replace />} />
          <Route path="home" element={<AdminHomePage />} />
          <Route path="drivers" element={<AdminDriversPage />} />
          <Route path="routes" element={<AdminRoutesPage />} />
          <Route path="settings" element={<AdminSettingsPage />} />
        </Route>

        {/* Driver Routes */}
        <Route path="/driver" element={<DriverLayout />}>
          <Route index element={<Navigate to="/driver/home" replace />} />
          <Route path="home" element={<DriverHomePage />} />
        </Route>

        {/* Shared Routes */}

        {/* 404 Not Found */}
        <Route path="*" element={<Navigate to="/admin/home" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
