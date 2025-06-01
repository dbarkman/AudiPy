import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Pagination,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Fab,
  Tooltip,
  IconButton,
  Menu,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Sync as SyncIcon,
  Book as BookIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  Language as LanguageIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';

const Library = () => {
  const { user } = useAuth();
  
  // State for library data
  const [books, setBooks] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [hasNext, setHasNext] = useState(false);
  
  // State for search and filtering
  const [searchTerm, setSearchTerm] = useState('');
  const [authorFilter, setAuthorFilter] = useState('');
  const [narratorFilter, setNarratorFilter] = useState('');
  const [seriesFilter, setSeriesFilter] = useState('');
  const [sortBy, setSortBy] = useState('title');
  const [sortOrder, setSortOrder] = useState('asc');
  
  // State for sync functionality
  const [syncStatus, setSyncStatus] = useState({
    is_syncing: false,
    last_sync: null,
    total_books: 0,
    status_message: 'Ready to sync'
  });
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  
  // State for book details dialog
  const [selectedBook, setSelectedBook] = useState(null);
  const [bookDetailsOpen, setBookDetailsOpen] = useState(false);
  const [bookDetails, setBookDetails] = useState(null);
  
  // State for filter menu
  const [filterMenuAnchor, setFilterMenuAnchor] = useState(null);

  // Fetch library data
  const fetchLibrary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort_by: sortBy,
        sort_order: sortOrder
      });
      
      if (searchTerm) params.append('search', searchTerm);
      if (authorFilter) params.append('author', authorFilter);
      if (narratorFilter) params.append('narrator', narratorFilter);
      if (seriesFilter) params.append('series', seriesFilter);
      
      const response = await api.get(`/library?${params}`);
      
      setBooks(response.data.books);
      setTotalCount(response.data.total_count);
      setHasNext(response.data.has_next);
      
    } catch (err) {
      console.error('Failed to fetch library:', err);
      setError('Failed to load library. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchTerm, authorFilter, narratorFilter, seriesFilter, sortBy, sortOrder]);

  // Fetch sync status
  const fetchSyncStatus = useCallback(async () => {
    try {
      const response = await api.get('/library/status');
      setSyncStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch sync status:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchLibrary();
    fetchSyncStatus();
  }, [fetchLibrary, fetchSyncStatus]);

  // Poll sync status when syncing
  useEffect(() => {
    let interval;
    if (syncStatus.is_syncing) {
      interval = setInterval(fetchSyncStatus, 2000); // Poll every 2 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [syncStatus.is_syncing, fetchSyncStatus]);

  // Handle search with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1); // Reset to first page when searching
      fetchLibrary();
    }, 500);
    
    return () => clearTimeout(timer);
  }, [searchTerm, authorFilter, narratorFilter, seriesFilter]);

  // Handle sync library
  const handleSync = async () => {
    try {
      const response = await api.post('/library/sync');
      if (response.data.success) {
        setSyncDialogOpen(true);
        fetchSyncStatus(); // Start polling
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Failed to start sync:', err);
      setError('Failed to start library sync. Please try again.');
    }
  };

  // Handle book details
  const handleBookDetails = async (book) => {
    try {
      setSelectedBook(book);
      setBookDetailsOpen(true);
      
      const response = await api.get(`/books/${book.asin}`);
      setBookDetails(response.data);
    } catch (err) {
      console.error('Failed to fetch book details:', err);
      setError('Failed to load book details.');
    }
  };

  // Format runtime
  const formatRuntime = (minutes) => {
    if (!minutes) return 'Unknown';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  // Handle page change
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  // Handle sort change
  const handleSortChange = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setPage(1);
  };

  // Clear filters
  const clearFilters = () => {
    setSearchTerm('');
    setAuthorFilter('');
    setNarratorFilter('');
    setSeriesFilter('');
    setPage(1);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            My Library
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {totalCount} books • Last sync: {syncStatus.last_sync ? formatDate(syncStatus.last_sync) : 'Never'}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh library">
            <IconButton onClick={fetchLibrary} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="contained"
            startIcon={<SyncIcon />}
            onClick={handleSync}
            disabled={syncStatus.is_syncing}
          >
            {syncStatus.is_syncing ? 'Syncing...' : 'Sync Library'}
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search books..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              placeholder="Filter by author"
              value={authorFilter}
              onChange={(e) => setAuthorFilter(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              placeholder="Filter by narrator"
              value={narratorFilter}
              onChange={(e) => setNarratorFilter(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              placeholder="Filter by series"
              value={seriesFilter}
              onChange={(e) => setSeriesFilter(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BookIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={2}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton
                onClick={(e) => setFilterMenuAnchor(e.currentTarget)}
                title="Sort options"
              >
                <SortIcon />
              </IconButton>
              
              <Button
                variant="outlined"
                size="small"
                onClick={clearFilters}
                disabled={!searchTerm && !authorFilter && !narratorFilter && !seriesFilter}
              >
                Clear
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Books Grid */}
      {!loading && (
        <>
          <Grid container spacing={3}>
            {books.map((book) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={book.asin}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    cursor: 'pointer',
                    border: '1px solid',
                    borderColor: 'grey.200',
                    borderRadius: 3,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      borderColor: 'primary.light',
                      boxShadow: '0px 12px 32px rgba(255, 102, 0, 0.15)',
                      transform: 'translateY(-4px)',
                    }
                  }}
                  onClick={() => handleBookDetails(book)}
                >
                  <CardMedia
                    component="div"
                    sx={{
                      height: 220,
                      background: 'linear-gradient(145deg, #f5f5f5 0%, #e0e0e0 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '12px 12px 0 0',
                    }}
                  >
                    <BookIcon sx={{ fontSize: 64, color: 'grey.400' }} />
                  </CardMedia>
                  
                  <CardContent sx={{ flexGrow: 1, p: 3 }}>
                    <Typography variant="h6" component="h3" gutterBottom noWrap sx={{ fontWeight: 600 }}>
                      {book.title}
                    </Typography>
                    
                    {book.subtitle && (
                      <Typography variant="body2" color="text.secondary" gutterBottom noWrap>
                        {book.subtitle}
                      </Typography>
                    )}
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      By: {book.authors.join(', ') || 'Unknown Author'}
                    </Typography>
                    
                    {book.narrators.length > 0 && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Narrated by: {book.narrators.join(', ')}
                      </Typography>
                    )}
                    
                    <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {book.runtime_length_min && (
                        <Chip
                          icon={<ScheduleIcon />}
                          label={formatRuntime(book.runtime_length_min)}
                          size="small"
                          variant="outlined"
                          sx={{ borderRadius: 2 }}
                        />
                      )}
                      
                      {book.language && (
                        <Chip
                          icon={<LanguageIcon />}
                          label={book.language}
                          size="small"
                          variant="outlined"
                          sx={{ borderRadius: 2 }}
                        />
                      )}
                    </Box>
                    
                    {book.series && (
                      <Typography variant="caption" display="block" sx={{ mt: 2, fontWeight: 500 }}>
                        Series: {book.series}
                      </Typography>
                    )}
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
                showFirstButton
                showLastButton
              />
            </Box>
          )}

          {/* Empty State */}
          {books.length === 0 && !loading && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <BookIcon sx={{ fontSize: 80, color: 'grey.400', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No books found
              </Typography>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                {searchTerm || authorFilter || narratorFilter || seriesFilter
                  ? 'Try adjusting your search or filters'
                  : 'Sync your library to see your books here'
                }
              </Typography>
              {!searchTerm && !authorFilter && !narratorFilter && !seriesFilter && (
                <Button
                  variant="contained"
                  startIcon={<SyncIcon />}
                  onClick={handleSync}
                  sx={{ mt: 2 }}
                  disabled={syncStatus.is_syncing}
                >
                  Sync Library
                </Button>
              )}
            </Box>
          )}
        </>
      )}

      {/* Sort Menu */}
      <Menu
        anchorEl={filterMenuAnchor}
        open={Boolean(filterMenuAnchor)}
        onClose={() => setFilterMenuAnchor(null)}
      >
        <MenuItem onClick={() => { handleSortChange('title'); setFilterMenuAnchor(null); }}>
          <ListItemText primary="Sort by Title" />
        </MenuItem>
        <MenuItem onClick={() => { handleSortChange('publication_date'); setFilterMenuAnchor(null); }}>
          <ListItemText primary="Sort by Publication Date" />
        </MenuItem>
        <MenuItem onClick={() => { handleSortChange('runtime'); setFilterMenuAnchor(null); }}>
          <ListItemText primary="Sort by Runtime" />
        </MenuItem>
        <MenuItem onClick={() => { handleSortChange('purchase_date'); setFilterMenuAnchor(null); }}>
          <ListItemText primary="Sort by Purchase Date" />
        </MenuItem>
      </Menu>

      {/* Sync Progress Dialog */}
      <Dialog open={syncDialogOpen} onClose={() => setSyncDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Library Sync in Progress</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body1" gutterBottom>
              {syncStatus.status_message}
            </Typography>
            {syncStatus.is_syncing && <LinearProgress />}
          </Box>
          
          {syncStatus.total_books > 0 && (
            <Typography variant="body2" color="text.secondary">
              Total books in library: {syncStatus.total_books}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setSyncDialogOpen(false)}
            disabled={syncStatus.is_syncing}
          >
            {syncStatus.is_syncing ? 'Syncing...' : 'Close'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Book Details Dialog */}
      <Dialog 
        open={bookDetailsOpen} 
        onClose={() => setBookDetailsOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        {selectedBook && (
          <>
            <DialogTitle>{selectedBook.title}</DialogTitle>
            <DialogContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Box
                    sx={{
                      height: 300,
                      backgroundColor: 'grey.200',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: 1
                    }}
                  >
                    <BookIcon sx={{ fontSize: 80, color: 'grey.400' }} />
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={8}>
                  {selectedBook.subtitle && (
                    <Typography variant="h6" gutterBottom>
                      {selectedBook.subtitle}
                    </Typography>
                  )}
                  
                  <Typography variant="body1" gutterBottom>
                    <strong>Authors:</strong> {selectedBook.authors.join(', ') || 'Unknown'}
                  </Typography>
                  
                  {selectedBook.narrators.length > 0 && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Narrators:</strong> {selectedBook.narrators.join(', ')}
                    </Typography>
                  )}
                  
                  {selectedBook.series && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Series:</strong> {selectedBook.series}
                    </Typography>
                  )}
                  
                  {selectedBook.runtime_length_min && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Runtime:</strong> {formatRuntime(selectedBook.runtime_length_min)}
                    </Typography>
                  )}
                  
                  {selectedBook.publication_datetime && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Published:</strong> {formatDate(selectedBook.publication_datetime)}
                    </Typography>
                  )}
                  
                  {selectedBook.purchase_date && (
                    <Typography variant="body1" gutterBottom>
                      <strong>Purchased:</strong> {formatDate(selectedBook.purchase_date)}
                    </Typography>
                  )}
                  
                  {bookDetails?.description && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        Description
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {bookDetails.description}
                      </Typography>
                    </Box>
                  )}
                  
                  {bookDetails?.categories && bookDetails.categories.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        Categories
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {bookDetails.categories.map((category, index) => (
                          <Chip key={index} label={category} size="small" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setBookDetailsOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default Library;  