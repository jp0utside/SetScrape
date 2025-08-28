import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, UserSession } from '../types/api';
import apiService from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AuthContextType {
  user: User | null;
  session: UserSession | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
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
  const [session, setSession] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!session;

  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      
      // Clear any existing session state before login
      setUser(null);
      setSession(null);
      
      const userSession = await apiService.login(username, password);
      setUser(userSession.user);
      setSession(userSession);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      await apiService.logout();
      setUser(null);
      setSession(null);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkAuth = async () => {
    try {
      setIsLoading(true);
      
      // Validate the stored token with the server
      const isValid = await apiService.validateToken();
      
      if (isValid) {
        // Token is valid, get user data from storage
        const userData = await AsyncStorage.getItem('userData');
        const token = await apiService.getStoredToken();
        
        if (userData && token) {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
          setSession({ session_token: token, user: parsedUser });
        }
      } else {
        // Token is invalid, clear everything
        setUser(null);
        setSession(null);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      // Clear invalid data
      setUser(null);
      setSession(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTokenExpired = async () => {
    console.log('Token expired, logging out...');
    setUser(null);
    setSession(null);
  };

  useEffect(() => {
    // Set up token expiration callback
    apiService.setTokenExpiredCallback(handleTokenExpired);
    
    // Check authentication on mount
    checkAuth();
  }, []);

  const value: AuthContextType = {
    user,
    session,
    isLoading,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
