import React, { useState } from 'react';

const Login: React.FC = () => {
  const [loginMethod, setLoginMethod] = useState<'github' | 'innerself'>('github');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleGitHubLogin = () => {
    // Redirect to GitHub OAuth
    window.location.href = `${process.env.REACT_APP_API_URL}/auth/github`;
  };

  const handleInnerSelfLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement InnerSelf account login
    console.log('InnerSelf login:', { email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to InnerSelf
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            The essence-based messaging platform for dev teams
          </p>
        </div>
        
        <div className="mt-8 space-y-6">
          {/* Login Method Selector */}
          <div className="bg-white py-4 px-6 shadow-md rounded-lg">
            <div className="flex space-x-4">
              <button
                onClick={() => setLoginMethod('github')}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                  loginMethod === 'github'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                GitHub Account
              </button>
              <button
                onClick={() => setLoginMethod('innerself')}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                  loginMethod === 'innerself'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                InnerSelf Account
              </button>
            </div>
          </div>

          {/* GitHub Login */}
          {loginMethod === 'github' && (
            <div className="bg-white py-8 px-6 shadow-md rounded-lg">
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Connect with GitHub
                  </h3>
                  <p className="text-sm text-gray-500 mb-6">
                    We use GitHub to track your contributions and build your essence level
                  </p>
                </div>
                
                <button
                  onClick={handleGitHubLogin}
                  className="w-full flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                  </svg>
                  Continue with GitHub
                </button>
              </div>
            </div>
          )}

          {/* InnerSelf Login */}
          {loginMethod === 'innerself' && (
            <div className="bg-white py-8 px-6 shadow-md rounded-lg">
              <div className="space-y-6">
                <div className="text-center">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Sign in to InnerSelf
                  </h3>
                  <p className="text-sm text-gray-500 mb-6">
                    Access your InnerSelf account to view your essence and team data
                  </p>
                </div>
                
                <form onSubmit={handleInnerSelfLogin} className="space-y-4">
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email address
                    </label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Enter your email"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                      Password
                    </label>
                    <input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      placeholder="Enter your password"
                    />
                  </div>
                  
                  <button
                    type="submit"
                    className="w-full flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                  >
                    Sign In
                  </button>
                </form>
                
                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    Don't have an account?{' '}
                    <button className="text-primary-600 hover:text-primary-700 font-medium">
                      Create one
                    </button>
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div className="text-xs text-gray-500 text-center">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </div>
          
          {loginMethod === 'github' && (
            <div className="text-center">
              <div className="text-sm text-gray-600">
                <strong>Why GitHub?</strong>
                <ul className="mt-2 space-y-1 text-left max-w-sm mx-auto">
                  <li>• Track your PR quality and commit patterns</li>
                  <li>• Measure code review participation</li>
                  <li>• Build essence based on contributions</li>
                  <li>• Prevent micromanagement through data</li>
                </ul>
              </div>
            </div>
          )}
          
          {loginMethod === 'innerself' && (
            <div className="text-center">
              <div className="text-sm text-gray-600">
                <strong>InnerSelf Account Benefits</strong>
                <ul className="mt-2 space-y-1 text-left max-w-sm mx-auto">
                  <li>• Manual essence tracking and team insights</li>
                  <li>• Access to messaging and collaboration tools</li>
                  <li>• View team analytics and leaderboards</li>
                  <li>• Connect GitHub later for enhanced tracking</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;