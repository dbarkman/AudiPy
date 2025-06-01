import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Grid,
  Avatar,
  Chip,
} from '@mui/material';
import {
  LibraryBooks,
  Recommend,
  Analytics,
  Sync,
  ExitToApp,
  Settings,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
  };

  const dashboardCards = [
    {
      title: 'My Library',
      description: 'View and manage your Audible library',
      icon: <LibraryBooks sx={{ fontSize: 40 }} />,
      action: 'View Library',
      color: 'primary',
      comingSoon: false,
      onClick: () => navigate('/library'),
    },
    {
      title: 'Recommendations',
      description: 'Get personalized book recommendations',
      icon: <Recommend sx={{ fontSize: 40 }} />,
      action: 'Get Recommendations',
      color: 'secondary',
      comingSoon: false,
      onClick: () => navigate('/recommendations'),
    },
    {
      title: 'Analytics',
      description: 'Insights about your reading habits',
      icon: <Analytics sx={{ fontSize: 40 }} />,
      action: 'View Analytics',
      color: 'success',
      comingSoon: true,
    },
    {
      title: 'Sync Library',
      description: 'Update your library from Audible',
      icon: <Sync sx={{ fontSize: 40 }} />,
      action: 'Sync Now',
      color: 'warning',
      comingSoon: true,
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 6, textAlign: 'center' }}>
        <Avatar
          sx={{
            width: 100,
            height: 100,
            mx: 'auto',
            mb: 3,
            bgcolor: 'primary.main',
            fontSize: '2.5rem',
            boxShadow: '0px 8px 24px rgba(25, 118, 210, 0.3)',
          }}
        >
          {user?.username?.charAt(0)?.toUpperCase() || 'U'}
        </Avatar>
        
        <Typography variant="h4" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
          Welcome back, {user?.username || 'User'}!
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, fontSize: '1.125rem' }}>
          Ready to discover your next great listen?
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <Chip 
            label={`Marketplace: ${user?.marketplace?.toUpperCase() || 'US'}`} 
            variant="outlined" 
            sx={{ 
              borderRadius: 3,
              fontWeight: 500,
            }}
          />
          <Chip 
            label="Connected to Audible" 
            color="success" 
            variant="filled"
            sx={{ 
              borderRadius: 3,
              fontWeight: 500,
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<Settings />}
            onClick={() => navigate('/profile')}
            sx={{ borderRadius: 3 }}
          >
            Profile & Settings
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExitToApp />}
            onClick={handleLogout}
            sx={{ borderRadius: 3 }}
          >
            Sign Out
          </Button>
        </Box>
      </Box>

      {/* Dashboard Cards */}
      <Grid container spacing={4}>
        {dashboardCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                border: '1px solid',
                borderColor: 'grey.200',
                background: 'linear-gradient(145deg, #ffffff 0%, #fafafa 100%)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: card.comingSoon ? 'default' : 'pointer',
                '&:hover': {
                  transform: card.comingSoon ? 'none' : 'translateY(-4px)',
                  borderColor: card.comingSoon ? 'grey.200' : 'primary.light',
                  boxShadow: card.comingSoon ? 'inherit' : '0px 12px 32px rgba(25, 118, 210, 0.15)',
                },
              }}
            >
              {card.comingSoon && (
                <Chip
                  label="Coming Soon"
                  size="small"
                  color="info"
                  sx={{
                    position: 'absolute',
                    top: 12,
                    right: 12,
                    zIndex: 1,
                    borderRadius: 2,
                  }}
                />
              )}
              
              <CardContent
                sx={{
                  flexGrow: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center',
                  p: 4,
                }}
              >
                <Box
                  sx={{
                    p: 2,
                    borderRadius: '50%',
                    bgcolor: `${card.color}.light`,
                    color: 'white',
                    mb: 3,
                    width: 80,
                    height: 80,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {card.icon}
                </Box>
                
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  {card.title}
                </Typography>
                
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 4, flexGrow: 1, lineHeight: 1.6 }}
                >
                  {card.description}
                </Typography>
                
                <Button
                  variant={card.comingSoon ? 'outlined' : 'contained'}
                  color={card.color}
                  disabled={card.comingSoon}
                  fullWidth
                  onClick={card.onClick}
                  sx={{ 
                    borderRadius: 3,
                    py: 1.5,
                    fontWeight: 600,
                  }}
                >
                  {card.action}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Phase 4 Complete Message */}
      <Box
        sx={{
          mt: 6,
          p: 3,
          bgcolor: 'success.light',
          borderRadius: 2,
          textAlign: 'center',
        }}
      >
        <Typography variant="h6" gutterBottom>
          🎉 Phase 4: AI Recommendations Engine Complete!
        </Typography>
        <Typography variant="body1">
          ✅ Authentication & User Profile (Phase 1 & 2) <br/>
          ✅ Library Display & Management (Phase 3) <br/>
          ✅ AI Recommendations Engine (Phase 4)
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
          Click "Get Recommendations" above to discover personalized book suggestions based on your library!
        </Typography>
      </Box>
    </Container>
  );
}      