import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  AccountCircle,
  Lock,
  Public,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

const MARKETPLACES = [
  { value: 'us', label: 'United States' },
  { value: 'uk', label: 'United Kingdom' },
  { value: 'de', label: 'Germany' },
  { value: 'fr', label: 'France' },
  { value: 'ca', label: 'Canada' },
  { value: 'au', label: 'Australia' },
  { value: 'jp', label: 'Japan' },
  { value: 'it', label: 'Italy' },
  { value: 'es', label: 'Spain' },
  { value: 'in', label: 'India' },
];

export default function LoginForm() {
  const { login, isLoading, error, clearError } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    marketplace: 'us',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }

    // Clear auth error when user makes changes
    if (error) {
      clearError();
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.username.trim()) {
      errors.username = 'Email or username is required';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    }

    if (!formData.marketplace) {
      errors.marketplace = 'Please select your marketplace';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    await login(formData);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Card 
      sx={{ 
        maxWidth: 450, 
        mx: 'auto',
        mt: { xs: 2, md: 4 },
        mb: 4,
        borderRadius: 4,
        boxShadow: '0px 8px 32px rgba(0, 0, 0, 0.12)',
        border: '1px solid',
        borderColor: 'grey.200',
      }}
    >
      <CardContent sx={{ p: { xs: 3, md: 4 } }}>
        <Typography 
          variant="h5" 
          component="h2" 
          gutterBottom 
          textAlign="center"
          sx={{ mb: 3 }}
        >
          Sign in to Audible
        </Typography>

        <Typography 
          variant="body2" 
          color="text.secondary" 
          textAlign="center"
          sx={{ mb: 3 }}
        >
          Enter your Audible credentials to analyze your library and get personalized recommendations.
        </Typography>

        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            onClose={clearError}
          >
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          {/* Username/Email Field */}
          <TextField
            fullWidth
            label="Email or Username"
            type="email"
            value={formData.username}
            onChange={handleChange('username')}
            error={!!validationErrors.username}
            helperText={validationErrors.username}
            disabled={isLoading}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <AccountCircle color="action" />
                </InputAdornment>
              ),
            }}
          />

          {/* Password Field */}
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleChange('password')}
            error={!!validationErrors.password}
            helperText={validationErrors.password}
            disabled={isLoading}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={togglePasswordVisibility}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* Marketplace Selection */}
          <FormControl 
            fullWidth 
            sx={{ mb: 3 }}
            error={!!validationErrors.marketplace}
          >
            <InputLabel id="marketplace-label">Marketplace</InputLabel>
            <Select
              labelId="marketplace-label"
              value={formData.marketplace}
              label="Marketplace"
              onChange={handleChange('marketplace')}
              disabled={isLoading}
              startAdornment={
                <InputAdornment position="start">
                  <Public color="action" />
                </InputAdornment>
              }
            >
              {MARKETPLACES.map((marketplace) => (
                <MenuItem key={marketplace.value} value={marketplace.value}>
                  {marketplace.label}
                </MenuItem>
              ))}
            </Select>
            {validationErrors.marketplace && (
              <Typography variant="caption" color="error" sx={{ mt: 0.5, ml: 2 }}>
                {validationErrors.marketplace}
              </Typography>
            )}
          </FormControl>

          {/* Submit Button */}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{ 
              py: 1.5,
              fontSize: '1.1rem',
              position: 'relative',
            }}
          >
            {isLoading ? (
              <>
                <CircularProgress 
                  size={20} 
                  sx={{ 
                    position: 'absolute',
                    left: '50%',
                    marginLeft: '-10px',
                  }} 
                />
                <span style={{ opacity: 0 }}>Sign In</span>
              </>
            ) : (
              'Sign In'
            )}
          </Button>
        </Box>

        <Typography 
          variant="body2" 
          color="text.secondary" 
          textAlign="center"
          sx={{ mt: 3 }}
        >
          We securely connect to your Audible account to analyze your library. 
          Your credentials are encrypted and never stored.
        </Typography>
      </CardContent>
    </Card>
  );
}  