# 📚 AudiPy Recommendation Processing Plan

## 🎯 **Two-Tier Recommendation Strategy**

### **Tier 1: Static Recommendations** (Database-Stored)
Populated during initial library processing and updated when library changes.

### **Tier 2: Dynamic Recommendations** (Real-Time)
Calculated on-demand when user visits the web interface.

---

## 🗄️ **Database Population Script**

### **Enhanced Library Processing Script**
```python
class AudibleLibraryProcessor:
    def process_user_library(self, user_id):
        """Complete library processing and recommendation generation"""
        
        # 1. Fetch and store user's library
        library = self.fetch_library()
        self.store_user_books(user_id, library)
        
        # 2. Analyze library patterns
        analysis = self.analyze_library(library)
        
        # 3. Generate static recommendations
        recommendations = self.generate_static_recommendations(user_id, analysis)
        self.store_recommendations(user_id, recommendations)
        
        # 4. Update user preferences
        self.update_user_preferences(user_id, analysis)
        
        return {
            'library_count': len(library),
            'recommendations_count': len(recommendations),
            'processing_complete': True
        }
    
    def generate_static_recommendations(self, user_id, analysis):
        """Generate the three core recommendation types"""
        recommendations = []
        
        # Author-based recommendations
        for author_name in analysis['authors']:
            author_books = self.search_books_by_author(author_name)
            for book in author_books:
                if not self.user_owns_book(user_id, book['asin']):
                    recommendations.append({
                        'book_asin': book['asin'],
                        'type': 'author',
                        'source': author_name,
                        'confidence': self.calculate_author_confidence(user_id, author_name),
                        'price': book.get('member_price')
                    })
        
        # Narrator-based recommendations  
        for narrator_name in analysis['narrators']:
            narrator_books = self.search_books_by_narrator(narrator_name)
            for book in narrator_books:
                if not self.user_owns_book(user_id, book['asin']):
                    recommendations.append({
                        'book_asin': book['asin'],
                        'type': 'narrator',
                        'source': narrator_name,
                        'confidence': self.calculate_narrator_confidence(user_id, narrator_name),
                        'price': book.get('member_price')
                    })
        
        # Series-based recommendations
        for series_name in analysis['series']:
            series_books = self.search_books_in_series(series_name)
            for book in series_books:
                if not self.user_owns_book(user_id, book['asin']):
                    recommendations.append({
                        'book_asin': book['asin'],
                        'type': 'series',
                        'source': series_name,
                        'confidence': 1.0,  # High confidence for series continuations
                        'price': book.get('member_price')
                    })
        
        return recommendations
    
    def store_recommendations(self, user_id, recommendations):
        """Store recommendations in database"""
        for rec in recommendations:
            # First ensure the book exists in our books table
            self.ensure_book_exists(rec['book_asin'])
            
            # Then store the recommendation
            query = """
                INSERT INTO user_recommendations 
                (user_id, book_asin, recommendation_type, recommendation_source, 
                 confidence_score, price_when_found)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                confidence_score = VALUES(confidence_score),
                price_when_found = VALUES(price_when_found),
                updated_at = CURRENT_TIMESTAMP
            """
            self.db.execute(query, (
                user_id, rec['book_asin'], rec['type'], rec['source'],
                rec['confidence'], rec['price']
            ))
```

## 🌐 **Web Interface Recommendations**

### **Static Recommendation Retrieval**
```python
class RecommendationService:
    def get_user_recommendations(self, user_id, recommendation_type=None, limit=50):
        """Get stored recommendations for user"""
        query = """
            SELECT 
                ur.book_asin,
                ur.recommendation_type,
                ur.recommendation_source,
                ur.confidence_score,
                ur.price_when_found,
                b.title,
                b.authors,
                b.narrators,
                b.cover_url,
                b.length_minutes,
                ur.created_at
            FROM user_recommendations ur
            JOIN books b ON ur.book_asin = b.asin
            WHERE ur.user_id = %s
        """
        
        params = [user_id]
        if recommendation_type:
            query += " AND ur.recommendation_type = %s"
            params.append(recommendation_type)
            
        query += """
            ORDER BY ur.confidence_score DESC, ur.created_at DESC
            LIMIT %s
        """
        params.append(limit)
        
        return self.db.fetch_all(query, params)
    
    def get_recommendations_by_category(self, user_id):
        """Get recommendations organized by category"""
        return {
            'authors': self.get_user_recommendations(user_id, 'author', 20),
            'narrators': self.get_user_recommendations(user_id, 'narrator', 20),
            'series': self.get_user_recommendations(user_id, 'series', 10)
        }
```

### **Dynamic Recommendation Generation**
```python
class DynamicRecommendations:
    def get_real_time_recommendations(self, user_id):
        """Generate real-time recommendations"""
        user_prefs = self.get_user_preferences(user_id)
        
        return {
            'on_sale': self.get_sale_books(user_prefs['marketplace']),
            'cash_deals': self.get_cash_deal_books(user_prefs['max_credit_price']),
            'favorite_genres': self.get_genre_recommendations(user_id),
            'trending': self.get_trending_books(user_prefs['marketplace']),
            'new_releases': self.get_new_releases_by_user_authors(user_id)
        }
    
    def get_sale_books(self, marketplace):
        """Get books currently on sale"""
        # Make real-time API calls to find sale books
        sale_books = self.audible_client.get_daily_deals(marketplace)
        return self.filter_and_format_books(sale_books)
    
    def get_cash_deal_books(self, max_credit_price):
        """Get books cheaper than credit price"""
        query = """
            SELECT * FROM books 
            WHERE member_price < %s 
            AND member_price IS NOT NULL
            ORDER BY member_price ASC
            LIMIT 20
        """
        return self.db.fetch_all(query, [max_credit_price])
    
    def get_genre_recommendations(self, user_id):
        """Get recommendations based on user's favorite genres"""
        # Analyze user's library to determine favorite genres
        user_genres = self.analyze_user_genres(user_id)
        
        recommendations = []
        for genre in user_genres[:3]:  # Top 3 genres
            genre_books = self.search_books_by_genre(genre['name'])
            recommendations.extend(genre_books[:10])  # 10 books per genre
            
        return recommendations
```

## 📊 **Recommendation Dashboard UI**

### **Web Interface Layout**
```html
<div class="recommendations-dashboard">
    <!-- Static Recommendations (Always Available) -->
    <section class="static-recommendations">
        <h2>📚 Based on Your Library</h2>
        
        <div class="recommendation-category">
            <h3>👨‍💼 More from Your Authors ({{author_count}} books)</h3>
            <div class="book-grid">
                <!-- Author-based recommendations -->
            </div>
        </div>
        
        <div class="recommendation-category">  
            <h3>🎙️ More from Your Narrators ({{narrator_count}} books)</h3>
            <div class="book-grid">
                <!-- Narrator-based recommendations -->
            </div>
        </div>
        
        <div class="recommendation-category">
            <h3>📖 Continue Your Series ({{series_count}} books)</h3>
            <div class="book-grid">
                <!-- Series-based recommendations -->
            </div>
        </div>
    </section>
    
    <!-- Dynamic Recommendations (Real-Time) -->
    <section class="dynamic-recommendations">
        <h2>🔥 Trending & Deals</h2>
        
        <div class="recommendation-category">
            <h3>💰 Cash Deals (Under ${{max_price}})</h3>
            <div class="book-grid">
                <!-- Cash deal books -->
            </div>
        </div>
        
        <div class="recommendation-category">
            <h3>🏷️ On Sale Today</h3>
            <div class="book-grid">
                <!-- Sale books -->
            </div>
        </div>
        
        <div class="recommendation-category">
            <h3>🎯 Your Favorite Genres</h3>
            <div class="book-grid">
                <!-- Genre-based recommendations -->
            </div>
        </div>
    </section>
</div>
```

## 🔄 **Update Strategy**

### **When to Refresh Static Recommendations**
1. **User adds new books** → Re-analyze and update recommendations
2. **Monthly maintenance** → Refresh all recommendations to catch new releases
3. **User preference changes** → Update confidence scores and filtering

### **Dynamic Recommendation Caching**
```python
# Cache dynamic recommendations for short periods
@cache(timeout=3600)  # 1 hour cache
def get_sale_books(marketplace):
    return fetch_current_sales(marketplace)

@cache(timeout=86400)  # 24 hour cache  
def get_trending_books(marketplace):
    return fetch_trending_books(marketplace)
```

## 🎯 **Benefits of This Approach**

### **Performance**
- ✅ **Fast loading** - Static recommendations pre-computed
- ✅ **Real-time accuracy** - Dynamic recommendations always current
- ✅ **Efficient queries** - Normalized database with proper indexes

### **User Experience**
- ✅ **Personalized** - Based on actual reading history
- ✅ **Diverse** - Multiple recommendation sources
- ✅ **Actionable** - Clear purchase recommendations (cash vs credit)

### **Scalability**
- ✅ **Background processing** - Heavy computation during initial setup
- ✅ **Cached dynamic data** - Reasonable API usage
- ✅ **Incremental updates** - Only update when library changes

---

**Implementation Priority**: Static recommendations first (Week 2), Dynamic recommendations second (Week 3) 