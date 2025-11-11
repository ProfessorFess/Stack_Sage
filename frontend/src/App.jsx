import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  // UI Mode State
  const [mode, setMode] = useState('chat') // 'chat', 'deck', or 'search'
  
  // Chat State
  const [question, setQuestion] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [examples, setExamples] = useState([])
  const [apiStatus, setApiStatus] = useState('checking')
  
  // Deck Validator State
  const [decklist, setDecklist] = useState('')
  const [deckFormat, setDeckFormat] = useState('standard')
  const [commander, setCommander] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  
  // Card Search State
  const [searchCardName, setSearchCardName] = useState('') // Primary search
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false) // Toggle for advanced
  const [searchColors, setSearchColors] = useState('')
  const [searchManaValue, setSearchManaValue] = useState('')
  const [searchPower, setSearchPower] = useState('')
  const [searchToughness, setSearchToughness] = useState('')
  const [searchFormat, setSearchFormat] = useState('')
  const [searchCardType, setSearchCardType] = useState('')
  const [searchKeywords, setSearchKeywords] = useState('')
  const [searchText, setSearchText] = useState('')
  const [searchRarity, setSearchRarity] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState(null)
  const [autocompleteResults, setAutocompleteResults] = useState([]) // Live autocomplete
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [isLoadingAutocomplete, setIsLoadingAutocomplete] = useState(false)
  
  // Refs
  const chatEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Check API health on mount
  useEffect(() => {
    checkApiHealth()
    fetchExamples()
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [question])

  // Live autocomplete search as user types
  useEffect(() => {
    const searchCards = async () => {
      const query = searchCardName.trim()
      
      if (query.length < 2) {
        setAutocompleteResults([])
        setShowAutocomplete(false)
        return
      }

      setIsLoadingAutocomplete(true)

      try {
        // Use Scryfall's autocomplete API directly
        const response = await axios.get('https://api.scryfall.com/cards/autocomplete', {
          params: { q: query },
          timeout: 5000
        })

        if (response.data.data && response.data.data.length > 0) {
          // Fetch full card details for the autocomplete results
          const cardNames = response.data.data.slice(0, 8) // Limit to 8 suggestions
          
          // Fetch detailed card info for each suggestion
          const cardDetailsPromises = cardNames.map(async (cardName) => {
            try {
              const cardResponse = await axios.get('https://api.scryfall.com/cards/named', {
                params: { fuzzy: cardName },
                timeout: 3000
              })
              return cardResponse.data
            } catch (err) {
              console.error(`Failed to fetch details for ${cardName}:`, err)
              return null
            }
          })

          const cardDetails = await Promise.all(cardDetailsPromises)
          const validCards = cardDetails.filter(card => card !== null)
          
          setAutocompleteResults(validCards)
          setShowAutocomplete(validCards.length > 0)
        } else {
          setAutocompleteResults([])
          setShowAutocomplete(false)
        }
      } catch (error) {
        console.error('Autocomplete error:', error)
        setAutocompleteResults([])
        setShowAutocomplete(false)
      } finally {
        setIsLoadingAutocomplete(false)
      }
    }

    // Debounce the search
    const timeoutId = setTimeout(searchCards, 300)
    
    return () => clearTimeout(timeoutId)
  }, [searchCardName])

  const checkApiHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`, { timeout: 5000 })
      setApiStatus(response.data.status === 'healthy' ? 'online' : 'error')
    } catch (error) {
      setApiStatus('offline')
      console.error('API health check failed:', error)
    }
  }

  const fetchExamples = async () => {
    try {
      const response = await axios.get(`${API_URL}/examples`)
      setExamples(response.data.examples || [])
    } catch (error) {
      console.error('Failed to fetch examples:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim() || isLoading) return

    const userQuestion = question.trim()
    setQuestion('')
    
    // Add user message to chat
    const userMessage = {
      type: 'question',
      content: userQuestion,
      timestamp: new Date().toISOString()
    }
    setChatHistory(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await axios.post(`${API_URL}/ask`, {
        question: userQuestion
      }, {
        timeout: 60000 // 60 second timeout for complex questions
      })

      // Add AI response to chat
      const aiMessage = {
        type: 'answer',
        content: response.data.answer,
        success: response.data.success,
        tools_used: response.data.tools_used || [],
        citations: response.data.citations || [],
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error asking question:', error)
      
      let errorMessage = 'Failed to get a response from Stack Sage. '
      if (error.code === 'ECONNREFUSED') {
        errorMessage += 'The API server appears to be offline. Please make sure it\'s running on port 8000.'
      } else if (error.code === 'ECONNABORTED') {
        errorMessage += 'The request timed out. This question might be too complex or the server is overloaded.'
      } else {
        errorMessage += error.message
      }

      const errorResponse = {
        type: 'answer',
        content: errorMessage,
        success: false,
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeckValidation = async (e) => {
    e.preventDefault()
    if (!decklist.trim() || isValidating) return

    setIsValidating(true)
    setValidationResult(null)

    try {
      const response = await axios.post(`${API_URL}/validate-deck`, {
        decklist: decklist.trim(),
        format: deckFormat,
        commander: commander.trim() || null
      }, {
        timeout: 30000
      })

      setValidationResult(response.data)
    } catch (error) {
      console.error('Error validating deck:', error)
      
      let errorMessage = 'Failed to validate deck. '
      if (error.response?.data?.detail) {
        errorMessage += error.response.data.detail
      } else {
        errorMessage += error.message
      }

      setValidationResult({
        is_legal: false,
        format: deckFormat,
        total_cards: 0,
        errors: [errorMessage],
        warnings: []
      })
    } finally {
      setIsValidating(false)
    }
  }

  const handleCardSearch = async (e) => {
    e.preventDefault()
    
    // Check if at least one search criterion is provided (name OR filters)
    const hasSearchCriteria = searchCardName.trim() || searchColors || searchManaValue || searchPower || 
                              searchToughness || searchFormat || searchCardType || 
                              searchKeywords || searchText || searchRarity
    
    if (!hasSearchCriteria || isSearching) return

    setIsSearching(true)
    setSearchResults(null)

    try {
      const response = await axios.post(`${API_URL}/search-cards`, {
        card_name: searchCardName.trim() || null,
        colors: searchColors || null,
        mana_value: searchManaValue || null,
        power: searchPower || null,
        toughness: searchToughness || null,
        format_legal: searchFormat || null,
        card_type: searchCardType || null,
        keywords: searchKeywords || null,
        text: searchText || null,
        rarity: searchRarity || null
      }, {
        timeout: 15000
      })

      setSearchResults(response.data)
    } catch (error) {
      console.error('Error searching cards:', error)
      
      let errorMessage = 'Failed to search cards. '
      if (error.response?.data?.detail) {
        errorMessage += error.response.data.detail
      } else {
        errorMessage += error.message
      }

      setSearchResults({
        total_cards: 0,
        query: '',
        cards: [],
        success: false,
        error: errorMessage
      })
    } finally {
      setIsSearching(false)
    }
  }

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion)
    textareaRef.current?.focus()
  }

  const clearChat = () => {
    setChatHistory([])
  }

  const clearDeck = () => {
    setDecklist('')
    setCommander('')
    setValidationResult(null)
  }

  const handleSelectCard = (card) => {
    // When user selects a card from autocomplete, show it as the result
    setSearchResults({
      total_cards: 1,
      query: `name:"${card.name}"`,
      cards: [{
        name: card.name,
        mana_cost: card.mana_cost || '',
        type_line: card.type_line || '',
        oracle_text: card.oracle_text || '',
        power: card.power,
        toughness: card.toughness,
        image_url: card.image_uris?.normal || '',
        scryfall_url: card.scryfall_uri || '',
        rarity: card.rarity || '',
        set_name: card.set_name || '',
        collector_number: card.collector_number || ''
      }],
      success: true
    })
    setShowAutocomplete(false)
    setSearchCardName(card.name)
  }

  const clearSearch = () => {
    setSearchCardName('')
    setSearchColors('')
    setSearchManaValue('')
    setSearchPower('')
    setSearchToughness('')
    setSearchFormat('')
    setSearchCardType('')
    setSearchKeywords('')
    setSearchText('')
    setSearchRarity('')
    setSearchResults(null)
    setShowAdvancedFilters(false)
    setAutocompleteResults([])
    setShowAutocomplete(false)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">📘</div>
            <div>
              <h1 className="title">Stack Sage</h1>
              <p className="subtitle">Your Intelligent MTG Rules Companion</p>
            </div>
          </div>
          
          <div className="header-actions">
            <div className="mode-toggle">
              <button
                className={`mode-button ${mode === 'chat' ? 'active' : ''}`}
                onClick={() => setMode('chat')}
              >
                <span className="mode-label">Chat</span>
              </button>
              <button
                className={`mode-button ${mode === 'search' ? 'active' : ''}`}
                onClick={() => setMode('search')}
              >
                <span className="mode-label">Card Search</span>
              </button>
              <button
                className={`mode-button ${mode === 'deck' ? 'active' : ''}`}
                onClick={() => setMode('deck')}
              >
                <span className="mode-label">Deck Validator</span>
              </button>
            </div>
            
            <div className="status-indicator">
              <span className={`status-dot ${apiStatus}`}></span>
              <span className="status-text">
                {apiStatus === 'online' ? 'Online' : 
                 apiStatus === 'offline' ? 'Offline' : 
                 apiStatus === 'checking' ? 'Checking...' : 'Error'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Chat Mode */}
        {mode === 'chat' && (
          <>
            <div className="chat-container">
              {/* Welcome / Empty State */}
              {chatHistory.length === 0 && (
                <div className="welcome-section fade-in">
                  <div className="welcome-icon">🧙‍♂️</div>
                  <h2 className="welcome-title">Welcome to Stack Sage</h2>
                  <p className="welcome-text">
                    Ask me anything about Magic: The Gathering rules, card interactions, 
                    format legality, and more.
                  </p>
                  
                  {examples.length > 0 && (
                    <div className="examples-section">
                      <h3 className="examples-title">Try asking:</h3>
                      <div className="examples-grid">
                        {examples.slice(0, 6).map((example, index) => (
                          <button
                            key={index}
                            className="example-chip"
                            onClick={() => handleExampleClick(example)}
                          >
                            {example}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Chat Messages */}
              {chatHistory.length > 0 && (
                <div className="chat-messages">
                  {chatHistory.map((message, index) => {
                    return (
                      <div 
                        key={index} 
                        className={`message ${message.type} fade-in`}
                      >
                        <div className="message-header">
                          <span className="message-icon">
                            {message.type === 'question' ? '🃏' : '📜'}
                          </span>
                          <span className="message-label">
                            {message.type === 'question' ? 'Your Question' : 'Stack Sage'}
                          </span>
                        </div>
                        <div className={`message-content ${message.success === false ? 'error' : ''}`}>
                          {message.type === 'answer' ? (
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                          ) : (
                            <p>{message.content}</p>
                          )}
                        </div>
                        
                        {/* Metadata section for answers */}
                        {message.type === 'answer' && (message.tools_used?.length > 0 || message.citations?.length > 0) && (
                          <div className="message-metadata">
                            {message.tools_used && message.tools_used.length > 0 && (
                              <div className="metadata-item">
                                <span className="metadata-icon">🔧</span>
                                <span className="metadata-label">Tools:</span>
                                <span className="metadata-value">{message.tools_used.join(', ')}</span>
                              </div>
                            )}
                            {message.citations && message.citations.length > 0 && (
                              <div className="metadata-item">
                                <span className="metadata-icon">📚</span>
                                <span className="metadata-label">Citations:</span>
                                <span className="metadata-value">{message.citations.length} source(s)</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  <div ref={chatEndRef} />
                </div>
              )}

              {/* Loading Indicator */}
              {isLoading && (
                <div className="loading-message fade-in">
                  <div className="loading-spinner"></div>
                  <p className="loading-text">Consulting the Comprehensive Rules...</p>
                </div>
              )}
            </div>

            {/* Chat Input Form */}
            <div className="input-container">
              <form onSubmit={handleSubmit} className="input-form">
                <div className="input-wrapper">
                  <textarea
                    ref={textareaRef}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSubmit(e)
                      }
                    }}
                    placeholder="Ask about MTG rules, card interactions, format legality..."
                    className="question-input"
                    rows="1"
                    disabled={isLoading || apiStatus === 'offline'}
                  />
                  <button 
                    type="submit" 
                    className="submit-button"
                    disabled={!question.trim() || isLoading || apiStatus === 'offline'}
                  >
                    {isLoading ? '⏳' : '✨'}
                  </button>
                </div>
                {chatHistory.length > 0 && (
                  <button 
                    type="button"
                    onClick={clearChat}
                    className="clear-button"
                  >
                    Clear Chat
                  </button>
                )}
              </form>
              <p className="input-hint">
                Press <kbd>Enter</kbd> to send • <kbd>Shift + Enter</kbd> for new line
              </p>
            </div>
          </>
        )}

        {/* Card Search Mode */}
        {mode === 'search' && (
          <div className="card-search-container">
            <div className="card-search-header">
              <div className="search-icon">🔍</div>
              <div>
                <h2 className="search-title">Card Search</h2>
                <p className="search-subtitle">
                  Find Magic: The Gathering cards by name or using advanced filters
                </p>
              </div>
            </div>

            <form onSubmit={handleCardSearch} className="search-form">
              {/* Primary Card Name Search */}
              <div className="primary-search">
                <label htmlFor="cardName" className="primary-search-label">
                  Search by Card Name
                  {isLoadingAutocomplete && <span className="loading-indicator"> • Searching...</span>}
                </label>
                <div className="primary-search-wrapper">
                  <input
                    id="cardName"
                    type="text"
                    value={searchCardName}
                    onChange={(e) => setSearchCardName(e.target.value)}
                    onFocus={() => autocompleteResults.length > 0 && setShowAutocomplete(true)}
                    placeholder="e.g., Lightning Bolt, Black Lotus, Counterspell..."
                    className="primary-search-input"
                    disabled={isSearching}
                    autoFocus
                    autoComplete="off"
                  />
                  <button
                    type="submit"
                    className="primary-search-button"
                    disabled={!searchCardName.trim() && !searchColors && !searchManaValue && !searchPower && 
                             !searchToughness && !searchFormat && !searchCardType && !searchKeywords && 
                             !searchText && !searchRarity || isSearching || apiStatus === 'offline'}
                  >
                    {isSearching ? (
                      <>
                        <div className="button-spinner"></div>
                        Searching...
                      </>
                    ) : (
                      <>🔍 Search</>
                    )}
                  </button>
                </div>

                {/* Autocomplete Dropdown */}
                {showAutocomplete && autocompleteResults.length > 0 && (
                  <div className="autocomplete-dropdown fade-in">
                    {autocompleteResults.map((card, index) => (
                      <div
                        key={index}
                        className="autocomplete-item"
                        onClick={() => handleSelectCard(card)}
                      >
                        {card.image_uris?.small && (
                          <img
                            src={card.image_uris.small}
                            alt={card.name}
                            className="autocomplete-card-image"
                          />
                        )}
                        <div className="autocomplete-card-info">
                          <div className="autocomplete-card-name">
                            {card.name}
                            {card.mana_cost && (
                              <span className="autocomplete-card-mana">{card.mana_cost}</span>
                            )}
                          </div>
                          <div className="autocomplete-card-type">{card.type_line}</div>
                          <div className="autocomplete-card-legality">
                            {Object.entries(card.legalities || {})
                              .filter(([_, status]) => status === 'legal')
                              .slice(0, 5)
                              .map(([format, _]) => (
                                <span key={format} className="legality-badge">
                                  {format}
                                </span>
                              ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Advanced Filters Toggle */}
              <div className="advanced-filters-toggle">
                <button
                  type="button"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className="toggle-advanced-button"
                  disabled={isSearching}
                >
                  <span className="toggle-icon">{showAdvancedFilters ? '▼' : '▶'}</span>
                  <span className="toggle-text">
                    {showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters
                  </span>
                  <span className="toggle-hint">
                    (colors, mana cost, type, format, etc.)
                  </span>
                </button>
              </div>

              {/* Advanced Filters Section (Collapsible) */}
              {showAdvancedFilters && (
                <div className="advanced-filters-section fade-in">
                  <div className="search-grid">
                {/* Colors */}
                <div className="form-group">
                  <label htmlFor="colors" className="form-label">
                    Colors <span className="label-hint">(w/u/b/r/g/c)</span>
                  </label>
                  <input
                    id="colors"
                    type="text"
                    value={searchColors}
                    onChange={(e) => setSearchColors(e.target.value)}
                    placeholder="e.g., ur (blue/red)"
                    className="search-input"
                    disabled={isSearching}
                  />
                </div>

                {/* Mana Value */}
                <div className="form-group">
                  <label htmlFor="manaValue" className="form-label">
                    Mana Value <span className="label-hint">(e.g., 3, {'<'}=2, {'>='}4)</span>
                  </label>
                  <input
                    id="manaValue"
                    type="text"
                    value={searchManaValue}
                    onChange={(e) => setSearchManaValue(e.target.value)}
                    placeholder="e.g., 3 or <=2"
                    className="search-input"
                    disabled={isSearching}
                  />
                </div>

                {/* Card Type */}
                <div className="form-group">
                  <label htmlFor="cardType" className="form-label">
                    Card Type
                  </label>
                  <select
                    id="cardType"
                    value={searchCardType}
                    onChange={(e) => setSearchCardType(e.target.value)}
                    className="search-select"
                    disabled={isSearching}
                  >
                    <option value="">Any Type</option>
                    <option value="creature">Creature</option>
                    <option value="instant">Instant</option>
                    <option value="sorcery">Sorcery</option>
                    <option value="enchantment">Enchantment</option>
                    <option value="artifact">Artifact</option>
                    <option value="planeswalker">Planeswalker</option>
                    <option value="land">Land</option>
                  </select>
                </div>

                {/* Format */}
                <div className="form-group">
                  <label htmlFor="format" className="form-label">
                    Format
                  </label>
                  <select
                    id="format"
                    value={searchFormat}
                    onChange={(e) => setSearchFormat(e.target.value)}
                    className="search-select"
                    disabled={isSearching}
                  >
                    <option value="">Any Format</option>
                    <option value="standard">Standard</option>
                    <option value="modern">Modern</option>
                    <option value="pioneer">Pioneer</option>
                    <option value="legacy">Legacy</option>
                    <option value="vintage">Vintage</option>
                    <option value="commander">Commander</option>
                    <option value="pauper">Pauper</option>
                  </select>
                </div>

                {/* Power */}
                <div className="form-group">
                  <label htmlFor="power" className="form-label">
                    Power <span className="label-hint">(creatures only)</span>
                  </label>
                  <input
                    id="power"
                    type="text"
                    value={searchPower}
                    onChange={(e) => setSearchPower(e.target.value)}
                    placeholder="e.g., 3 or >=5"
                    className="search-input"
                    disabled={isSearching}
                  />
                </div>

                {/* Toughness */}
                <div className="form-group">
                  <label htmlFor="toughness" className="form-label">
                    Toughness <span className="label-hint">(creatures only)</span>
                  </label>
                  <input
                    id="toughness"
                    type="text"
                    value={searchToughness}
                    onChange={(e) => setSearchToughness(e.target.value)}
                    placeholder="e.g., 3 or >=5"
                    className="search-input"
                    disabled={isSearching}
                  />
                </div>

                {/* Rarity */}
                <div className="form-group">
                  <label htmlFor="rarity" className="form-label">
                    Rarity
                  </label>
                  <select
                    id="rarity"
                    value={searchRarity}
                    onChange={(e) => setSearchRarity(e.target.value)}
                    className="search-select"
                    disabled={isSearching}
                  >
                    <option value="">Any Rarity</option>
                    <option value="common">Common</option>
                    <option value="uncommon">Uncommon</option>
                    <option value="rare">Rare</option>
                    <option value="mythic">Mythic Rare</option>
                  </select>
                </div>

                {/* Keywords */}
                <div className="form-group">
                  <label htmlFor="keywords" className="form-label">
                    Keywords
                  </label>
                  <input
                    id="keywords"
                    type="text"
                    value={searchKeywords}
                    onChange={(e) => setSearchKeywords(e.target.value)}
                    placeholder="e.g., flying, haste"
                    className="search-input"
                    disabled={isSearching}
                  />
                </div>
              </div>

                  {/* Oracle Text Search (Full Width) */}
                  <div className="form-group full-width">
                    <label htmlFor="text" className="form-label">
                      Oracle Text <span className="label-hint">(search card text)</span>
                    </label>
                    <input
                      id="text"
                      type="text"
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      placeholder="e.g., counter target spell, draw a card"
                      className="search-input"
                      disabled={isSearching}
                    />
                  </div>
                </div>
              )}

              {/* Clear Button */}
              {(searchCardName || searchColors || searchManaValue || searchPower || searchToughness || 
                searchFormat || searchCardType || searchKeywords || searchText || searchRarity) && (
                <div className="form-actions">
                  <button
                    type="button"
                    onClick={clearSearch}
                    className="clear-all-button"
                    disabled={isSearching}
                  >
                    ✕ Clear All
                  </button>
                </div>
              )}
            </form>

            {/* Search Results */}
            {searchResults && (
              <div className="search-results fade-in">
                {searchResults.success !== false ? (
                  <>
                    <div className="results-header">
                      <h3 className="results-title">
                        {searchResults.total_cards > 0 
                          ? `Found ${searchResults.total_cards} card${searchResults.total_cards !== 1 ? 's' : ''}`
                          : 'No cards found'}
                      </h3>
                      {searchResults.query && (
                        <p className="results-query">Query: <code>{searchResults.query}</code></p>
                      )}
                    </div>

                    {searchResults.cards && searchResults.cards.length > 0 ? (
                      <>
                        <div className="cards-grid">
                          {searchResults.cards.map((card, index) => (
                            <div key={index} className="card-result">
                              {card.image_url && (
                                <div className="card-image-container">
                                  <img 
                                    src={card.image_url} 
                                    alt={card.name}
                                    className="card-image"
                                  />
                                </div>
                              )}
                              <div className="card-details">
                                <h4 className="card-name">{card.name}</h4>
                                {card.mana_cost && (
                                  <p className="card-mana">{card.mana_cost}</p>
                                )}
                                <p className="card-type">{card.type_line}</p>
                                {(card.power || card.toughness) && (
                                  <p className="card-pt">{card.power}/{card.toughness}</p>
                                )}
                                {card.oracle_text && (
                                  <p className="card-text">{card.oracle_text}</p>
                                )}
                                <div className="card-meta">
                                  {card.set_name && (
                                    <span className="card-set">{card.set_name}</span>
                                  )}
                                  {card.rarity && (
                                    <span className={`card-rarity ${card.rarity}`}>
                                      {card.rarity}
                                    </span>
                                  )}
                                </div>
                                {card.scryfall_url && (
                                  <a 
                                    href={card.scryfall_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="card-link"
                                  >
                                    View on Scryfall →
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                        {searchResults.total_cards > searchResults.cards.length && (
                          <p className="results-note">
                            Showing top {searchResults.cards.length} of {searchResults.total_cards} results. 
                            Refine your search for more specific results.
                          </p>
                        )}
                      </>
                    ) : (
                      <div className="no-results">
                        <p className="no-results-icon">🔍</p>
                        <p className="no-results-text">No cards match your search criteria.</p>
                        <p className="no-results-hint">Try adjusting your filters or broadening your search.</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="search-error">
                    <p className="error-icon">❌</p>
                    <p className="error-text">{searchResults.error || 'Failed to search cards'}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Deck Validator Mode */}
        {mode === 'deck' && (
          <div className="deck-validator-container">
            <div className="deck-validator-header">
              <div className="deck-icon">🎴</div>
              <div>
                <h2 className="deck-title">Deck Validator</h2>
                <p className="deck-subtitle">
                  Validate your deck for format legality and card restrictions
                </p>
              </div>
            </div>

            <form onSubmit={handleDeckValidation} className="deck-form">
              <div className="form-group">
                <label htmlFor="format" className="form-label">
                  Format <span className="format-badge">{deckFormat.toUpperCase()}</span>
                </label>
                <select
                  id="format"
                  value={deckFormat}
                  onChange={(e) => setDeckFormat(e.target.value)}
                  className="format-select"
                  disabled={isValidating}
                >
                  <option value="standard">Standard</option>
                  <option value="modern">Modern</option>
                  <option value="pioneer">Pioneer</option>
                  <option value="legacy">Legacy</option>
                  <option value="vintage">Vintage</option>
                  <option value="commander">Commander (EDH)</option>
                  <option value="pauper">Pauper</option>
                  <option value="brawl">Brawl</option>
                </select>
              </div>

              {(deckFormat === 'commander' || deckFormat === 'brawl') && (
                <div className="form-group">
                  <label htmlFor="commander" className="form-label">
                    Commander (Optional)
                  </label>
                  <input
                    id="commander"
                    type="text"
                    value={commander}
                    onChange={(e) => setCommander(e.target.value)}
                    placeholder="Enter commander name..."
                    className="commander-input"
                    disabled={isValidating}
                  />
                </div>
              )}

              <div className="form-group">
                <label htmlFor="decklist" className="form-label">
                  Decklist
                </label>
                <textarea
                  id="decklist"
                  value={decklist}
                  onChange={(e) => setDecklist(e.target.value)}
                  placeholder="Enter your decklist (e.g., '4 Lightning Bolt')&#10;One card per line"
                  className="decklist-input"
                  rows="12"
                  disabled={isValidating}
                />
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="validate-button"
                  disabled={!decklist.trim() || isValidating || apiStatus === 'offline'}
                >
                  {isValidating ? (
                    <>
                      <div className="button-spinner"></div>
                      Validating...
                    </>
                  ) : (
                    <>✓ Validate Deck</>
                  )}
                </button>
                {decklist && (
                  <button
                    type="button"
                    onClick={clearDeck}
                    className="clear-deck-button"
                    disabled={isValidating}
                  >
                    Clear
                  </button>
                )}
              </div>
            </form>

            {/* Validation Results */}
            {validationResult && (
              <div className={`validation-result ${validationResult.is_legal ? 'legal' : 'illegal'} fade-in`}>
                <div className="result-header">
                  <div className="result-icon">
                    {validationResult.is_legal ? '✅' : '❌'}
                  </div>
                  <div>
                    <h3 className="result-title">
                      {validationResult.is_legal ? 'Deck is Legal!' : 'Deck is Not Legal'}
                    </h3>
                    <p className="result-subtitle">
                      {validationResult.format.toUpperCase()} • {validationResult.total_cards} cards
                    </p>
                  </div>
                </div>

                <div className="result-stats">
                  <div className="stat-item">
                    <span className="stat-label">Total Cards</span>
                    <span className="stat-value">{validationResult.total_cards}</span>
                  </div>
                  <div className={`stat-item ${validationResult.errors.length > 0 ? 'error' : ''}`}>
                    <span className="stat-label">Errors</span>
                    <span className="stat-value">{validationResult.errors.length}</span>
                  </div>
                  <div className={`stat-item ${validationResult.warnings.length > 0 ? 'warning' : ''}`}>
                    <span className="stat-label">Warnings</span>
                    <span className="stat-value">{validationResult.warnings.length}</span>
                  </div>
                </div>

                {validationResult.errors.length > 0 && (
                  <div className="result-issues errors">
                    <h4 className="issues-title">🚫 Errors</h4>
                    <ul className="issues-list">
                      {validationResult.errors.map((error, index) => (
                        <li key={index} className="issue-item error">
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {validationResult.warnings.length > 0 && (
                  <div className="result-issues warnings">
                    <h4 className="issues-title">⚠️ Warnings</h4>
                    <ul className="issues-list">
                      {validationResult.warnings.map((warning, index) => (
                        <li key={index} className="issue-item warning">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          Powered by <strong>RAG</strong> • Comprehensive Rules • Scryfall API
        </p>
      </footer>
    </div>
  )
}

export default App
