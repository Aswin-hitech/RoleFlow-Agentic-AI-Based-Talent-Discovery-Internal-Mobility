import { useEffect, useRef, useState } from 'react'

const MAX_HEIGHT = 160

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, MAX_HEIGHT)}px`
  }, [value])

  const submit = (event) => {
    event.preventDefault()
    const text = value.trim()
    if (!text || disabled) return
    setValue('')
    onSend(text)
  }

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        ref={textareaRef}
        className="composer__input"
        value={value}
        rows={1}
        placeholder="Send a message…  (Enter to send, Shift+Enter for a new line)"
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) submit(event)
        }}
      />
      <button className="composer__send" type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  )
}
