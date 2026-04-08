import { useState } from 'react';
import axios from 'axios';
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
      const response = await axios.post('http://localhost:8080/drivers/register', { 
        user_invite_id: token, 
        password: password 
      });
      
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
    <div className="bg-gray-100 flex min-h-screen items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-sm w-full max-w-md text-center">
        <h1 className="text-gray-800 mb-6 text-2xl font-bold">Create Password</h1>
        
        <form onSubmit={submitPassword} className="flex flex-col gap-4">
          <input
            type="password"
            placeholder="Enter test password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="border-gray-200 rounded-lg border p-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            required
          />
          
          <button 
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 rounded-lg py-3 font-bold text-white transition-colors"
          >
            Test Backend
          </button>
        </form>

        {feedback && (
          <p className={`mt-4 text-sm font-medium ${feedback.includes('Error') ? 'text-red-500' : 'text-green-600'}`}>
            {feedback}
          </p>
        )}
      </div>
    </div>
  );
};
