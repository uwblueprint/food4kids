import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AdminLayout, DriverLayout } from './layouts';
import {
  AdminDriversPage,
  AdminHomePage,
  AdminRoutesPage,
  AdminSettingsPage,
} from './pages/admin';
import { DriverHomePage } from './pages/driver';
import { NotFoundPage } from './pages/NotFoundPage';
import { StyleGuidePage } from './pages/StyleGuide';
import { LoginPage } from './pages/auth/LoginPage';
import { TestImageUpload } from './pages/TestImageUpload';

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
          <Route path="test-image-upload" element={<TestImageUpload />} />
        </Route>

        {/* Driver Routes */}
        <Route path="/driver" element={<DriverLayout />}>
          <Route index element={<Navigate to="/driver/home" replace />} />
          <Route path="home" element={<DriverHomePage />} />
        </Route>

        {/* Dev-only: test image upload route */}
        <Route path="/test-image-upload" element={<TestImageUpload />} />

        {/* Login Routes */}
        <Route path="/login" element={<LoginPage />}/>

        {/* Dev-only: style guide is not accessible in production */}
        {import.meta.env.DEV && (
          <Route path="/style-guide" element={<StyleGuidePage />} />
        )}

        {/* 404 Not Found */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
