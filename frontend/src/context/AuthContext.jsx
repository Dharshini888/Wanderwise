import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';

const AuthContext = createContext();

const isValidTokenString = (t) => Boolean(t && t !== 'null' && t !== 'undefined' && typeof t === 'string' && t.trim() !== '');

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    const t = localStorage.getItem('token');
    return isValidTokenString(t) ? t : null;
  });
  const [refreshToken, setRefreshToken] = useState(() => {
    const rt = localStorage.getItem('refresh_token');
    return isValidTokenString(rt) ? rt : null;
  });
  const [user, setUser] = useState(() => {
    const t = localStorage.getItem('token');
    if (!isValidTokenString(t)) return null;
    const saved = localStorage.getItem('user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch (_) {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Sync token and headers
  const setSession = (accessToken, newRefreshToken, userData) => {
    if (isValidTokenString(accessToken)) {
      localStorage.setItem('token', accessToken);
      setToken(accessToken);
    } else {
      localStorage.removeItem('token');
      setToken(null);
    }

    if (isValidTokenString(newRefreshToken)) {
      localStorage.setItem('refresh_token', newRefreshToken);
      setRefreshToken(newRefreshToken);
    } else {
      localStorage.removeItem('refresh_token');
      setRefreshToken(null);
    }

    if (userData && (isValidTokenString(accessToken) || token)) {
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    } else {
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  // Check auth session validity on mount
  useEffect(() => {
    let isMounted = true;
    const verifySession = async () => {
      const storedToken = localStorage.getItem('token');
      if (!isValidTokenString(storedToken)) {
        setSession(null, null, null);
        if (isMounted) setLoading(false);
        return;
      }
      try {
        const res = await api.get('/api/auth/me');
        if (isMounted && res.data) {
          setUser(res.data);
          localStorage.setItem('user', JSON.stringify(res.data));
        }
      } catch (err) {
        // Stale or invalid token - clear session cleanly
        if (isMounted) {
          setSession(null, null, null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    verifySession();
    return () => {
      isMounted = false;
    };
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
        isAuthenticated: !loading && !!token && !!user,
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
