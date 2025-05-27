import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import LoginForm from '../LoginForm'
import { AuthProvider } from '../../../contexts/AuthContext'

// Mock the AuthContext
const mockAuthContext = {
  login: vi.fn(),
  isLoading: false,
  error: null,
  clearError: vi.fn(),
}

// Mock the useAuth hook
vi.mock('../../../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../../contexts/AuthContext')
  return {
    ...actual,
    useAuth: () => mockAuthContext,
  }
})

// Helper function to render LoginForm with context
const renderLoginForm = () => {
  return render(<LoginForm />)
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthContext.isLoading = false
    mockAuthContext.error = null
  })

  describe('Rendering', () => {
    it('should render all form elements', () => {
      renderLoginForm()
      
      expect(screen.getByText('Sign in to Audible')).toBeInTheDocument()
      expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/marketplace/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should render description text', () => {
      renderLoginForm()
      
      expect(screen.getByText(/enter your audible credentials/i)).toBeInTheDocument()
      expect(screen.getByText(/we securely connect to your audible account/i)).toBeInTheDocument()
    })

    it('should have default marketplace selected', () => {
      renderLoginForm()
      
      expect(screen.getByText('United States')).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should show validation errors for empty fields', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Email or username is required')).toBeInTheDocument()
      expect(screen.getByText('Password is required')).toBeInTheDocument()
      expect(mockAuthContext.login).not.toHaveBeenCalled()
    })

    it('should clear validation errors when user starts typing', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      // Trigger validation errors
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Email or username is required')).toBeInTheDocument()
      
      // Start typing in username field
      const usernameField = screen.getByLabelText(/email or username/i)
      await user.type(usernameField, 'test')
      
      expect(screen.queryByText('Email or username is required')).not.toBeInTheDocument()
    })

    it('should validate only username field when password is provided', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      // Fill password but leave username empty
      const passwordField = screen.getByLabelText(/^password$/i)
      await user.type(passwordField, 'password123')
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)
      
      expect(screen.getByText('Email or username is required')).toBeInTheDocument()
      expect(screen.queryByText('Password is required')).not.toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('should toggle password visibility', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      const passwordField = screen.getByLabelText(/^password$/i)
      const toggleButton = screen.getByLabelText(/toggle password visibility/i)
      
      // Initially password should be hidden
      expect(passwordField).toHaveAttribute('type', 'password')
      
      // Click toggle to show password
      await user.click(toggleButton)
      expect(passwordField).toHaveAttribute('type', 'text')
      
      // Click toggle to hide password again
      await user.click(toggleButton)
      expect(passwordField).toHaveAttribute('type', 'password')
    })

    it('should update form fields when user types', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      const usernameField = screen.getByLabelText(/email or username/i)
      const passwordField = screen.getByLabelText(/^password$/i)
      
      await user.type(usernameField, 'test@example.com')
      await user.type(passwordField, 'password123')
      
      expect(usernameField).toHaveValue('test@example.com')
      expect(passwordField).toHaveValue('password123')
    })

    it('should change marketplace selection', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      const marketplaceSelect = screen.getByRole('combobox', { name: /marketplace/i })
      await user.click(marketplaceSelect)
      
      const ukOption = screen.getByText('United Kingdom')
      await user.click(ukOption)
      
      expect(screen.getByText('United Kingdom')).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('should call login with correct data when form is valid', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      // Fill form with valid data
      await user.type(screen.getByLabelText(/email or username/i), 'test@example.com')
      await user.type(screen.getByLabelText(/^password$/i), 'password123')
      
      // Change marketplace
      await user.click(screen.getByRole('combobox', { name: /marketplace/i }))
      await user.click(screen.getByText('United Kingdom'))
      
      // Submit form
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      expect(mockAuthContext.login).toHaveBeenCalledWith({
        username: 'test@example.com',
        password: 'password123',
        marketplace: 'uk',
      })
    })

    it('should prevent form submission when validation fails', async () => {
      const user = userEvent.setup()
      renderLoginForm()
      
      // Submit empty form
      await user.click(screen.getByRole('button', { name: /sign in/i }))
      
      expect(mockAuthContext.login).not.toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('should disable form fields when loading', () => {
      mockAuthContext.isLoading = true
      renderLoginForm()
      
      expect(screen.getByLabelText(/email or username/i)).toBeDisabled()
      expect(screen.getByLabelText(/^password$/i)).toBeDisabled()
      expect(screen.getByRole('combobox', { name: /marketplace/i })).toHaveAttribute('aria-disabled', 'true')
      expect(screen.getByLabelText(/toggle password visibility/i)).toBeDisabled()
    })

    it('should show loading spinner in submit button', () => {
      mockAuthContext.isLoading = true
      renderLoginForm()
      
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled()
    })
  })

  describe('Error Handling', () => {
    it('should display error message when present', () => {
      mockAuthContext.error = 'Invalid credentials'
      renderLoginForm()
      
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })

    it('should clear error when user makes changes', async () => {
      const user = userEvent.setup()
      mockAuthContext.error = 'Invalid credentials'
      renderLoginForm()
      
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      
      // Type in username field
      await user.type(screen.getByLabelText(/email or username/i), 'test')
      
      expect(mockAuthContext.clearError).toHaveBeenCalled()
    })

    it('should clear error when close button is clicked', async () => {
      const user = userEvent.setup()
      mockAuthContext.error = 'Invalid credentials'
      renderLoginForm()
      
      const closeButton = screen.getByLabelText(/close/i)
      await user.click(closeButton)
      
      expect(mockAuthContext.clearError).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper form labels and structure', () => {
      renderLoginForm()
      
      expect(screen.getByRole('textbox', { name: /email or username/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
      expect(screen.getByRole('combobox', { name: /marketplace/i })).toBeInTheDocument()
    })

    it('should have proper button accessibility', () => {
      renderLoginForm()
      
      const toggleButton = screen.getByLabelText(/toggle password visibility/i)
      expect(toggleButton).toHaveAttribute('aria-label', 'toggle password visibility')
    })
  })
}) 