import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  AutoAwesome,
  Refresh,
  FilterList,
  Star,
  Schedule,
  Person,
  RecordVoiceOver,
  MenuBook,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

const Recommendations = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState(null);
  
  // Pagination and filtering
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [filterType, setFilterType] = useState('');
  
  const pageSize = 12;

  // Load recommendations
  const loadRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        page,
        page_size: pageSize,
      };
      
      if (filterType) {
        params.recommendation_type = filterType;
      }
      
      const response = await api.get('/recommendations', { params });
      
      setRecommendations(response.data.recommendations);
      setTotalCount(response.data.total_count);
      setTotalPages(Math.ceil(response.data.total_count / pageSize));
      
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setError('Failed to load recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Load generation status
  const loadGenerationStatus = async () => {
    try {
      const response = await api.get('/recommendations/status');
      setGenerationStatus(response.data);
      setGenerating(response.data.is_generating);
    } catch (err) {
      console.error('Failed to load generation status:', err);
    }
  };

  // Generate recommendations
  const generateRecommendations = async () => {
    try {
      setError(null);
      const response = await api.post('/recommendations/generate');
      
      if (response.data.success) {
        setGenerating(true);
        // Poll for status updates
        const pollStatus = setInterval(async () => {
          await loadGenerationStatus();
          const status = await api.get('/recommendations/status');
          if (!status.data.is_generating) {
            clearInterval(pollStatus);
            setGenerating(false);
            loadRecommendations(); // Reload recommendations
          }
        }, 2000);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Failed to generate recommendations:', err);
      setError('Failed to start recommendation generation. Please try again.');
    }
  };

  // Format runtime
  const formatRuntime = (minutes) => {
    if (!minutes) return 'Unknown';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Get confidence color
  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'default';
  };

  // Get type icon
  const getTypeIcon = (type) => {
    switch (type) {
      case 'author': return <Person fontSize="small" />;
      case 'narrator': return <RecordVoiceOver fontSize="small" />;
      case 'series': return <MenuBook fontSize="small" />;
      default: return <Star fontSize="small" />;
    }
  };

  useEffect(() => {
    loadRecommendations();
    loadGenerationStatus();
  }, [page, filterType]);

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleFilterChange = (event) => {
    setFilterType(event.target.value);
    setPage(1); // Reset to first page when filtering
  };

  const clearError = () => setError(null);

  return (
    <Container maxWidth="xl" sx={{ py: 4, mx: 'auto' }}>
      {/* Header */}
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
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            <AutoAwesome sx={{ mr: 1, verticalAlign: 'middle' }} />
            Recommendations
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Personalized book recommendations based on your library
          </Typography>
        </Box>
      </Box>

      {/* Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<AutoAwesome />}
          onClick={generateRecommendations}
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate New Recommendations'}
        </Button>
        
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={loadRecommendations}
          disabled={loading}
        >
          Refresh
        </Button>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Filter by Type</InputLabel>
          <Select
            value={filterType}
            label="Filter by Type"
            onChange={handleFilterChange}
            startAdornment={<FilterList sx={{ mr: 1 }} />}
          >
            <MenuItem value="">All Types</MenuItem>
            <MenuItem value="author">Author</MenuItem>
            <MenuItem value="narrator">Narrator</MenuItem>
            <MenuItem value="series">Series</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Generation Status */}
      {generationStatus && (
        <Box sx={{ mb: 3 }}>
          <Alert 
            severity={generating ? "info" : generationStatus.total_recommendations > 0 ? "success" : "warning"}
            sx={{ mb: 2 }}
          >
            {generating ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                {generationStatus.status_message}
              </Box>
            ) : (
              <>
                {generationStatus.total_recommendations > 0 ? (
                  `${generationStatus.total_recommendations} recommendations available`
                ) : (
                  'No recommendations yet. Click "Generate New Recommendations" to get started!'
                )}
                {generationStatus.last_generated && (
                  <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                    Last generated: {new Date(generationStatus.last_generated).toLocaleString()}
                  </Typography>
                )}
              </>
            )}
          </Alert>
        </Box>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={clearError} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Recommendations Grid */}
      {!loading && recommendations.length > 0 && (
        <>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              {totalCount} Recommendations Found
              {filterType && ` (${filterType})`}
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {recommendations.map((rec) => (
              <Grid item xs={12} sm={6} md={4} key={`${rec.asin}-${rec.recommendation_type}-${rec.source_name}`}>
                <Card sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  border: '1px solid',
                  borderColor: 'grey.200',
                  borderRadius: 3,
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&:hover': {
                    borderColor: 'primary.light',
                    boxShadow: '0px 12px 32px rgba(25, 118, 210, 0.15)',
                    transform: 'translateY(-4px)',
                  }
                }}>
                  <CardContent sx={{ flexGrow: 1, p: 3 }}>
                    {/* Book Title */}
                    <Typography variant="h6" component="h3" gutterBottom noWrap sx={{ fontWeight: 600 }}>
                      {rec.title}
                    </Typography>
                    
                    {/* Subtitle */}
                    {rec.subtitle && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {rec.subtitle}
                      </Typography>
                    )}

                    {/* Authors */}
                    <Typography variant="body2" gutterBottom>
                      <strong>By:</strong> {rec.authors.join(', ')}
                    </Typography>

                    {/* Narrators */}
                    {rec.narrators.length > 0 && (
                      <Typography variant="body2" gutterBottom>
                        <strong>Narrated by:</strong> {rec.narrators.join(', ')}
                      </Typography>
                    )}

                    {/* Series */}
                    {rec.series && (
                      <Typography variant="body2" gutterBottom>
                        <strong>Series:</strong> {rec.series}
                      </Typography>
                    )}

                    {/* Runtime */}
                    {rec.runtime_length_min && (
                      <Typography variant="body2" gutterBottom>
                        <Schedule fontSize="small" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                        {formatRuntime(rec.runtime_length_min)}
                      </Typography>
                    )}

                    <Divider sx={{ my: 2 }} />

                    {/* Recommendation Info */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip
                        icon={getTypeIcon(rec.recommendation_type)}
                        label={rec.recommendation_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ borderRadius: 2 }}
                      />
                      <Chip
                        label={`${(rec.confidence_score * 100).toFixed(0)}% match`}
                        size="small"
                        color={getConfidenceColor(rec.confidence_score)}
                        sx={{ borderRadius: 2 }}
                      />
                      <Chip
                        label={rec.purchase_method}
                        size="small"
                        color={rec.purchase_method === 'cash' ? 'success' : 'default'}
                        sx={{ borderRadius: 2 }}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary">
                      Recommended because you like: <strong>{rec.source_name}</strong>
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="large"
              />
            </Box>
          )}
        </>
      )}

      {/* No Recommendations */}
      {!loading && recommendations.length === 0 && !error && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <AutoAwesome sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No Recommendations Yet
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Generate personalized recommendations based on your library
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<AutoAwesome />}
            onClick={generateRecommendations}
            disabled={generating}
          >
            Generate Recommendations
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default Recommendations;      