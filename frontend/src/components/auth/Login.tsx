import React, { useContext, useState } from "react";
import { Redirect, useHistory } from "react-router-dom";

import authAPIClient from "../../APIClients/AuthAPIClient";
import { HOME_PAGE, SIGNUP_PAGE } from "../../constants/Routes";
import AuthContext from "../../contexts/AuthContext";
import { AuthenticatedUser } from "../../types/AuthTypes";

const Login = (): React.ReactElement => {
  const { authenticatedUser, setAuthenticatedUser } = useContext(AuthContext);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const history = useHistory();

  const onLogInClick = async () => {
    const user: AuthenticatedUser = await authAPIClient.login(email, password);
    setAuthenticatedUser(user);
  };

  const onSignUpClick = () => {
    history.push(SIGNUP_PAGE);
  };


  if (authenticatedUser) {
    return <Redirect to={HOME_PAGE} />;
  }

  return (
    <div style={{ textAlign: "center" }}>
      <h1>Login</h1>
      <form>
        <div>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="username@domain.com"
          />
        </div>
        <div>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="password"
          />
        </div>
        <div>
          <button
            className="btn btn-primary"
            type="button"
            onClick={onLogInClick}
          >
            Log In
          </button>
        </div>
      </form>
      <div>
        <button
          className="btn btn-primary"
          type="button"
          onClick={onSignUpClick}
        >
          Sign Up
        </button>
      </div>
    </div>
  );
};

export default Login;
