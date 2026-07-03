# Audible API Data Structure

This document outlines the structure of book data returned by the Audible API. The data is returned as a JSON object with the following structure:

## Book Object Structure

```json
{
  "amazon_asin": null,
  "asin": "B07DHSQL6Q",
  "asin_trends": null,
  "asset_badges": null,
  "asset_details": null,
  "audible_editors_summary": null,
  "author_pages": null,
  "authors": [
    {
      "asin": "B019N34KS2",
      "name": "Jake Knapp"
    },
    {
      "asin": "B01ATPESEY",
      "name": "John Zeratsky"
    }
  ],
  "availability": null,
  "available_codecs": [
    {
      "enhanced_codec": "format4",
      "format": "Format4",
      "is_kindle_enhanced": false,
      "name": "format4"
    },
    {
      "enhanced_codec": "LC_32_22050_stereo",
      "format": "Enhanced",
      "is_kindle_enhanced": true,
      "name": "aax_22_32"
    }
    // ... more codec options
  ],
  "content_delivery_type": "SinglePartBook",
  "content_type": "Product",
  "format_type": "unabridged",
  "is_listenable": true,
  "issue_date": "2018-09-25",
  "language": "english",
  "library_status": {
    "date_added": "2025-05-21T05:42:18.895Z",
    "is_pending": null,
    "is_preordered": null,
    "is_removable": null,
    "is_visible": null
  },
  "merchandising_summary": "<p>Nobody ever looked at an empty calendar...</p>",
  "narrators": [
    {
      "asin": null,
      "name": "Jake Knapp"
    },
    {
      "asin": null,
      "name": "John Zeratsky"
    }
  ],
  "price": null,
  "product_images": {
    "500": "https://m.media-amazon.com/images/I/410ZBczEAqL._SL500_.jpg"
  },
  "publication_datetime": "2018-09-25T07:00:00Z",
  "publisher_name": "Random House Audio",
  "purchase_date": "2025-05-21T05:42:18.895Z",
  "release_date": "2018-09-25",
  "runtime_length_min": 298,
  "series": null,
  "status": "Active",
  "subtitle": "How to Focus on What Matters Every Day",
  "title": "Make Time"
}
```

## Key Fields

### Basic Information
- `asin`: Unique identifier for the book
- `title`: Book title
- `subtitle`: Book subtitle
- `format_type`: Book format (e.g., "unabridged")
- `language`: Book language
- `runtime_length_min`: Length in minutes

### Dates
- `issue_date`: Publication date
- `release_date`: Release date
- `purchase_date`: When the book was purchased
- `publication_datetime`: Full publication timestamp

### Contributors
- `authors`: Array of author objects with `asin` and `name`
- `narrators`: Array of narrator objects with `asin` and `name`
- `publisher_name`: Name of the publisher

### Library Status
- `library_status`: Object containing:
  - `date_added`: When the book was added to library
  - `is_pending`: Pending status
  - `is_preordered`: Preorder status
  - `is_removable`: Whether book can be removed
  - `is_visible`: Visibility status

### Media
- `available_codecs`: Array of available audio formats
- `product_images`: Object containing image URLs
- `is_listenable`: Whether the book is currently listenable

### Optional Fields
- `series`: Series information (null if not part of a series)
- `price`: Current price (null if not available)
- `merchandising_summary`: Book description in HTML format

## Notes
- Many fields can be null
- The API returns additional fields not shown here
- Some fields may vary based on the book's type and availability
- The structure may change with API updates 