import { useCallback, useEffect, useRef, useState } from 'react'

import ChatInput from './components/ChatInput'
import MessageBubble from './components/MessageBubble'
import { streamChat } from './api'

let nextId = 1
const newId = () => `m${nextId++}`

export default function App() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)

  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages])

  const send = useCallback(
    async (text) => {
      const history = [...messages, { id: newId(), role: 'user', content: text }]
      const replyId = newId()

      setMessages([...history, { id: replyId, role: 'assistant', content: '' }])
      setError(null)
      setIsStreaming(true)

      try {
        await streamChat(
          history.map(({ role, content }) => ({ role, content })),
          {
            onDelta: (_delta, full) =>
              setMessages((prev) =>
                prev.map((message) =>
                  message.id === replyId ? { ...message, content: full } : message,
                ),
              ),
          },
        )
      } catch (err) {
        setError(err.message)
        setMessages((prev) => prev.filter((message) => message.id !== replyId))
      } finally {
        setIsStreaming(false)
      }
    },
    [messages],
  )

  return (
    <div className="app">
      <div className="chat">
        <header className="chat__header">
          <div>
            <h1 className="chat__title">Chatbot</h1>
            <p className="chat__subtitle">React + Flask + gpt-oss-120b</p>
          </div>
          <button
            className="chat__reset"
            onClick={() => {
              setMessages([])
              setError(null)
            }}
            disabled={isStreaming || messages.length === 0}
          >
            New chat
          </button>
        </header>

        <main className="chat__body" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="empty">
              <h2>Ask me anything</h2>
              <p>Your messages are sent to the Flask backend and streamed back token by token.</p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                pending={isStreaming && message.content === ''}
              />
            ))
          )}
        </main>

        {error && <div className="alert">{error}</div>}

        <ChatInput onSend={send} disabled={isStreaming} />
      </div>
    </div>
  )
}
