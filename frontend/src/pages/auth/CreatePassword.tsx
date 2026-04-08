import axios from 'axios';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

export const CreatePassword = () => {
  const [password, setPassword] = useState('');
  const [feedback, setFeedback] = useState('');
  const { token } = useParams();

  const submitPassword = async (e) => {
    e.preventDefault();
    setFeedback('Connecting...');

    try {
      // Axios handles JSON stringification automatically
      const response = await axios.post(
        'http://localhost:8080/drivers/register',
        {
          user_invite_id: token,
          password: password,
        }
      );

      console.log('Backend response:', response.data);
      setFeedback('Success: Password recorded.');
      setPassword(''); // Clear input on success
    } catch (err) {
      // Axios catches 4xx/5xx errors automatically
      const errorMessage = err.response?.data?.message || 'Server unreachable';
      setFeedback(`Error: ${errorMessage}`);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 text-center shadow-sm">
        <h1 className="mb-6 text-2xl font-bold text-gray-800">
          Create Password
        </h1>

        <form onSubmit={submitPassword} className="flex flex-col gap-4">
          <input
            type="password"
            placeholder="Enter test password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg border border-gray-200 p-3 transition-all outline-none focus:ring-2 focus:ring-blue-500"
            required
          />

          <button
            type="submit"
            className="rounded-lg bg-blue-600 py-3 font-bold text-white transition-colors hover:bg-blue-700"
          >
            Test Backend
          </button>
        </form>

        {feedback && (
          <p
            className={`mt-4 text-sm font-medium ${feedback.includes('Error') ? 'text-red-500' : 'text-green-600'}`}
          >
            {feedback}
          </p>
        )}
      </div>
    </div>
  );
};
