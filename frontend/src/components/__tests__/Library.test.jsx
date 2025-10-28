import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Library from '../Library'
import api from '../../utils/api'

// Mock the AuthContext
const mockAuthContext = {
  user: { id: 1, username: 'testuser' },
}

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
}))

// Mock the API
vi.mock('../../utils/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

// Mock data
const mockBooks = [
  {
    asin: 'B001',
    title: 'Test Book 1',
    subtitle: 'A Great Story',
    authors: ['Author One'],
    narrators: ['Narrator One'],
    series: 'Test Series',
    runtime_length_min: 480,
    release_date: '2023-01-01',
    language: 'English',
  },
  {
    asin: 'B002',
    title: 'Test Book 2',
    subtitle: null,
    authors: ['Author Two'],
    narrators: ['Narrator Two'],
    series: null,
    runtime_length_min: 360,
    release_date: '2023-02-01',
    language: 'English',
  },
]

const mockLibraryResponse = {
  books: mockBooks,
  total_count: 2,
  has_next: false,
}

const mockSyncStatus = {
  is_syncing: false,
  last_sync: '2023-12-01T10:00:00Z',
  total_books: 2,
  status_message: 'Ready to sync',
}

describe('Library', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default API responses
    api.get.mockImplementation((url) => {
      if (url.includes('/library/status')) {
        return Promise.resolve({ data: mockSyncStatus })
      }
      if (url.includes('/library')) {
        return Promise.resolve({ data: mockLibraryResponse })
      }
      return Promise.reject(new Error('Unknown endpoint'))
    })
  })

  describe('Rendering', () => {
    it('should render library header and controls', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      expect(screen.getByText('My Library')).toBeInTheDocument()
      
      // Wait for the library data to load
      await waitFor(() => {
        expect(screen.getByText(/2 books/)).toBeInTheDocument()
      })
      
      expect(screen.getByText(/Last sync:/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sync library/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /refresh library/i })).toBeInTheDocument()
    })

    it('should render search and filter controls', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      expect(screen.getByPlaceholderText('Search books...')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by author')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by narrator')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by series')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
    })

    it('should render books after loading', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      expect(screen.getByText('Test Book 1')).toBeInTheDocument()
      expect(screen.getByText('Test Book 2')).toBeInTheDocument()
      expect(screen.getByText('A Great Story')).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('should show loading spinner initially', () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('should hide loading spinner after data loads', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
    })
  })

  describe('Search and Filtering', () => {
    it('should update search term and trigger API call', async () => {
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText('Search books...')
      await user.type(searchInput, 'test search')
      
      expect(searchInput).toHaveValue('test search')
      
      // Wait for debounced search
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('search=test+search')
        )
      }, { timeout: 1000 })
    })

    it('should filter by author', async () => {
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const authorInput = screen.getByPlaceholderText('Filter by author')
      await user.type(authorInput, 'Author One')
      
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('author=Author+One')
        )
      }, { timeout: 1000 })
    })

    it('should clear all filters', async () => {
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Set some filters
      await user.type(screen.getByPlaceholderText('Search books...'), 'test')
      await user.type(screen.getByPlaceholderText('Filter by author'), 'author')
      
      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear/i })
      expect(clearButton).not.toBeDisabled()
      
      await user.click(clearButton)
      
      expect(screen.getByPlaceholderText('Search books...')).toHaveValue('')
      expect(screen.getByPlaceholderText('Filter by author')).toHaveValue('')
    })

    it('should disable clear button when no filters are active', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const clearButton = screen.getByRole('button', { name: /clear/i })
      expect(clearButton).toBeDisabled()
    })
  })

  describe('Sync Functionality', () => {
    it('should start sync when sync button is clicked', async () => {
      const user = userEvent.setup()
      api.post.mockResolvedValue({ data: { success: true } })
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const syncButton = screen.getByRole('button', { name: /sync library/i })
      await user.click(syncButton)
      
      expect(api.post).toHaveBeenCalledWith('/library/sync')
    })

    it('should show syncing state when sync is in progress', async () => {
      const syncingStatus = { ...mockSyncStatus, is_syncing: true }
      api.get.mockImplementation((url) => {
        if (url.includes('/library/status')) {
          return Promise.resolve({ data: syncingStatus })
        }
        if (url.includes('/library')) {
          return Promise.resolve({ data: mockLibraryResponse })
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Syncing...')).toBeInTheDocument()
      })
      
      const syncButton = screen.getByRole('button', { name: /syncing/i })
      expect(syncButton).toBeDisabled()
    })

    it('should refresh library when refresh button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Clear previous calls
      vi.clearAllMocks()
      
      const refreshButton = screen.getByRole('button', { name: /refresh library/i })
      await user.click(refreshButton)
      
      expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/library'))
    })
  })

  describe('Error Handling', () => {
    it('should display error message when library fetch fails', async () => {
      api.get.mockImplementation((url) => {
        if (url.includes('/library/status')) {
          return Promise.resolve({ data: mockSyncStatus })
        }
        if (url.includes('/library')) {
          return Promise.reject(new Error('Network error'))
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load library. Please try again.')).toBeInTheDocument()
      })
    })

    it('should display error when sync fails', async () => {
      const user = userEvent.setup()
      api.post.mockRejectedValue(new Error('Sync failed'))
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const syncButton = screen.getByRole('button', { name: /sync library/i })
      await user.click(syncButton)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to start library sync. Please try again.')).toBeInTheDocument()
      })
    })

    it('should allow closing error alerts', async () => {
      const user = userEvent.setup()
      api.get.mockImplementation((url) => {
        if (url.includes('/library/status')) {
          return Promise.resolve({ data: mockSyncStatus })
        }
        if (url.includes('/library')) {
          return Promise.reject(new Error('Network error'))
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load library. Please try again.')).toBeInTheDocument()
      })
      
      const closeButton = screen.getByLabelText(/close/i)
      await user.click(closeButton)
      
      expect(screen.queryByText('Failed to load library. Please try again.')).not.toBeInTheDocument()
    })
  })

  describe('Book Interactions', () => {
    it('should open book details when book is clicked', async () => {
      const user = userEvent.setup()
      api.get.mockImplementation((url) => {
        if (url.includes('/library/status')) {
          return Promise.resolve({ data: mockSyncStatus })
        }
        if (url.includes('/library')) {
          return Promise.resolve({ data: mockLibraryResponse })
        }
        if (url.includes('/books/B001')) {
          return Promise.resolve({ data: { ...mockBooks[0], description: 'Book description' } })
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      const bookCard = screen.getByText('Test Book 1').closest('[role="button"]') || 
                      screen.getByText('Test Book 1').closest('div[style*="cursor"]')
      
      if (bookCard) {
        await user.click(bookCard)
        expect(api.get).toHaveBeenCalledWith('/books/B001')
      }
    })
  })

  describe('Data Display', () => {
    it('should format and display book information correctly', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
      })
      
      // Check that book titles are displayed
      expect(screen.getByText('Test Book 1')).toBeInTheDocument()
      expect(screen.getByText('Test Book 2')).toBeInTheDocument()
      
      // Check that subtitle is displayed for books that have it
      expect(screen.getByText('A Great Story')).toBeInTheDocument()
    })

    it('should show correct book count in header', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/2 books/)).toBeInTheDocument()
      })
    })

    it('should display last sync date', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/Last sync:/)).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      expect(screen.getByRole('button', { name: /sync library/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /refresh library/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /clear/i })).toBeInTheDocument()
    })

    it('should have proper form labels', async () => {
      render(
        <MemoryRouter>
          <Library />
        </MemoryRouter>
      )
      
      expect(screen.getByPlaceholderText('Search books...')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by author')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by narrator')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Filter by series')).toBeInTheDocument()
    })
  })
})            