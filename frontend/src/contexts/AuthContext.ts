import { createContext } from "react";
import { AuthenticatedUser } from "../types/AuthTypes";

type AuthContextType = {
  authenticatedUser: AuthenticatedUser;
  setAuthenticatedUser: (_authenticatedUser: AuthenticatedUser) => void;
};

const AuthContext = createContext<AuthContextType>({
  authenticatedUser: null,
  setAuthenticatedUser: (_authenticatedUser: AuthenticatedUser): void => {
    // This is a placeholder implementation for the context default value
  },
});

export default AuthContext;
