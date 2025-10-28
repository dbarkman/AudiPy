import React from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Card,
  CardContent,
  Button,
  Grid,
  useMediaQuery,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Audiotrack,
  Search,
  Recommend,
  Analytics,
} from '@mui/icons-material';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './components/Dashboard';
import UserProfile from './components/UserProfile';
import Library from './components/Library';
import Recommendations from './components/Recommendations';

// Create a modern theme with enhanced design tokens
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#26a69a',
      light: '#4db6ac',
      dark: '#00695c',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.01562em',
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 0, 0, 0.05)',
    '0px 4px 8px rgba(0, 0, 0, 0.08)',
    '0px 8px 16px rgba(0, 0, 0, 0.1)',
    '0px 12px 24px rgba(0, 0, 0, 0.12)',
    '0px 16px 32px rgba(0, 0, 0, 0.15)',
    '0px 20px 40px rgba(0, 0, 0, 0.18)',
    '0px 24px 48px rgba(0, 0, 0, 0.2)',
    '0px 28px 56px rgba(0, 0, 0, 0.22)',
    '0px 32px 64px rgba(0, 0, 0, 0.24)',
    '0px 36px 72px rgba(0, 0, 0, 0.26)',
    '0px 40px 80px rgba(0, 0, 0, 0.28)',
    '0px 44px 88px rgba(0, 0, 0, 0.3)',
    '0px 48px 96px rgba(0, 0, 0, 0.32)',
    '0px 52px 104px rgba(0, 0, 0, 0.34)',
    '0px 56px 112px rgba(0, 0, 0, 0.36)',
    '0px 60px 120px rgba(0, 0, 0, 0.38)',
    '0px 64px 128px rgba(0, 0, 0, 0.4)',
    '0px 68px 136px rgba(0, 0, 0, 0.42)',
    '0px 72px 144px rgba(0, 0, 0, 0.44)',
    '0px 76px 152px rgba(0, 0, 0, 0.46)',
    '0px 80px 160px rgba(0, 0, 0, 0.48)',
    '0px 84px 168px rgba(0, 0, 0, 0.5)',
    '0px 88px 176px rgba(0, 0, 0, 0.52)',
    '0px 92px 184px rgba(0, 0, 0, 0.54)',
  ],
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.08)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.12)',
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          textTransform: 'none',
          fontWeight: 600,
          padding: '12px 24px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          boxShadow: '0px 4px 12px rgba(25, 118, 210, 0.3)',
          '&:hover': {
            boxShadow: '0px 6px 16px rgba(25, 118, 210, 0.4)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
          },
        },
      },
    },
  },
});

// Landing page component for non-authenticated users
function LandingPage() {
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const navigationItems = [
    { text: 'Home', href: '#home' },
    { text: 'Features', href: '#features' },
    { text: 'About', href: '#about' },
    { text: 'Login', href: '#login' },
  ];

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Typography variant="h6" sx={{ my: 2 }}>
        AudiPy
      </Typography>
      <List>
        {navigationItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemText primary={item.text} sx={{ textAlign: 'center' }} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  const features = [
    {
      icon: <Search sx={{ fontSize: 40 }} />,
      title: 'Library Analysis',
      description: 'Analyze your entire Audible library to discover patterns and preferences.',
    },
    {
      icon: <Recommend sx={{ fontSize: 40 }} />,
      title: 'Smart Recommendations',
      description: 'Get personalized book recommendations based on your favorite authors, narrators, and series.',
    },
    {
      icon: <Analytics sx={{ fontSize: 40 }} />,
      title: 'Insights & Analytics',
      description: 'Discover insights about your reading habits and find great deals on new audiobooks.',
    },
  ];

  return (
    <>
      {/* Navigation */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Audiotrack sx={{ mr: 2 }} />
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600 }}
          >
            AudiPy
          </Typography>
          
          {isMobile ? (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
            >
              <MenuIcon />
            </IconButton>
          ) : (
            <Box sx={{ display: 'flex', gap: 2 }}>
              {navigationItems.map((item) => (
                <Button key={item.text} color="inherit">
                  {item.text}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>

      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 50%, #81c784 100%)',
          color: 'white',
          py: { xs: 8, md: 12 },
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)',
          },
        }}
      >
        <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <Typography variant="h1" gutterBottom sx={{ mb: 3 }}>
            Discover Your Next Great Listen
          </Typography>
          <Typography variant="h5" sx={{ mb: 5, opacity: 0.95, fontWeight: 400 }}>
            Analyze your Audible library and get personalized audiobook recommendations powered by AI
          </Typography>
          <Button
            variant="contained"
            size="large"
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              px: 5,
              py: 2,
              fontSize: '1.125rem',
              fontWeight: 600,
              borderRadius: 3,
              boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.15)',
              '&:hover': {
                bgcolor: 'grey.50',
                transform: 'translateY(-2px)',
                boxShadow: '0px 12px 32px rgba(0, 0, 0, 0.2)',
              },
            }}
            href="#login"
          >
            Get Started Free
          </Button>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 12 }, textAlign: 'center' }} id="features">
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography variant="h2" gutterBottom sx={{ mb: 2 }}>
            Powerful Features
          </Typography>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 600, mx: 'auto', fontWeight: 400 }}
          >
            Everything you need to enhance your audiobook experience and discover your next favorite listen
          </Typography>
        </Box>
        
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  textAlign: 'center',
                  p: 4,
                  border: '1px solid',
                  borderColor: 'grey.200',
                  background: 'linear-gradient(145deg, #ffffff 0%, #fafafa 100%)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    borderColor: 'primary.light',
                    boxShadow: '0px 16px 40px rgba(25, 118, 210, 0.15)',
                  },
                }}
              >
                <CardContent sx={{ p: 0 }}>
                  <Box 
                    sx={{ 
                      p: 2,
                      borderRadius: '50%',
                      bgcolor: 'primary.light',
                      color: 'white',
                      width: 80,
                      height: 80,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" gutterBottom sx={{ mb: 2 }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Login Section */}
      <Box sx={{ bgcolor: 'grey.50', py: { xs: 6, md: 10 } }} id="login">
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h2" textAlign="center" gutterBottom>
            Ready to Get Started?
          </Typography>
          <Typography
            variant="h6"
            textAlign="center"
            color="text.secondary"
            sx={{ mb: 4 }}
          >
            Sign in with your Audible account to begin analyzing your library
          </Typography>
          
          {/* The ProtectedRoute component will show the login form here */}
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        </Container>
      </Box>
    </>
  );
}

// Authenticated app layout
function AuthenticatedApp() {
  return (
    <>
      {/* Simple header for authenticated users */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Audiotrack sx={{ mr: 2 }} />
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600 }}
          >
            AudiPy
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profile" element={<UserProfile />} />
        <Route path="/library" element={<Library />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

// Main app component with authentication
function AppContent() {
  const { isAuthenticated } = useAuth();

  // Show authenticated app if logged in, landing page if not
  if (isAuthenticated) {
    return <AuthenticatedApp />;
  }

  return <LandingPage />;
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%'
      }}>
        <AuthProvider>
          <Router>
            <Box sx={{ width: '100%', maxWidth: '1200px' }}>
              <AppContent />
            </Box>
          </Router>
        </AuthProvider>
      </Box>
    </ThemeProvider>
  );
}

export default App;
