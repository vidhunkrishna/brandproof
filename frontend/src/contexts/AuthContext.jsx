import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../api/client';

const AuthContext = createContext(null);

export const DEMO_PRESETS = [
  { role: 'admin', label: 'Admin (Lumen)', email: 'admin@lumen.demo', password: 'LumenAdmin2026!' },
  { role: 'creator', label: 'Creator (Lumen)', email: 'creator@lumen.demo', password: 'LumenCreator2026!' },
  { role: 'reviewer', label: 'Reviewer (Lumen)', email: 'reviewer@lumen.demo', password: 'LumenReviewer2026!' },
];

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [activeOrganization, setActiveOrganization] = useState(null);
  const [role, setRole] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('brandproof_token'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get('/api/v1/auth/me');
      setUser(res.data.user);
      setActiveOrganization(res.data.active_organization);
      setRole(res.data.role);
    } catch (err) {
      console.warn('Authentication check failed:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      // Default auto-login to Admin for frictionless demo exploration
      quickLogin('admin');
    }
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/api/v1/auth/login', { email, password });
      const { access_token, user: u, active_organization: org, role: r } = res.data;
      localStorage.setItem('brandproof_token', access_token);
      setToken(access_token);
      setUser(u);
      setActiveOrganization(org);
      setRole(r);
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Login failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, full_name, organization_name, selectedRole = 'creator') => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/api/v1/auth/register', {
        email,
        password,
        full_name,
        organization_name,
        role: selectedRole,
      });
      const { access_token, user: u, active_organization: org, role: r } = res.data;
      localStorage.setItem('brandproof_token', access_token);
      setToken(access_token);
      setUser(u);
      setActiveOrganization(org);
      setRole(r);
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Registration failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (targetRole) => {
    const preset = DEMO_PRESETS.find((p) => p.role === targetRole);
    if (preset) {
      return await login(preset.email, preset.password);
    }
  };

  const logout = () => {
    localStorage.removeItem('brandproof_token');
    setToken(null);
    setUser(null);
    setActiveOrganization(null);
    setRole(null);
    setLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeOrganization,
        role,
        token,
        loading,
        error,
        login,
        register,
        quickLogin,
        logout,
        fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

