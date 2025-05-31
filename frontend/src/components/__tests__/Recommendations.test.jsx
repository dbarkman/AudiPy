import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Recommendations from '../Recommendations'
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
const mockRecommendations = [
  {
    asin: 'B001',
    title: 'Recommended Book 1',
    subtitle: 'A Great Recommendation',
    authors: ['Author One'],
    narrators: ['Narrator One'],
    series: 'Test Series',
    runtime_length_min: 480,
    language: 'English',
    recommendation_type: 'author',
    source_name: 'Author One',
    confidence_score: 0.85,
    purchase_method: 'credits',
    generated_at: '2023-12-01T10:00:00Z'
  },
  {
    asin: 'B002',
    title: 'Recommended Book 2',
    subtitle: null,
    authors: ['Author Two'],
    narrators: ['Narrator Two'],
    series: null,
    runtime_length_min: 360,
    language: 'English',
    recommendation_type: 'narrator',
    source_name: 'Narrator Two',
    confidence_score: 0.75,
    purchase_method: 'cash',
    generated_at: '2023-12-01T11:00:00Z'
  }
]

const mockGenerationStatus = {
  is_generating: false,
  last_generated: '2023-12-01T10:00:00Z',
  total_recommendations: 2,
  status_message: 'Recommendations generated successfully'
}

describe('Recommendations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Default API responses
    api.get.mockImplementation((url) => {
      if (url === '/recommendations') {
        return Promise.resolve({
          data: {
            recommendations: mockRecommendations,
            total_count: 2,
            page: 1,
            page_size: 12,
            has_next: false
          }
        })
      }
      if (url === '/recommendations/status') {
        return Promise.resolve({
          data: mockGenerationStatus
        })
      }
      return Promise.reject(new Error('Unknown endpoint'))
    })
    
    api.post.mockImplementation((url) => {
      if (url === '/recommendations/generate') {
        return Promise.resolve({
          data: { success: true, message: 'Generation started' }
        })
      }
      return Promise.reject(new Error('Unknown endpoint'))
    })
  })

  describe('Rendering', () => {
    it('should render recommendations page header', async () => {
      render(<Recommendations />)
      
      expect(screen.getByText('Recommendations')).toBeInTheDocument()
      expect(screen.getByText('Personalized book recommendations based on your library')).toBeInTheDocument()
    })

    it('should render control buttons', async () => {
      render(<Recommendations />)
      
      expect(screen.getByText('Generate New Recommendations')).toBeInTheDocument()
      expect(screen.getByText('Refresh')).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('should render recommendations after loading', async () => {
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('2 Recommendations Found')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Recommended Book 1')).toBeInTheDocument()
      expect(screen.getByText('Recommended Book 2')).toBeInTheDocument()
    })
  })

  describe('Generation Status', () => {
    it('should show generation status when available', async () => {
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('2 recommendations available')).toBeInTheDocument()
      })
    })

    it('should show generating state when generation is in progress', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/recommendations') {
          return Promise.resolve({
            data: {
              recommendations: [],
              total_count: 0,
              page: 1,
              page_size: 12,
              has_next: false
            }
          })
        }
        if (url === '/recommendations/status') {
          return Promise.resolve({
            data: {
              ...mockGenerationStatus,
              is_generating: true,
              status_message: 'Generating recommendations...'
            }
          })
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('Generating recommendations...')).toBeInTheDocument()
      })
    })
  })

  describe('User Interactions', () => {
    it('should trigger generation when generate button is clicked', async () => {
      const user = userEvent.setup()
      render(<Recommendations />)
      
      const generateButton = screen.getByText('Generate New Recommendations')
      await user.click(generateButton)
      
      expect(api.post).toHaveBeenCalledWith('/recommendations/generate')
    })

    it('should refresh recommendations when refresh button is clicked', async () => {
      const user = userEvent.setup()
      render(<Recommendations />)
      
      // Wait for initial load
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/recommendations', expect.any(Object))
      })
      
      vi.clearAllMocks()
      
      const refreshButton = screen.getByText('Refresh')
      await user.click(refreshButton)
      
      expect(api.get).toHaveBeenCalledWith('/recommendations', expect.any(Object))
    })

    it('should filter recommendations by type', async () => {
      const user = userEvent.setup()
      render(<Recommendations />)
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('2 Recommendations Found')).toBeInTheDocument()
      })
      
      vi.clearAllMocks()
      
      const filterSelect = screen.getByRole('combobox')
      await user.click(filterSelect)
      
      const authorOption = screen.getByText('Author')
      await user.click(authorOption)
      
      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith('/recommendations', 
          expect.objectContaining({
            params: expect.objectContaining({
              recommendation_type: 'author'
            })
          })
        )
      })
    })
  })

  describe('Recommendation Display', () => {
    it('should display recommendation details correctly', async () => {
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('Recommended Book 1')).toBeInTheDocument()
      })
      
      // Check book details - just verify key content exists
      expect(screen.getByText('A Great Recommendation')).toBeInTheDocument()
      expect(screen.getByText('Narrator One')).toBeInTheDocument()
      expect(screen.getByText('Test Series')).toBeInTheDocument()
      expect(screen.getByText('8h 0m')).toBeInTheDocument()
      
      // Check recommendation metadata
      expect(screen.getByText('author')).toBeInTheDocument()
      expect(screen.getByText('85% match')).toBeInTheDocument()
      expect(screen.getByText('credits')).toBeInTheDocument()
    })

    it('should handle books without optional fields', async () => {
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('Recommended Book 2')).toBeInTheDocument()
      })
      
      // Should not show subtitle or series for book 2
      expect(screen.queryByText('null')).not.toBeInTheDocument()
    })
  })

  describe('Empty States', () => {
    it('should show empty state when no recommendations exist', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/recommendations') {
          return Promise.resolve({
            data: {
              recommendations: [],
              total_count: 0,
              page: 1,
              page_size: 12,
              has_next: false
            }
          })
        }
        if (url === '/recommendations/status') {
          return Promise.resolve({
            data: {
              ...mockGenerationStatus,
              total_recommendations: 0
            }
          })
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('No Recommendations Yet')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Generate personalized recommendations based on your library')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should display error when recommendations fetch fails', async () => {
      api.get.mockImplementation((url) => {
        if (url === '/recommendations') {
          return Promise.reject(new Error('Network error'))
        }
        if (url === '/recommendations/status') {
          return Promise.resolve({ data: mockGenerationStatus })
        }
        return Promise.reject(new Error('Unknown endpoint'))
      })
      
      render(<Recommendations />)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load recommendations. Please try again.')).toBeInTheDocument()
      })
    })

    it('should display error when generation fails', async () => {
      api.post.mockImplementation(() => {
        return Promise.reject(new Error('Generation failed'))
      })
      
      const user = userEvent.setup()
      render(<Recommendations />)
      
      const generateButton = screen.getByText('Generate New Recommendations')
      await user.click(generateButton)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to start recommendation generation. Please try again.')).toBeInTheDocument()
      })
    })
  })
}) 