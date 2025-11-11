# 🔍 Card Search Feature - Complete Implementation

## Overview

The Card Search feature is a production-ready, advanced search interface that allows users to find Magic: The Gathering cards using multiple criteria simultaneously. It integrates with the Scryfall API to provide comprehensive card information with beautiful card image displays.

---

## ✨ Features

### Advanced Search Filters

The Card Search supports 9 different search criteria:

1. **Colors** - Filter by color identity (w/u/b/r/g/c)
2. **Mana Value** - Search by converted mana cost (exact or with comparisons)
3. **Card Type** - Filter by card type (Creature, Instant, Sorcery, etc.)
4. **Format** - Find cards legal in specific formats (Standard, Modern, Commander, etc.)
5. **Power/Toughness** - Search creatures by power and toughness values
6. **Rarity** - Filter by card rarity (Common, Uncommon, Rare, Mythic)
7. **Keywords** - Search for specific keywords (flying, haste, trample, etc.)
8. **Oracle Text** - Full-text search within card text
9. **Combinations** - Use multiple filters simultaneously for precision

### Professional UI Design

- **Three-Mode Interface**: Seamlessly switch between Chat, Card Search, and Deck Validator
- **Glassmorphic Design**: Modern, professional UI with backdrop blur effects
- **Responsive Layout**: Optimized for desktop, tablet, and mobile
- **Grid-Based Form**: Clean, organized search filters in a responsive grid
- **Beautiful Card Display**: Full card images with zoom effect on hover
- **Color-Coded Rarity**: Visual rarity indicators (Common, Uncommon, Rare, Mythic)
- **Smooth Animations**: Professional transitions and hover effects throughout

### Smart Search Results

- **Card Images**: Full-resolution card images from Scryfall
- **Detailed Information**: Card name, mana cost, type, oracle text, P/T
- **Set Information**: Display set name and collector number
- **Direct Links**: "View on Scryfall" links for more details
- **Result Count**: Shows total matches and displays top 20 results
- **Empty States**: Helpful messages when no results are found
- **Error Handling**: Clear error messages with suggestions

---

## 🏗️ Technical Implementation

### Backend API Endpoint

**Endpoint**: `POST /search-cards`

**Request Body** (`CardSearchRequest`):
```json
{
  "colors": "string (optional)",
  "mana_value": "string (optional)",
  "mana_cost": "string (optional)",
  "power": "string (optional)",
  "toughness": "string (optional)",
  "format_legal": "string (optional)",
  "card_type": "string (optional)",
  "keywords": "string (optional)",
  "text": "string (optional)",
  "rarity": "string (optional)"
}
```

**Response** (`CardSearchResponse`):
```json
{
  "total_cards": "integer",
  "query": "string (Scryfall query syntax)",
  "cards": [
    {
      "name": "string",
      "mana_cost": "string",
      "type_line": "string",
      "oracle_text": "string",
      "power": "string (nullable)",
      "toughness": "string (nullable)",
      "image_url": "string (URL)",
      "scryfall_url": "string (URL)",
      "rarity": "string",
      "set_name": "string",
      "collector_number": "string"
    }
  ],
  "success": "boolean"
}
```

### Search Query Builder

The backend constructs Scryfall search syntax automatically:

| Filter | Scryfall Syntax | Example |
|--------|----------------|---------|
| Colors | `c:` | `c:ur` (blue/red) |
| Mana Value | `mv=` or `mv<`/`mv>` | `mv=3`, `mv<=2` |
| Mana Cost | `m:` | `m:{R}{R}{R}` |
| Power | `pow=` or `pow<`/`pow>` | `pow=3`, `pow>=5` |
| Toughness | `tou=` or `tou<`/`tou>` | `tou=3`, `tou>=5` |
| Format | `f:` | `f:standard` |
| Card Type | `t:` | `t:creature` |
| Keywords | `o:` | `o:flying` |
| Oracle Text | `o:""` | `o:"draw a card"` |
| Rarity | `r:` | `r:rare` |

### Format Legality Validation

The backend **validates** format legality:
- Filters out cards not actually legal in the specified format
- Double-checks legalities even if Scryfall returns them
- Ensures only truly legal cards are displayed

### Intelligent Ordering

Results are sorted intelligently:
- **Competitive formats** (Standard, Modern, Pioneer): Sorted by release date (newest first)
- **Casual formats** (Commander, etc.): Sorted by EDHREC popularity
- **Other searches**: Default Scryfall ordering

---

## 🎨 Frontend Architecture

### Component Structure

```
App.jsx
├── Mode State (chat, search, deck)
├── Card Search State (9 filter variables)
├── Card Search UI
│   ├── Header with icon and title
│   ├── Search Form
│   │   ├── Search Grid (8 filters)
│   │   ├── Oracle Text (full width)
│   │   └── Action Buttons (Search, Clear)
│   └── Search Results
│       ├── Results Header
│       ├── Cards Grid
│       │   └── Card Result Components
│       ├── No Results State
│       └── Error State
```

### State Management

The Card Search uses React hooks for state management:

```javascript
// 9 search filter states
const [searchColors, setSearchColors] = useState('')
const [searchManaValue, setSearchManaValue] = useState('')
const [searchPower, setSearchPower] = useState('')
const [searchToughness, setSearchToughness] = useState('')
const [searchFormat, setSearchFormat] = useState('')
const [searchCardType, setSearchCardType] = useState('')
const [searchKeywords, setSearchKeywords] = useState('')
const [searchText, setSearchText] = useState('')
const [searchRarity, setSearchRarity] = useState('')

// Search operation states
const [isSearching, setIsSearching] = useState(false)
const [searchResults, setSearchResults] = useState(null)
```

### Form Validation

The search button is disabled when:
- No search criteria are provided
- A search is already in progress
- API is offline

```javascript
disabled={isSearching || apiStatus === 'offline' || 
         !(searchColors || searchManaValue || searchPower || ...)}
```

---

## 💅 CSS Styling

### Design System

The Card Search follows the Stack Sage design system:

**Colors:**
- Primary accent: `#4a9eff` (blue)
- Secondary accent: `#a78bfa` (purple)
- Success: `#10b981` (green)
- Warning: `#f59e0b` (orange)
- Error: `#ef4444` (red)

**Animations:**
- Smooth cubic-bezier transitions: `cubic-bezier(0.4, 0, 0.2, 1)`
- Hover lift effect: `translateY(-4px)`
- Image zoom: `scale(1.05)`
- Fade-in animations for results

**Responsive Breakpoints:**
- Desktop: Default (1200px max-width)
- Tablet: `@media (max-width: 768px)`
- Mobile: `@media (max-width: 480px)`

### Card Display Styling

Cards feature:
- **Card Images**: 63:88 aspect ratio (standard MTG card ratio)
- **Hover Effects**: Lift and zoom animations
- **Rarity Colors**: 
  - Common: Gray
  - Uncommon: Silver
  - Rare: Gold
  - Mythic: Red
- **Metadata**: Set name and collector number badges
- **Truncated Text**: Oracle text limited to 4 lines with ellipsis

---

## 📖 Usage Examples

### Example 1: Find Red 3-Drops in Standard

**Filters:**
- Colors: `r`
- Mana Value: `3`
- Format: `standard`
- Card Type: `creature`

**Scryfall Query:** `c:r mv=3 f:standard t:creature`

**Result:** Shows all red 3-mana-value creatures legal in Standard

---

### Example 2: Find Blue Counterspells in Modern

**Filters:**
- Colors: `u`
- Format: `modern`
- Oracle Text: `counter target spell`

**Scryfall Query:** `c:u f:modern o:"counter target spell"`

**Result:** Shows all blue counterspell effects legal in Modern

---

### Example 3: Find 5+ Power Creatures Costing 4 or Less

**Filters:**
- Power: `>=5`
- Mana Value: `<=4`
- Card Type: `creature`

**Scryfall Query:** `pow>=5 mv<=4 t:creature`

**Result:** Shows efficient high-power creatures

---

### Example 4: Find Commander Staples with "Draw" Effects

**Filters:**
- Format: `commander`
- Keywords: `draw`

**Scryfall Query:** `f:commander o:draw`

**Result:** Shows card draw spells legal in Commander

---

## 🚀 API Integration

### Scryfall API Calls

The implementation makes efficient API calls:

1. **Single Request**: One API call per search
2. **Pagination**: Retrieves first 20 results
3. **Timeout**: 10-second timeout for reliability
4. **Error Handling**: Graceful degradation on API failures
5. **Rate Limiting**: Respects Scryfall's rate limits

### Response Processing

The backend:
1. Receives Scryfall's raw response
2. Validates format legality (if specified)
3. Filters out non-legal cards
4. Formats card data for frontend consumption
5. Limits results to 20 cards
6. Returns structured response with total count

---

## 🎯 User Experience Features

### Loading States

- **Search Button**: Shows spinner and "Searching..." text
- **Disabled Inputs**: All inputs disabled during search
- **Visual Feedback**: Button animation indicates progress

### Empty States

- **No Results**: Friendly "No cards found" message
- **Helpful Hints**: Suggestions to adjust search criteria
- **Search Icon**: Large magnifying glass emoji for visual clarity

### Error States

- **Error Messages**: Clear, actionable error descriptions
- **API Errors**: Specific messages for connection issues
- **Validation Errors**: Frontend validation before API call

### Result Display

- **Total Count**: "Found X cards" header
- **Query Display**: Shows Scryfall query used
- **Pagination Note**: Indicates when more results exist
- **Direct Links**: External links to Scryfall for more info

---

## 🔧 Maintenance & Extensibility

### Adding New Search Filters

To add a new search filter:

1. **Backend** (`server.py`):
   ```python
   # Add to CardSearchRequest model
   new_filter: Optional[str] = None
   
   # Add to query builder
   if request.new_filter:
       query_parts.append(f"syntax:{request.new_filter}")
   ```

2. **Frontend** (`App.jsx`):
   ```javascript
   // Add state
   const [searchNewFilter, setSearchNewFilter] = useState('')
   
   // Add to form
   <input value={searchNewFilter} onChange={...} />
   
   // Add to API call
   new_filter: searchNewFilter || null
   ```

3. **Styling** (`App.css`):
   - Form inputs share `.search-input` and `.search-select` classes
   - No additional styling needed for standard filters

### Performance Optimization

Current optimizations:
- **Result Limit**: 20 cards max per search (prevents overwhelming UI)
- **Image Lazy Loading**: Browser-native lazy loading for images
- **CSS Transforms**: Hardware-accelerated animations
- **Minimal Re-renders**: Efficient state updates

Potential future optimizations:
- Debounced search input
- Infinite scroll pagination
- Image preloading
- Search history caching

---

## 📊 Testing

### Manual Test Cases

**Test 1: Basic Search**
1. Navigate to Card Search mode
2. Enter "flying" in Keywords
3. Click Search
4. Verify results show cards with flying

**Test 2: Combined Filters**
1. Set Colors to "u"
2. Set Mana Value to "2"
3. Set Format to "standard"
4. Click Search
5. Verify only 2-mana blue Standard-legal cards appear

**Test 3: No Results**
1. Set impossible criteria (e.g., Power "100")
2. Click Search
3. Verify "No cards found" message appears

**Test 4: API Error**
1. Stop backend server
2. Click Search
3. Verify error message displays clearly

**Test 5: Clear Function**
1. Fill in multiple filters
2. Click Clear button
3. Verify all filters reset

### Automated Testing

Recommended test coverage:
- Unit tests for query builder logic
- Integration tests for API endpoint
- E2E tests for search flow
- Visual regression tests for card display

---

## 🐛 Known Issues & Limitations

### Current Limitations

1. **Result Limit**: Maximum 20 results per search (by design)
2. **No Pagination**: Can't view results beyond first 20
3. **Single Page**: All results load at once (no infinite scroll)
4. **No Search History**: Previous searches not saved
5. **No Favorites**: Can't save favorite cards

### Future Enhancements

Potential improvements:
- [ ] Pagination support for more results
- [ ] Infinite scroll for seamless browsing
- [ ] Search history with quick access
- [ ] Favorite/bookmark cards
- [ ] Advanced syntax input (raw Scryfall queries)
- [ ] Export results to CSV/JSON
- [ ] Card comparison mode
- [ ] Price information integration
- [ ] Deck building from search results

---

## 📚 Additional Resources

### Scryfall API Documentation
- **Base URL**: `https://api.scryfall.com`
- **Search Endpoint**: `/cards/search`
- **Query Syntax**: [Scryfall Search Reference](https://scryfall.com/docs/syntax)

### Related Files

- **Backend API**: `backend/api/server.py` (lines 84-373)
- **Frontend UI**: `frontend/src/App.jsx` (lines 1-894)
- **Styles**: `frontend/src/App.css` (lines 1046-1485)
- **Tools Module**: `backend/core/tools.py` (search_cards_by_criteria)

---

## 🎉 Summary

The Card Search feature is a **production-ready, fully-featured** advanced search interface with:

✅ **9 Search Filters** - Comprehensive search criteria  
✅ **Professional UI** - Modern, responsive design  
✅ **Beautiful Card Display** - Full images with hover effects  
✅ **Smart Validation** - Format legality checking  
✅ **Error Handling** - Graceful error states  
✅ **Mobile Responsive** - Works on all devices  
✅ **Scryfall Integration** - Direct API integration  
✅ **Production Quality** - Clean code, linter-error free  

**Ready to use immediately!** 🚀

---

*Last Updated: [Auto-generated timestamp]*  
*Version: 1.0.0*  
*Status: ✅ Production Ready*

