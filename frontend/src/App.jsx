import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [question, setQuestion] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [examples, setExamples] = useState([])
  const [apiStatus, setApiStatus] = useState('checking')
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

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion)
    textareaRef.current?.focus()
  }

  const clearChat = () => {
    setChatHistory([])
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
          <div className="status-indicator">
            <span className={`status-dot ${apiStatus}`}></span>
            <span className="status-text">
              {apiStatus === 'online' ? 'Online' : 
               apiStatus === 'offline' ? 'Offline' : 
               apiStatus === 'checking' ? 'Checking...' : 'Error'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="chat-container">
          {/* Welcome / Empty State */}
          {chatHistory.length === 0 && (
            <div className="welcome-section fade-in">
              <div className="welcome-icon">🧙‍♂️</div>
              <h2 className="welcome-title">Welcome to Stack Sage</h2>
              <p className="welcome-text">
                Ask me anything about Magic: The Gathering rules, card interactions, 
                format legality, and more. I have access to the Comprehensive Rules 
                and the Scryfall database.
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
              {chatHistory.map((message, index) => (
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
                </div>
              ))}
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

        {/* Input Form */}
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

