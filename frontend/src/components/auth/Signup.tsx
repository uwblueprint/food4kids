import React, { useContext, useState } from "react";
import { Navigate } from "react-router-dom";

import authAPIClient from "../../APIClients/AuthAPIClient";
import { HOME_PAGE } from "../../constants/Routes";
import AuthContext from "../../contexts/AuthContext";
import { AuthenticatedUser } from "../../types/AuthTypes";

const Signup = (): React.ReactElement => {
  const { authenticatedUser, setAuthenticatedUser } = useContext(AuthContext);
  const [name, setName] = useState("John Doe");
  const [email, setEmail] = useState("john.doe@example.com");
  const [phone, setPhone] = useState("+1234567890");
  const [address, setAddress] = useState("123 Main St, City, State 12345");
  const [licensePlate, setLicensePlate] = useState("ABC123");
  const [carMakeModel, setCarMakeModel] = useState("Toyota Camry");
  const [password, setPassword] = useState("password123");

  const onSignupClick = async () => {
    const user: AuthenticatedUser = await authAPIClient.register(
      name,
      email,
      phone,
      address,
      licensePlate,
      carMakeModel,
      password,
    );
    setAuthenticatedUser(user);
  };

  if (authenticatedUser) {
    return <Navigate to={HOME_PAGE} />;
  }

  return (
    <div style={{ textAlign: "center" }}>
      <h1>Driver Signup</h1>
      <form>
        <div>
          <input
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Full name"
            required
          />
        </div>
        <div>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="username@domain.com"
            required
          />
        </div>
        <div>
          <input
            type="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            placeholder="Phone number (e.g., +1234567890)"
            required
          />
        </div>
        <div>
          <input
            type="text"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
            placeholder="Address"
            required
          />
        </div>
        <div>
          <input
            type="text"
            value={licensePlate}
            onChange={(event) => setLicensePlate(event.target.value)}
            placeholder="License plate"
            required
          />
        </div>
        <div>
          <input
            type="text"
            value={carMakeModel}
            onChange={(event) => setCarMakeModel(event.target.value)}
            placeholder="Car make and model (e.g., Toyota Camry)"
            required
          />
        </div>
        <div>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password (min 8 characters)"
            required
          />
        </div>
        <div>
          <button
            className="btn btn-primary"
            type="button"
            onClick={onSignupClick}
          >
            Sign Up
          </button>
        </div>
      </form>
    </div>
  );
};

export default Signup;
