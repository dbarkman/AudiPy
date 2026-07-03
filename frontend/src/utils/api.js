import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api', // Use proxy for API requests
  timeout: 30000, // 30 seconds for auth operations
  withCredentials: true, // Include cookies for JWT tokens
});

// Request interceptor to add auth headers if needed
api.interceptors.request.use(
  (config) => {
    // Add any default headers here
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 unauthorized globally
    if (error.response?.status === 401) {
      // Could trigger logout here if needed
      console.warn('Unauthorized request');
    }
    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  // Login with Audible credentials
  login: (credentials) => {
    return api.post('/auth/login', {
      username: credentials.username,
      password: credentials.password,
      marketplace: credentials.marketplace || 'us',
    });
  },

  // Verify OTP code
  verifyOTP: (otpData) => {
    return api.post('/auth/verify-otp', {
      session_id: otpData.session_id,
      otp_code: otpData.otp_code,
    });
  },

  // Check current auth status
  checkAuth: () => {
    return api.get('/auth/me');
  },

  // Logout
  logout: () => {
    return api.post('/auth/logout');
  },

  // Test API access (for debugging)
  test: () => {
    return api.get('/auth/test');
  },
};

// User API endpoints
export const userAPI = {
  // Get user profile
  getProfile: () => {
    return api.get('/user/profile');
  },

  // Update user preferences
  updatePreferences: (preferences) => {
    return api.put('/user/preferences', preferences);
  },

  // Get user status
  getStatus: () => {
    return api.get('/user/status');
  },
};

// Library API endpoints
export const libraryAPI = {
  // Get user's library (paginated)
  getLibrary: (params = {}) => {
    return api.get('/library', { params });
  },

  // Trigger library sync
  syncLibrary: () => {
    return api.post('/library/sync');
  },

  // Get sync status
  getSyncStatus: () => {
    return api.get('/library/status');
  },

  // Get book details
  getBook: (bookId) => {
    return api.get(`/books/${bookId}`);
  },
};

// Recommendations API endpoints
export const recommendationsAPI = {
  // Get recommendations (paginated)
  getRecommendations: (params = {}) => {
    return api.get('/recommendations', { params });
  },

  // Generate new recommendations
  generateRecommendations: () => {
    return api.post('/recommendations/generate');
  },

  // Get generation status
  getGenerationStatus: () => {
    return api.get('/recommendations/status');
  },

  // Mark recommendation as favorite
  favoriteRecommendation: (recommendationId) => {
    return api.post(`/recommendations/${recommendationId}/favorite`);
  },
};

// Health check
export const healthAPI = {
  check: () => {
    return api.get('/health');
  },
};

export default api; 