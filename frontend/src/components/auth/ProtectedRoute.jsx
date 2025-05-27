import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import LoginForm from './LoginForm';
import OTPDialog from './OTPDialog';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading, requiresOTP } = useAuth();

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '50vh',
          gap: 2,
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body1" color="text.secondary">
          Checking authentication...
        </Typography>
      </Box>
    );
  }

  // Show OTP dialog if required
  if (requiresOTP) {
    return (
      <>
        <LoginForm />
        <OTPDialog 
          open={requiresOTP} 
          onClose={() => {
            // OTP dialog shouldn't be closeable during the flow
            // The user needs to complete OTP or start over
          }} 
        />
      </>
    );
  }

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <LoginForm />;
  }

  // User is authenticated, show protected content
  return children;
} 