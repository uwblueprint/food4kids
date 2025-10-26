import React, { useContext } from "react";
import { Navigate } from "react-router-dom";

import AuthContext from "../../contexts/AuthContext";
import { LOGIN_PAGE } from "../../constants/Routes";

type PrivateRouteProps = {
  children: React.ReactNode;
};

const PrivateRoute: React.FC<PrivateRouteProps> = ({
  children,
}: PrivateRouteProps) => {
  const { authenticatedUser } = useContext(AuthContext);

  return authenticatedUser ? <>{children}</> : <Navigate to={LOGIN_PAGE} />;
};

export default PrivateRoute;
