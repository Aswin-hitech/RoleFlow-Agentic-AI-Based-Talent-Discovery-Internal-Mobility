export default function MessageBubble({ role, content, pending }) {
  const isUser = role === 'user'

  return (
    <div className={`message message--${isUser ? 'user' : 'assistant'}`}>
      <div className="message__avatar">{isUser ? 'You' : 'AI'}</div>
      <div className="message__bubble">
        {pending ? (
          <span className="dots" aria-label="Thinking">
            <i />
            <i />
            <i />
          </span>
        ) : (
          content
        )}
      </div>
    </div>
  )
}
