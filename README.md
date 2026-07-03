# AudiPy - Audible Library Analyzer & Discovery Platform

A comprehensive Python tool that analyzes your Audible library and helps you discover new books based on your existing collection. It organizes your books by series, authors, and narrators, and intelligently suggests new books you should buy next - with smart purchase recommendations (cash vs credits).

## 🎯 Project Vision

AudiPy aims to become the ultimate audiobook discovery and library management platform, starting as a Python CLI tool and evolving into a full-featured web application with advanced analytics, social features, and AI-powered recommendations.

## ✅ Features Implemented (POC Complete)

### Core Library Analysis
- **Complete library import** from Audible (696+ books supported)
- **Smart organization** by series, authors, and narrators
- **Series progression tracking** with book positioning
- **Language filtering** (English by default, configurable)
- **Duplicate detection** using both ASIN and title matching

### Intelligent Suggestions
- **Missing books in your series** (highest priority - continue what you've started!)
- **More books by your favorite authors** (second priority)
- **Discovery through narrators** (find new authors/series via trusted narrators)
- **Price-aware recommendations** with cash vs credit logic
- **Purchase optimization** (never pay more than $12.66 cash when you could use a credit)

### Reports & Analytics
- **6 comprehensive text reports** for easy scanning:
  - `my_library_by_authors.txt` - Your books organized by author
  - `my_library_by_narrators.txt` - Your books organized by narrator
  - `my_library_by_series.txt` - Your books organized by series (with positions)
  - `missing_books_in_my_series.txt` - **MOST IMPORTANT** - Series continuations
  - `missing_books_by_my_authors.txt` - **2ND MOST IMPORTANT** - More by favorite authors
  - `missing_books_by_my_narrators.txt` - **DISCOVERY** - New content via trusted narrators

### Smart Purchase Logic
- **💰 Cash recommendations** for books under $12.66 (save your credits!)
- **🎫 Credit recommendations** for books $12.66+ (better value than cash)
- **Price tracking** with member price display
- **Economic optimization** built into every suggestion

## 🚀 Features Planned (Next Phase)

### Database & Web Interface
- **MySQL/MariaDB backend** for robust data storage
- **React frontend** with modern, responsive design
- **User authentication** and personal profiles
- **Real-time library syncing** with background job processing

### Enhanced Analytics
- **Reading statistics dashboard** (hours listened, completion rates, etc.)
- **Spending analysis** (track Audible expenses over time)
- **Genre breakdown** and preference mapping
- **Author/narrator loyalty metrics**
- **Series completion tracking** with visual progress bars

### Advanced Discovery Features
- **Mood-based recommendations** ("I want something light/thrilling/educational")
- **Reading time estimation** based on your pace
- **Similar books engine** using content analysis
- **Trending books** within your preference categories
- **Price drop alerts** for wishlist items

### Social & Community Features
- **Friend connections** and reading activity sharing
- **Book clubs** and reading groups
- **Collaborative wishlists** and recommendations
- **Reading challenges** and goal tracking
- **Community reviews** and ratings
- **Gift recommendations** based on friends' libraries

### Personalization & AI
- **Custom reading lists** (themes, moods, commute length)
- **Smart categorization** using AI to tag books by themes
- **Personalized dashboard** with drag-and-drop widgets
- **Reading schedule optimization**
- **AI-powered book summaries** and content analysis

### Mobile & Integrations
- **Progressive Web App** for mobile access
- **Goodreads sync** for ratings and reviews
- **Library system integration** (check local availability)
- **Calendar integration** for reading time blocking
- **Voice commands** for hands-free list management

### Advanced Features (Future)
- **Barcode scanning** for physical book tracking
- **Offline mode** for browsing without internet
- **Data export tools** for backup and portability
- **API for third-party integrations**
- **Multi-language support** for international users

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- An Audible account with valid credentials
- pip (Python package installer)

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/audipy.git
cd audipy
```

2. **Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure your credentials:**
```bash
cp .env.example .env
# Edit .env with your Audible credentials
```

## ⚙️ Configuration

Create a `.env` file with these settings:

```env
# Audible credentials (required)
AUDIBLE_USERNAME=your_audible_email@example.com
AUDIBLE_PASSWORD=your_audible_password
AUDIBLE_MARKETPLACE=us

# Purchase optimization (recommended: 12.66)
MAX_PRICE=12.66

# Content filtering
LANGUAGE=english
```

### Configuration Explained:
- **MAX_PRICE**: Price threshold for cash vs credit recommendations (default: $12.66 = cost of 1 credit when buying 3 credits at once)
- **LANGUAGE**: Filter suggestions to specific language (prevents foreign language recommendations)
- **MARKETPLACE**: Your Audible marketplace region (us, uk, de, fr, etc.)

## 🚀 Usage

1. **Activate your virtual environment:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Run the analyzer:**
```bash
python audipy.py
```

3. **Follow the prompts:**
   - Enter your OTP code when requested
   - Wait for library analysis (696 books takes ~2-3 minutes)
   - Review generated reports in the `reports/` directory

## 📊 Output Reports

The tool generates 6 focused text reports in the `reports/` directory:

### Your Library (Reference)
- **`my_library_by_authors.txt`** - All your books organized by author
- **`my_library_by_narrators.txt`** - All your books organized by narrator
- **`my_library_by_series.txt`** - All your books organized by series (with book numbers)

### Shopping Lists (Action Items)
- **`missing_books_in_my_series.txt`** - 🔥 **PRIORITY 1** - Continue series you've started
- **`missing_books_by_my_authors.txt`** - 🔥 **PRIORITY 2** - More books by favorite authors  
- **`missing_books_by_my_narrators.txt`** - 🔍 **DISCOVERY** - Find new content via trusted narrators

### Sample Output Format:
```
Craig Alanson:
- Ascendant (Expeditionary Force #12) - $9.65 (💰 cash)
- Deceptions (Expeditionary Force #8) - $11.23 (💰 cash)
- Mavericks - $15.74 (🎫 credits)
```

## 🎯 Purchase Recommendations

The tool optimizes your spending with smart purchase logic:

- **💰 Cash purchases** (< $12.66): Better to pay cash and save credits for expensive books
- **🎫 Credit purchases** (≥ $12.66): Use credits instead of overpaying with cash
- **Economic principle**: Never pay more than $12.66 cash when you could use a credit

## 🔒 Security

- **Never commit `.env` files** to version control
- **Credentials stored locally** only in your `.env` file
- **No data transmission** to third-party servers
- **Audible official API** used for all data access

## 🤝 Contributing

We welcome contributions! Areas where help is needed:
- Database schema design for the web version
- React component development
- API optimization and rate limiting
- Machine learning for book recommendations
- Mobile app development

## 📈 Project Roadmap

### Phase 1: CLI Tool ✅ **COMPLETE**
- Core library analysis
- Text-based reports
- Purchase optimization

### Phase 2: Web Platform 🚧 **IN PROGRESS**
- Database integration (MySQL/MariaDB)
- React frontend development
- User authentication system

### Phase 3: Advanced Features 📋 **PLANNED**
- Social features and book clubs
- AI-powered recommendations
- Mobile progressive web app

### Phase 4: Ecosystem 🔮 **FUTURE**
- API for third-party developers
- Mobile native apps
- Publishing partnerships

## 📝 License

MIT License - feel free to use, modify, and distribute!

## 🎉 Acknowledgments

- **Audible Python Library** for API access
- **Rich Console** for beautiful terminal output
- **The audiobook community** for inspiration and feedback

---

*Happy listening! 📚🎧* 