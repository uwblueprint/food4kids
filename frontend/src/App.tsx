import 'bootstrap/dist/css/bootstrap.min.css';
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import PrivateRoute from './components/auth/PrivateRoute';
import Default from './components/pages/Default';
import NotFound from './components/pages/NotFound';
import * as AppRoutes from './constants/Routes';
import { AuthProvider } from './providers/AuthProvider';

const App = (): React.ReactElement => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path={AppRoutes.LOGIN_PAGE} element={<Login />} />
          <Route path={AppRoutes.SIGNUP_PAGE} element={<Signup />} />
          <Route
            path={AppRoutes.HOME_PAGE}
            element={
              <PrivateRoute>
                <Default />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
