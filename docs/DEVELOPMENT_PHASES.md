# AudiPy Web Application Development Phases

## 🎯 **Project Overview**

Transform the existing CLI-based AudiPy tool into a modern, mobile-first web application using React frontend and FastAPI backend.

## 📱 **Design Principles**

- **Mobile-First**: Optimized for phone screens, then desktop
- **Community Standards**: Use widely-adopted libraries and patterns
- **Maintainable**: Easy for new developers to understand and contribute
- **Respectful**: Support Audible/Amazon by linking to their store

## 🚀 **Development Phases**

### **Phase 1: Foundation & Authentication (Weeks 1-2)**
**Goal:** Get users logged in and authenticated with Audible

#### **Frontend Tasks:**
- ✅ React app setup with Vite + Material-UI
- ✅ Mobile-first responsive design foundation
- ✅ Basic landing page with navigation
- 🔄 Authentication flow components:
  - Login form (username, password, marketplace)
  - OTP input dialog
  - Loading states and error handling
  - Success confirmation
- 🔄 Token management and API integration
- 🔄 Protected routes setup

#### **Backend Tasks:**
- 🔄 FastAPI setup and configuration
- 🔄 CORS configuration for React frontend
- 🔄 Authentication endpoints:
  - `POST /api/auth/login` (wraps phase1_authenticate.py logic)
  - `POST /api/auth/verify-otp` (handle 2FA)
  - `GET /api/auth/test` (test API access)
  - `POST /api/auth/logout`
- 🔄 JWT token management
- 🔄 Error handling and validation

#### **Integration:**
- 🔄 Connect React auth forms to FastAPI endpoints
- 🔄 Handle authentication flow states
- 🔄 Store tokens securely (httpOnly cookies)

---

### **Phase 2: User Profile & Preferences (Week 3)**
**Goal:** Let users configure their preferences

#### **Frontend Tasks:**
- User profile dashboard page
- Preferences form with Material-UI components:
  - Language selection dropdown
  - Marketplace selection
  - Price threshold sliders
  - Notification preferences
- Settings management interface
- Account status display
- Mobile-optimized forms

#### **Backend Tasks:**
- User preferences endpoints:
  - `GET /api/user/profile`
  - `PUT /api/user/preferences`
  - `GET /api/user/status`
- Wrap phase2_user_profile.py logic
- Database integration for user settings

#### **Integration:**
- Form validation and submission
- Real-time preference updates
- Success/error feedback

---

### **Phase 3: Library Display & Management (Weeks 4-5)**
**Goal:** Show user's Audible library with search/filter capabilities

#### **Frontend Tasks:**
- Library grid/list view (mobile-optimized)
- Book card components with:
  - Cover images
  - Title, author, narrator
  - Duration, publication date
  - Purchase date
- Search and filtering interface:
  - Text search
  - Filter by author, narrator, series
  - Sort options (date, title, duration)
- Book details modal/page
- Library sync controls and status
- Infinite scroll/pagination for large libraries

#### **Backend Tasks:**
- Library endpoints:
  - `GET /api/library` (paginated, searchable)
  - `POST /api/library/sync` (trigger phase3_fetch_library.py)
  - `GET /api/library/status` (sync progress)
  - `GET /api/books/{book_id}` (book details)
- Search and filtering logic
- Pagination implementation
- Background sync job management

#### **Integration:**
- Real-time sync progress updates
- Responsive book grid layout
- Search debouncing and optimization

---

### **Phase 4: Recommendations Engine (Weeks 6-7)**
**Goal:** Display personalized recommendations

#### **Frontend Tasks:**
- Recommendations dashboard
- Recommendation cards with:
  - Book details
  - Recommendation reason (author, narrator, series)
  - Confidence score display
  - Purchase links to Audible
- Filtering by recommendation type:
  - By favorite authors
  - By favorite narrators
  - By series continuation
- Wishlist/favorites functionality
- Price tracking and deal alerts

#### **Backend Tasks:**
- Recommendations endpoints:
  - `GET /api/recommendations` (paginated, filtered)
  - `POST /api/recommendations/generate` (trigger phase4)
  - `GET /api/recommendations/status`
  - `POST /api/recommendations/favorite`
- Wrap phase4_generate_recommendations.py logic
- Recommendation filtering and sorting
- Deal detection and pricing

#### **Integration:**
- Recommendation generation triggers
- Real-time updates during processing
- Audible store link integration

---

### **Phase 5: Advanced Features (Weeks 8+)**
**Goal:** Enhanced user experience and analytics

#### **Frontend Tasks:**
- Advanced analytics dashboard:
  - Reading statistics
  - Genre preferences
  - Author/narrator analytics
  - Spending insights
- Recommendation tuning interface:
  - Adjust recommendation weights
  - Exclude authors/narrators
  - Set genre preferences
- Export/sharing features:
  - Export library data
  - Share favorite books
  - Generate reading reports
- Performance optimizations:
  - Code splitting
  - Image lazy loading
  - Caching strategies

#### **Backend Tasks:**
- Analytics endpoints:
  - `GET /api/analytics/reading-stats`
  - `GET /api/analytics/spending`
  - `GET /api/analytics/preferences`
- Advanced recommendation tuning
- Export functionality
- Performance optimizations:
  - Database indexing
  - Caching layer
  - Background job optimization

#### **Integration:**
- Interactive charts and graphs
- Real-time analytics updates
- Smooth user experience optimizations

---

## 🛠️ **Technical Stack**

### **Frontend:**
- **Framework:** React 18 with Vite
- **UI Library:** Material-UI (MUI)
- **Routing:** React Router
- **HTTP Client:** Axios
- **State Management:** React Context + useReducer
- **Styling:** MUI's sx prop + custom theme

### **Backend:**
- **Framework:** FastAPI
- **Database:** MySQL (existing)
- **Authentication:** JWT tokens in httpOnly cookies
- **Background Jobs:** Celery (for long-running tasks)
- **API Documentation:** Auto-generated with FastAPI

### **Deployment:**
- **Frontend:** Static files served by Apache
- **Backend:** FastAPI as systemd service
- **Database:** Existing MySQL setup
- **Server:** Rocky Linux 9 with Apache

---

## 📱 **Mobile-First Responsive Design**

### **Breakpoints:**
```css
- xs: 320px (small phones)
- sm: 375px (standard phones) 
- md: 768px (tablets)
- lg: 1024px (desktop)
- xl: 1440px (large desktop)
```

### **Navigation Pattern:**
- **Desktop:** Top navigation bar with menu items
- **Mobile:** Hamburger menu that slides in from left
- **Consistent:** Material-UI AppBar + Drawer components

### **Key Mobile Considerations:**
- Touch-friendly buttons (44px minimum)
- Thumb-zone navigation (bottom of screen for key actions)
- Swipe gestures for book browsing
- Progressive loading for large libraries
- Optimized images and lazy loading

---

## 🔄 **Data Flow & Integration**

### **Authentication Flow:**
1. User enters Audible credentials
2. React → FastAPI → Existing auth logic
3. Handle OTP if required
4. Store JWT tokens securely
5. Redirect to dashboard

### **Library Sync Flow:**
1. User triggers sync
2. FastAPI starts background job
3. Real-time progress updates via WebSocket/polling
4. Update UI when complete

### **Recommendation Flow:**
1. User requests recommendations
2. FastAPI triggers recommendation engine
3. Background processing with progress updates
4. Display results with filtering options

---

## 🚦 **Success Criteria**

### **Phase 1:**
- [ ] User can log in with Audible credentials
- [ ] OTP authentication works
- [ ] Mobile-responsive navigation
- [ ] Secure token storage

### **Phase 2:**
- [ ] User can set preferences
- [ ] Settings persist across sessions
- [ ] Mobile-friendly forms

### **Phase 3:**
- [ ] Library displays correctly on mobile/desktop
- [ ] Search and filtering work smoothly
- [ ] Sync process is user-friendly

### **Phase 4:**
- [ ] Recommendations display with clear reasoning
- [ ] Filtering and sorting work
- [ ] Audible links are properly formatted

### **Phase 5:**
- [ ] Analytics provide valuable insights
- [ ] Performance is optimized
- [ ] User experience is polished

---

## 🎯 **Next Steps**

1. **Complete Phase 1 setup** (FastAPI + authentication)
2. **Deploy to test server** for real-world testing
3. **Iterate based on feedback** from each phase
4. **Maintain focus on mobile-first** design throughout

---

## 📞 **Support & Maintenance**

- **Community Standards:** All choices favor widely-adopted solutions
- **Documentation:** Comprehensive docs for new developers
- **Testing:** Maintain test coverage throughout development
- **Performance:** Monitor and optimize at each phase 