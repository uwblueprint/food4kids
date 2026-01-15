import React, { useState } from 'react';
import { Button } from 'react-bootstrap';
import { useAuth } from '../../hooks/useAuth';

const Logout = (): React.ReactElement => {
  const { signOut } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleLogout = async () => {
    setLoading(true);
    try {
      await signOut();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button variant="danger" onClick={handleLogout} disabled={loading}>
      {loading ? 'Logging out...' : 'Logout'}
    </Button>
  );
};

export default Logout;
