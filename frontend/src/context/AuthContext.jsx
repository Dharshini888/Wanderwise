import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('token') || null);
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem('refresh_token') || null);
  const [loading, setLoading] = useState(true);

  // Sync token and headers
  const setSession = (accessToken, newRefreshToken, userData) => {
    if (accessToken) {
      localStorage.setItem('token', accessToken);
      setToken(accessToken);
    } else {
      localStorage.removeItem('token');
      setToken(null);
    }

    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken);
      setRefreshToken(newRefreshToken);
    } else {
      localStorage.removeItem('refresh_token');
      setRefreshToken(null);
    }

    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    } else {
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  // Check auth session validity on mount
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('token');
      if (!storedToken) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.get('/api/auth/me');
        if (res.data) {
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        }
      } catch (err) {
        // Stale or invalid token - clear session cleanly
        setSession(null, null, null);
      } finally {
        setLoading(false);
      }
    };
    verifySession();
  }, []);

  const login = async (email, password, rememberMe = false) => {
    const res = await api.post('/api/auth/login', { email, password, remember_me: rememberMe });
    const { access_token, refresh_token, user: userData } = res.data;
    setSession(access_token, refresh_token, userData);
    return userData;
  };

  const register = async (formData) => {
    const res = await api.post('/api/auth/register', formData);
    const { access_token, refresh_token, user: userData } = res.data;
    setSession(access_token, refresh_token, userData);
    return userData;
  };

  const logout = async () => {
    try {
      await api.post('/api/auth/logout');
    } catch (_) {}
    setSession(null, null, null);
  };

  const updateUser = async (profileData) => {
    const res = await api.put('/api/auth/me', profileData);
    if (res.data) {
      setUser(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
    }
    return res.data;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        refreshToken,
        isAuthenticated: !!token && !!user,
        loading,
        login,
        register,
        logout,
        updateUser,
        setSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
