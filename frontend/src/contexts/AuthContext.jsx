import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI } from '../utils/api';

// Auth state shape
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  requiresOTP: false,
  otpSession: null,
};

// Auth actions
const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  REQUIRE_OTP: 'REQUIRE_OTP',
  OTP_SUCCESS: 'OTP_SUCCESS',
  OTP_FAILURE: 'OTP_FAILURE',
  LOGOUT: 'LOGOUT',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Auth reducer
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload,
        error: null,
      };
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        requiresOTP: false,
        otpSession: null,
      };
    
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        requiresOTP: false,
        otpSession: null,
      };
    
    case AUTH_ACTIONS.REQUIRE_OTP:
      return {
        ...state,
        isLoading: false,
        error: null,
        requiresOTP: true,
        otpSession: action.payload,
      };
    
    case AUTH_ACTIONS.OTP_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        requiresOTP: false,
        otpSession: null,
      };
    
    case AUTH_ACTIONS.OTP_FAILURE:
      return {
        ...state,
        isLoading: false,
        error: action.payload,
        requiresOTP: true, // Keep OTP form open
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...initialState,
        isLoading: false,
      };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
}

// Create context
const AuthContext = createContext();

// Auth provider component
export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check if user is already authenticated on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      const response = await authAPI.checkAuth();
      
      if (response.data.authenticated) {
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: { user: response.data.user },
        });
      } else {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
    }
  };

  const login = async (credentials) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      const response = await authAPI.login(credentials);
      
      if (response.data.requires_otp) {
        dispatch({
          type: AUTH_ACTIONS.REQUIRE_OTP,
          payload: response.data.session_id,
        });
      } else {
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: { user: response.data.user },
        });
      }
    } catch (error) {
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: error.response?.data?.detail || 'Login failed',
      });
    }
  };

  const verifyOTP = async (otpCode) => {
    try {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      const response = await authAPI.verifyOTP({
        session_id: state.otpSession,
        otp_code: otpCode,
      });
      
      dispatch({
        type: AUTH_ACTIONS.OTP_SUCCESS,
        payload: { user: response.data.user },
      });
    } catch (error) {
      dispatch({
        type: AUTH_ACTIONS.OTP_FAILURE,
        payload: error.response?.data?.detail || 'OTP verification failed',
      });
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  const value = {
    ...state,
    login,
    verifyOTP,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { AUTH_ACTIONS }; 