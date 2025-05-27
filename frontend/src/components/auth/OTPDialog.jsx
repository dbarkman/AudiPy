import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Alert,
  Box,
  CircularProgress,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

export default function OTPDialog({ open, onClose }) {
  const { verifyOTP, isLoading, error, clearError } = useAuth();
  const [otpCode, setOtpCode] = useState('');
  const [validationError, setValidationError] = useState('');
  const otpInputRef = useRef(null);

  // Focus the input when dialog opens
  useEffect(() => {
    if (open && otpInputRef.current) {
      // Small delay to ensure dialog is fully rendered
      setTimeout(() => {
        otpInputRef.current.focus();
      }, 100);
    }
  }, [open]);

  // Clear errors when dialog opens
  useEffect(() => {
    if (open) {
      setOtpCode('');
      setValidationError('');
      if (error) {
        clearError();
      }
    }
  }, [open, error, clearError]);

  const handleOtpChange = (event) => {
    const value = event.target.value;
    
    // Only allow digits and limit to reasonable length
    if (/^\d*$/.test(value) && value.length <= 8) {
      setOtpCode(value);
      
      // Clear validation error when user starts typing
      if (validationError) {
        setValidationError('');
      }
      
      // Clear auth error when user makes changes
      if (error) {
        clearError();
      }
    }
  };

  const validateOtp = () => {
    if (!otpCode.trim()) {
      setValidationError('Please enter the verification code');
      return false;
    }
    
    if (otpCode.length < 4) {
      setValidationError('Verification code must be at least 4 digits');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!validateOtp()) {
      return;
    }

    await verifyOTP(otpCode);
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSubmit(event);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown={isLoading}
      PaperProps={{
        sx: {
          mx: 2, // Margin on mobile
          width: '100%',
        },
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon color="primary" />
          <Typography variant="h6" component="span">
            Two-Factor Authentication
          </Typography>
          {!isLoading && (
            <IconButton
              aria-label="close"
              onClick={handleClose}
              sx={{ ml: 'auto' }}
            >
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Audible has sent a verification code to your registered device or email. 
          Please enter the code below to complete your sign-in.
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
          <TextField
            ref={otpInputRef}
            fullWidth
            label="Verification Code"
            value={otpCode}
            onChange={handleOtpChange}
            onKeyPress={handleKeyPress}
            error={!!validationError}
            helperText={validationError || 'Enter the 4-8 digit code from Audible'}
            disabled={isLoading}
            inputProps={{
              inputMode: 'numeric',
              pattern: '[0-9]*',
              autoComplete: 'one-time-code',
            }}
            sx={{
              '& input': {
                fontSize: '1.2rem',
                textAlign: 'center',
                letterSpacing: '0.5em',
              },
            }}
          />
        </Box>

        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ mt: 2, textAlign: 'center' }}
        >
          Didn't receive a code? Check your email or SMS, or try signing in again.
        </Typography>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          onClick={handleClose}
          disabled={isLoading}
          color="inherit"
        >
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isLoading || !otpCode.trim()}
          sx={{ 
            minWidth: 120,
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
              <span style={{ opacity: 0 }}>Verify</span>
            </>
          ) : (
            'Verify'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
} 