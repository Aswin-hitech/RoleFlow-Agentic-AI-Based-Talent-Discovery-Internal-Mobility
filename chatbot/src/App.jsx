import { useState, useRef, useEffect } from 'react';
import { Mic, Send, Volume2, Bot, Play, Square, Plus, Menu, User, MessageSquare } from 'lucide-react';
import './App.css';

const INITIAL_MESSAGES = [
  { id: 1, text: "Hello! Welcome to All Chat AI. How can I assist you today?", sender: 'bot' },
  { id: 2, text: "Can you explain the new design?", sender: 'user' },
  { id: 3, text: "Certainly! I've been upgraded to a full-screen, immersive layout similar to ChatGPT and Gemini. I also feature ultra-premium colors with deep indigo and fuchsia accents for a futuristic feel.", sender: 'bot' }
];

function App() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [playingId, setPlayingId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    
    const newUserMsg = { id: Date.now(), text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');

    // Simulate bot response
    setTimeout(() => {
      const botMsg = { id: Date.now() + 1, text: "I've received your query. In a real environment, I would connect to the All Chat AI backend to process this.", sender: 'bot' };
      setMessages(prev => [...prev, botMsg]);
    }, 1000);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // Simulate stopping recording after a few seconds
    if (!isRecording) {
      setTimeout(() => {
        setIsRecording(false);
        setInputValue("Simulated voice input via Gnani...");
      }, 3000);
    }
  };

  const togglePlay = (id) => {
    if (playingId === id) {
      setPlayingId(null);
    } else {
      setPlayingId(id);
      setTimeout(() => setPlayingId(null), 4000);
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <button className="new-chat-btn" onClick={() => setMessages([INITIAL_MESSAGES[0]])}>
          <Plus size={18} />
          New chat
        </button>
        
        <div className="history-list">
          <div className="history-item">Understanding Quantum Physics</div>
          <div className="history-item">React useEffect Hook explained</div>
          <div className="history-item">Best hiking trails in CA</div>
        </div>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="avatar">U</div>
            <span style={{ fontSize: '0.95rem' }}>User Profile</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="main-chat">
        <header className="chat-header">
          <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <Menu size={24} />
          </button>
          <div className="header-title">
            <Bot size={24} />
            <span>All Chat AI</span>
          </div>
        </header>

        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-row ${msg.sender}`}>
              <div className="message-content">
                <div className={`msg-avatar ${msg.sender}`}>
                  {msg.sender === 'bot' ? <Bot size={20} /> : <User size={20} />}
                </div>
                <div className="msg-body">
                  <p>{msg.text}</p>
                  {msg.sender === 'bot' && (
                    <div className="msg-actions">
                      <button 
                        className={`icon-btn ${playingId === msg.id ? 'playing' : ''}`}
                        onClick={() => togglePlay(msg.id)}
                        title="Read aloud"
                      >
                        {playingId === msg.id ? <Volume2 size={16} /> : <Play size={16} />}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Wrapper */}
        <div className="input-wrapper">
          <div className="input-box">
            <button 
              className={`mic-btn-main ${isRecording ? 'recording' : ''}`}
              onClick={toggleRecording}
              title="Voice to Text"
            >
              {isRecording ? <Square size={18} fill="currentColor" /> : <Mic size={20} />}
            </button>
            <input 
              type="text"
              className="chat-input"
              placeholder={isRecording ? "Listening..." : "Message All Chat AI..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isRecording}
            />
            <button 
              className="send-btn-main" 
              onClick={handleSend}
              disabled={isRecording || !inputValue.trim()}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
