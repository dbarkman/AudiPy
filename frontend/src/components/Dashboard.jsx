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
      comingSoon: true,
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Avatar
          sx={{
            width: 80,
            height: 80,
            mx: 'auto',
            mb: 2,
            bgcolor: 'primary.main',
            fontSize: '2rem',
          }}
        >
          {user?.username?.charAt(0)?.toUpperCase() || 'U'}
        </Avatar>
        
        <Typography variant="h4" gutterBottom>
          Welcome back!
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Ready to discover your next great listen?
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
          <Chip 
            label={`Marketplace: ${user?.marketplace?.toUpperCase() || 'US'}`} 
            variant="outlined" 
            size="small" 
          />
          <Chip 
            label="Connected to Audible" 
            color="success" 
            variant="outlined" 
            size="small" 
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Settings />}
            onClick={() => navigate('/profile')}
            size="small"
          >
            Profile & Settings
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExitToApp />}
            onClick={handleLogout}
            size="small"
          >
            Sign Out
          </Button>
        </Box>
      </Box>

      {/* Dashboard Cards */}
      <Grid container spacing={3}>
        {dashboardCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  transition: 'transform 0.2s ease-in-out',
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
                    top: 8,
                    right: 8,
                    zIndex: 1,
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
                  p: 3,
                }}
              >
                <Box
                  sx={{
                    color: `${card.color}.main`,
                    mb: 2,
                  }}
                >
                  {card.icon}
                </Box>
                
                <Typography variant="h6" gutterBottom>
                  {card.title}
                </Typography>
                
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 3, flexGrow: 1 }}
                >
                  {card.description}
                </Typography>
                
                <Button
                  variant={card.comingSoon ? 'outlined' : 'contained'}
                  color={card.color}
                  disabled={card.comingSoon}
                  fullWidth
                  onClick={card.onClick}
                >
                  {card.action}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Phase 3 Complete Message */}
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
          🎉 Phase 3: Library Management Complete!
        </Typography>
        <Typography variant="body1">
          ✅ Authentication & User Profile (Phase 1 & 2) <br/>
          ✅ Library Display & Management (Phase 3) <br/>
          🔄 Next: Recommendations Engine (Phase 4)
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
          Click "View Library" above to see your books with search, filtering, and sync capabilities!
        </Typography>
      </Box>
    </Container>
  );
} 