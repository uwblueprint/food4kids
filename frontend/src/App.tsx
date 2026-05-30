import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import {
  CatchAllErrorPage,
  ForbiddenPage,
  NotFoundPage,
  ServiceUnavailablePage,
} from './common/components/ErrorScreen';
import { AdminLayout, DriverLayout } from './layouts';

const AdminHomePage = lazy(() =>
  import('./pages/admin/home/AdminHomePage').then((m) => ({ default: m.AdminHomePage }))
);
const AdminDriversPage = lazy(() =>
  import('./pages/admin/drivers/AdminDriversPage').then((m) => ({ default: m.AdminDriversPage }))
);
const AdminRoutesPage = lazy(() =>
  import('./pages/admin/routes/AdminRoutesPage').then((m) => ({ default: m.AdminRoutesPage }))
);
const AdminRoutesGenerationLayout = lazy(() =>
  import('./pages/admin/routes/generation/AdminRoutesGenerationLayout').then((m) => ({ default: m.AdminRoutesGenerationLayout }))
);
const ImportStep = lazy(() =>
  import('./pages/admin/routes/generation/ImportStep').then((m) => ({ default: m.ImportStep }))
);
const ValidateStep = lazy(() =>
  import('./pages/admin/routes/generation/ValidateStep').then((m) => ({ default: m.ValidateStep }))
);
const ReviewStep = lazy(() =>
  import('./pages/admin/routes/generation/ReviewStep').then((m) => ({ default: m.ReviewStep }))
);
const ConfigureStep = lazy(() =>
  import('./pages/admin/routes/generation/ConfigureStep').then((m) => ({ default: m.ConfigureStep }))
);
const GenerateStep = lazy(() =>
  import('./pages/admin/routes/generation/GenerateStep').then((m) => ({ default: m.GenerateStep }))
);
const AdminSettingsPage = lazy(() =>
  import('./pages/admin/settings/AdminSettingsPage').then((m) => ({ default: m.AdminSettingsPage }))
);
const DriverHomePage = lazy(() =>
  import('./pages/driver/home/DriverHomePage').then((m) => ({ default: m.DriverHomePage }))
);
const TestImageUpload = lazy(() =>
  import('./pages/TestImageUpload').then((m) => ({ default: m.TestImageUpload }))
);
const StyleGuidePage = lazy(() =>
  import('./pages/StyleGuide').then((m) => ({ default: m.StyleGuidePage }))
);

function App() {
  return (
    <BrowserRouter>
      <Suspense>
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
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
