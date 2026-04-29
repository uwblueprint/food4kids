import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import {
  CatchAllErrorPage,
  ForbiddenPage,
  NotFoundPage,
  ServiceUnavailablePage,
} from './common/components';
import { AdminLayout, DriverLayout } from './layouts';
import {
  AdminDriversPage,
  AdminHomePage,
  AdminRoutesGenerationLayout,
  AdminRoutesPage,
  AdminSettingsPage,
  ConfigureStep,
  GenerateStep,
  ImportStep,
  ReviewStep,
  ValidateStep,
} from './pages/admin';
import { DriverHomePage } from './pages/driver';
import { StyleGuidePage } from './pages/StyleGuide';
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
          {/* Route Generation */}
          <Route
            path="routes/generation"
            element={<AdminRoutesGenerationLayout />}
          >
            <Route index element={<Navigate to="import" replace />} />
            <Route path="import" element={<ImportStep />} />
            <Route path="validate" element={<ValidateStep />} />
            <Route path="review" element={<ReviewStep />} />
            <Route path="configure" element={<ConfigureStep />} />
            <Route path="generate" element={<GenerateStep />} />
          </Route>
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

        {/* Dev-only: style guide is not accessible in production */}
        {import.meta.env.DEV && (
          <Route path="/style-guide" element={<StyleGuidePage />} />
        )}

        {/* Error pages (dev preview) */}
        {import.meta.env.DEV && (
          <>
            <Route path="/403" element={<ForbiddenPage />} />
            <Route path="/404" element={<NotFoundPage />} />
            <Route path="/503" element={<ServiceUnavailablePage />} />
            <Route path="/error" element={<CatchAllErrorPage />} />
          </>
        )}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
