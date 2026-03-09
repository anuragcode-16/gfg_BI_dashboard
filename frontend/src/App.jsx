// src/App.jsx
import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import WelcomeHero from './components/WelcomeHero';
import ChatInterface from './components/ChatInterface';
import { sendQuery, uploadCSV, resetDataset, healthCheck } from './api';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploaded, setIsUploaded] = useState(false);
  const [uploadedDbPath, setUploadedDbPath] = useState(null);
  const [uploadedSchema, setUploadedSchema] = useState(null);
  const [lastSql, setLastSql] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const bottomRef = useRef(null);

  // Check API health on mount
  useEffect(() => {
    healthCheck().then(setApiOnline);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (queryText) => {
    const query = queryText || input.trim();
    if (!query || isLoading) return;

    setInput('');

    // Add user message
    const userMsg = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await sendQuery({
        query,
        conversationHistory: messages.length > 0 ? messages : null,
        previousSql: lastSql,
        dbPath: isUploaded ? uploadedDbPath : null,
        schemaOverride: isUploaded ? uploadedSchema : null,
      });

      if (result.error) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', error: result.error, sql: result.sql },
        ]);
      } else {
        setLastSql(result.sql);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            sql: result.sql,
            data: result.data,
            columns: result.columns,
            visualization: result.visualization,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', error: `Connection error: ${err.message}. Is the backend running?` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file) => {
    try {
      const result = await uploadCSV(file);
      if (result.success) {
        setIsUploaded(true);
        setUploadedDbPath(result.db_path);
        setUploadedSchema(result.schema);
        setMessages([]);
        setLastSql(null);
        setMessages([
          {
            role: 'assistant',
            text: `✅ Dataset loaded: ${result.row_count} rows, ${result.col_count} columns. Ask me anything about your data!`,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', error: `Upload failed: ${result.message}` },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', error: `Upload error: ${err.message}` },
      ]);
    }
  };

  const handleReset = async () => {
    try {
      await resetDataset();
      setIsUploaded(false);
      setUploadedDbPath(null);
      setUploadedSchema(null);
      setMessages([]);
      setLastSql(null);
    } catch (err) {
      console.error('Reset error:', err);
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
    setLastSql(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <>
      {/* Animated Background */}
      <div className="app-background">
        <div className="glow-orb glow-orb--purple" />
        <div className="glow-orb glow-orb--pink" />
        <div className="glow-orb glow-orb--violet" />
      </div>

      <div className="app-layout">
        {/* Sidebar */}
        <Sidebar
          onQuery={handleSubmit}
          isUploaded={isUploaded}
          onUpload={handleUpload}
          onReset={handleReset}
          onClearHistory={handleClearHistory}
        />

        {/* Main */}
        <div className="app-main">
          {/* Header */}
          <header className="app-header">
            <div className="header-logo">
              <div className="header-logo-icon">⚡</div>
              <span className="header-logo-text">InsightAI</span>
            </div>
            <div className="header-badge">
              <span
                className="header-badge-dot"
                style={{ background: apiOnline ? '#22c55e' : '#f87171' }}
              />
              {apiOnline ? 'System Online' : 'Backend Offline'}
            </div>
          </header>

          {/* Content */}
          <div className="app-content">
            {messages.length === 0 ? (
              <WelcomeHero />
            ) : (
              <ChatInterface messages={messages} isLoading={isLoading} />
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input Area */}
          <div className="app-input-area">
            <div className="chat-input-container">
              <input
                className="chat-input"
                type="text"
                placeholder="Ask a question about your data..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
              />
              <button
                className="chat-send-btn"
                onClick={() => handleSubmit()}
                disabled={isLoading || !input.trim()}
              >
                ➤
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
