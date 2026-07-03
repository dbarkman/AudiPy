import { http, HttpResponse } from 'msw'

// Mock data
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
}

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

const mockSyncStatus = {
  is_syncing: false,
  last_sync: '2023-12-01T10:00:00Z',
  total_books: 2,
  status_message: 'Ready to sync',
}

export const handlers = [
  // Authentication endpoints
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json()
    
    if (body.username === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        user: mockUser,
        access_token: 'mock-token',
      })
    }
    
    if (body.username === 'otp@example.com') {
      return HttpResponse.json({
        requires_otp: true,
        session_id: 'mock-session-id',
      })
    }
    
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  http.post('/api/auth/verify-otp', async ({ request }) => {
    const body = await request.json()
    
    if (body.otp_code === '123456') {
      return HttpResponse.json({
        user: mockUser,
        access_token: 'mock-token',
      })
    }
    
    return HttpResponse.json(
      { detail: 'Invalid OTP code' },
      { status: 401 }
    )
  }),

  http.get('/api/auth/me', () => {
    return HttpResponse.json({
      authenticated: true,
      user: mockUser,
    })
  }),

  http.post('/api/auth/logout', () => {
    return HttpResponse.json({ success: true })
  }),

  // Library endpoints
  http.get('/api/library', ({ request }) => {
    const url = new URL(request.url)
    const search = url.searchParams.get('search')
    const author = url.searchParams.get('author')
    const page = parseInt(url.searchParams.get('page') || '1')
    const pageSize = parseInt(url.searchParams.get('page_size') || '20')
    
    let filteredBooks = [...mockBooks]
    
    // Apply search filter
    if (search) {
      filteredBooks = filteredBooks.filter(book =>
        book.title.toLowerCase().includes(search.toLowerCase()) ||
        book.authors.some(a => a.toLowerCase().includes(search.toLowerCase()))
      )
    }
    
    // Apply author filter
    if (author) {
      filteredBooks = filteredBooks.filter(book =>
        book.authors.some(a => a.toLowerCase().includes(author.toLowerCase()))
      )
    }
    
    // Pagination
    const startIndex = (page - 1) * pageSize
    const endIndex = startIndex + pageSize
    const paginatedBooks = filteredBooks.slice(startIndex, endIndex)
    
    return HttpResponse.json({
      books: paginatedBooks,
      total_count: filteredBooks.length,
      has_next: endIndex < filteredBooks.length,
      page,
      page_size: pageSize,
    })
  }),

  http.get('/api/library/status', () => {
    return HttpResponse.json(mockSyncStatus)
  }),

  http.post('/api/library/sync', () => {
    return HttpResponse.json({ success: true })
  }),

  http.get('/api/books/:asin', ({ params }) => {
    const book = mockBooks.find(b => b.asin === params.asin)
    
    if (!book) {
      return HttpResponse.json(
        { detail: 'Book not found' },
        { status: 404 }
      )
    }
    
    return HttpResponse.json({
      ...book,
      description: 'This is a detailed description of the book.',
      genres: ['Fiction', 'Adventure'],
      publisher: 'Test Publisher',
    })
  }),

  // User profile endpoints
  http.get('/api/user/profile', () => {
    return HttpResponse.json({
      ...mockUser,
      preferences: {
        theme: 'light',
        notifications: true,
        auto_sync: false,
      },
    })
  }),

  http.put('/api/user/profile', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      ...mockUser,
      ...body,
    })
  }),

  // Health check
  http.get('/health', () => {
    return HttpResponse.json({ status: 'healthy' })
  }),
]

// Error handlers for testing error scenarios
export const errorHandlers = [
  http.get('/api/library', () => {
    return HttpResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }),

  http.post('/api/library/sync', () => {
    return HttpResponse.json(
      { detail: 'Sync failed' },
      { status: 500 }
    )
  }),

  http.post('/api/auth/login', () => {
    return HttpResponse.json(
      { detail: 'Authentication service unavailable' },
      { status: 503 }
    )
  }),
] 