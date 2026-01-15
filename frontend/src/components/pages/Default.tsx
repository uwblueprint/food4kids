import React from 'react';
import { Container, Card } from 'react-bootstrap';
import { useAuth } from '../../hooks/useAuth';
import Logout from '../auth/Logout';

const Default = (): React.ReactElement => {
  const { user } = useAuth();

  return (
    <Container className="mt-5">
      <Card>
        <Card.Body>
          <h1>Welcome to Food4Kids</h1>
          <p>Hello, {user?.name || 'Driver'}!</p>
          <p>Email: {user?.email}</p>
          <div className="mt-4">
            <Logout />
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Default;
