import React, { createContext, useState, useEffect } from 'react';
import api, { authAPI } from '../services/api';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await authAPI.getMe();
          setUser(userData.data);
        } catch (error) {
          console.error('Auth initialization failed', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    
    const userData = await authAPI.getMe();
    setUser(userData.data);
  };

  const register = async (email, password) => {
    await authAPI.register(email, password);
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
