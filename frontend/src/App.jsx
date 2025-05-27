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

// Create a custom theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#ff6600', // Audible orange
    },
    secondary: {
      main: '#1976d2',
    },
  },
  typography: {
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
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
          background: 'linear-gradient(135deg, #ff6600 0%, #ff8533 100%)',
          color: 'white',
          py: { xs: 6, md: 10 },
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h1" gutterBottom>
            Discover Your Next Great Listen
          </Typography>
          <Typography variant="h5" sx={{ mb: 4, opacity: 0.9 }}>
            Analyze your Audible library and get personalized audiobook recommendations
          </Typography>
          <Button
            variant="contained"
            size="large"
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              '&:hover': {
                bgcolor: 'grey.100',
              },
            }}
            href="#login"
          >
            Get Started
          </Button>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }} id="features">
        <Typography variant="h2" textAlign="center" gutterBottom>
          Features
        </Typography>
        <Typography
          variant="h6"
          textAlign="center"
          color="text.secondary"
          sx={{ mb: 6 }}
        >
          Everything you need to enhance your audiobook experience
        </Typography>
        
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card
                sx={{
                  height: '100%',
                  textAlign: 'center',
                  p: 2,
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    transition: 'transform 0.3s ease-in-out',
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
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
        <Container maxWidth="md">
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
      <AuthProvider>
        <Router>
          <AppContent />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
