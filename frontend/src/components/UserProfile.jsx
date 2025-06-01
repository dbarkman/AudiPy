import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Avatar
} from '@mui/material';
import {
  Person as PersonIcon,
  Settings as SettingsIcon,
  LibraryBooks as LibraryIcon,
  Recommend as RecommendIcon,
  Save as SaveIcon,
  Sync as SyncIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

const UserProfile = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState({
    language: 'english',
    marketplace: 'us',
    max_price: 12.66,
    notifications_enabled: true,
    price_alert_enabled: true,
    new_release_alerts: true
  });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const marketplaces = [
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'de', label: 'Germany' },
    { value: 'fr', label: 'France' },
    { value: 'ca', label: 'Canada' },
    { value: 'au', label: 'Australia' },
    { value: 'jp', label: 'Japan' }
  ];

  const languages = [
    { value: 'english', label: 'English' },
    { value: 'german', label: 'Deutsch' },
    { value: 'french', label: 'Français' },
    { value: 'spanish', label: 'Español' },
    { value: 'italian', label: 'Italiano' },
    { value: 'japanese', label: '日本語' }
  ];

  const frequencies = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'never', label: 'Never' }
  ];

  useEffect(() => {
    loadProfileData();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const [profileRes, statusRes] = await Promise.all([
        api.get('/user/profile'),
        api.get('/user/status')
      ]);
      
      setProfile(profileRes.data.profile);
      setPreferences(profileRes.data.preferences);
      setStatus(statusRes.data);
    } catch (error) {
      console.error('Failed to load profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile data' });
    } finally {
      setLoading(false);
    }
  };

  const handlePreferenceChange = (field, value) => {
    setPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handlePriceChange = (event, newValue) => {
    setPreferences(prev => ({
      ...prev,
      max_price: newValue
    }));
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      await api.put('/user/preferences', preferences);
      setMessage({ type: 'success', text: 'Preferences saved successfully!' });
      
      // Reload status to reflect changes
      const statusRes = await api.get('/user/status');
      setStatus(statusRes.data);
    } catch (error) {
      console.error('Failed to save preferences:', error);
      setMessage({ type: 'error', text: 'Failed to save preferences' });
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'syncing': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4, mx: 'auto' }}>
      {/* Header with Back Button */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton 
          onClick={() => navigate('/')}
          sx={{ 
            mr: 1,
            bgcolor: 'primary.light',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.main',
            },
          }}
        >
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          User Profile
        </Typography>
      </Box>

      {message && (
        <Alert 
          severity={message.type} 
          onClose={() => setMessage(null)}
          sx={{ mb: 3 }}
        >
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Profile Overview */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ 
            p: 4, 
            textAlign: 'center',
            borderRadius: 3,
            border: '1px solid',
            borderColor: 'grey.200',
            background: 'linear-gradient(145deg, #ffffff 0%, #fafafa 100%)',
          }}>
            <Avatar
              sx={{ 
                width: 100, 
                height: 100, 
                mx: 'auto', 
                mb: 3,
                bgcolor: 'primary.main',
                boxShadow: '0px 8px 24px rgba(25, 118, 210, 0.3)',
              }}
            >
              <PersonIcon sx={{ fontSize: 48 }} />
            </Avatar>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              {profile?.username || 'User'}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Member since {formatDate(profile?.created_at)}
            </Typography>
            
            <Divider sx={{ my: 3 }} />
            
            {/* Account Status */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                Audible Account
              </Typography>
              <Chip
                label={status?.sync?.sync_status || 'Not Connected'}
                color={getStatusColor(status?.sync?.sync_status)}
                size="small"
                sx={{ borderRadius: 2 }}
              />
            </Box>

            {/* Quick Stats */}
            <Grid container spacing={2} sx={{ mt: 2 }}>
              <Grid item xs={6}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <LibraryIcon color="primary" sx={{ mb: 1 }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {status?.library?.total_books || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Books
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <RecommendIcon color="primary" sx={{ mb: 1 }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {status?.recommendations?.total_recommendations || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Recommendations
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Preferences */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={3}>
              <SettingsIcon sx={{ mr: 1 }} />
              <Typography variant="h5">Preferences</Typography>
            </Box>

            <Grid container spacing={3}>
              {/* Language & Marketplace */}
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={preferences.language}
                    label="Language"
                    onChange={(e) => handlePreferenceChange('language', e.target.value)}
                  >
                    {languages.map((lang) => (
                      <MenuItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Marketplace</InputLabel>
                  <Select
                    value={preferences.marketplace}
                    label="Marketplace"
                    onChange={(e) => handlePreferenceChange('marketplace', e.target.value)}
                  >
                    {marketplaces.map((market) => (
                      <MenuItem key={market.value} value={market.value}>
                        {market.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Max Price */}
              <Grid item xs={12}>
                <Typography gutterBottom>
                  Maximum Price: ${preferences.max_price}
                </Typography>
                <Slider
                  value={preferences.max_price}
                  onChange={handlePriceChange}
                  valueLabelDisplay="auto"
                  min={0}
                  max={50}
                  step={0.99}
                  marks={[
                    { value: 0, label: '$0' },
                    { value: 12.66, label: '$12.66' },
                    { value: 25, label: '$25' },
                    { value: 50, label: '$50+' }
                  ]}
                />
              </Grid>

              {/* Notification Preferences */}
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications_enabled}
                      onChange={(e) => handlePreferenceChange('notifications_enabled', e.target.checked)}
                    />
                  }
                  label="Email Notifications"
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.price_alert_enabled}
                      onChange={(e) => handlePreferenceChange('price_alert_enabled', e.target.checked)}
                    />
                  }
                  label="Price Alerts"
                />
              </Grid>

              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.new_release_alerts}
                      onChange={(e) => handlePreferenceChange('new_release_alerts', e.target.checked)}
                    />
                  }
                  label="New Release Alerts"
                />
              </Grid>

              {/* Save Button */}
              <Grid item xs={12}>
                <Box display="flex" justifyContent="flex-end" gap={2}>
                  <Button
                    variant="contained"
                    startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                    onClick={savePreferences}
                    disabled={saving}
                  >
                    {saving ? 'Saving...' : 'Save Preferences'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Sync Status */}
          {status?.sync && (
            <Paper sx={{ p: 3, mt: 3 }}>
              <Box display="flex" alignItems="center" mb={2}>
                <SyncIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Sync Status</Typography>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Last Sync
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(status.sync.last_sync_at)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={status.sync.sync_status}
                    color={getStatusColor(status.sync.sync_status)}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Token Expires
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(status.sync.tokens_expires_at)}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default UserProfile;      