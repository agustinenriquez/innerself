import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../services/api.ts';
import websocketService from '../services/websocket.ts';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  github_profile?: {
    username: string;
    avatar_url: string;
  };
  essence: {
    overall: number;
    pr_quality: number;
    communication_score: number;
    commit_activity: number;
    team_collaboration: number;
  };
  is_online: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    if (token) {
      loadCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const loadCurrentUser = async () => {
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData);
      
      // Connect to WebSocket
      const token = localStorage.getItem('access_token');
      if (token) {
        websocketService.connect(userData.id, token);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (token: string) => {
    apiService.setToken(token);
    localStorage.setItem('access_token', token);
    await loadCurrentUser();
  };

  const logout = () => {
    apiService.logout();
    websocketService.disconnect();
    setUser(null);
    localStorage.removeItem('access_token');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};