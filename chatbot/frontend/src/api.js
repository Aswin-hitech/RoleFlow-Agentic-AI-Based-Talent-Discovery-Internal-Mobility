const CHAT_ENDPOINT = '/api/chat'

/**
 * POSTs the conversation to the backend and reads the SSE stream of tokens.
 * Calls `onDelta(delta, fullTextSoFar)` as text arrives, resolves with the
 * complete reply, and throws if the request or the model call fails.
 */
export async function streamChat(messages, { onDelta, signal } = {}) {
  const response = await fetch(CHAT_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }
  if (!response.body) {
    throw new Error('Streaming is not supported by this browser.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let full = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const event of events) {
      const payload = parseEvent(event)
      if (!payload) continue
      if (payload.error) throw new Error(payload.error)
      if (payload.delta) {
        full += payload.delta
        onDelta?.(payload.delta, full)
      }
    }
  }

  return full
}

function parseEvent(event) {
  const line = event
    .split('\n')
    .map((part) => part.trim())
    .find((part) => part.startsWith('data:'))

  if (!line) return null
  try {
    return JSON.parse(line.slice('data:'.length).trim())
  } catch {
    return null
  }
}

async function readError(response) {
  try {
    const body = await response.json()
    if (body?.error) return body.error
  } catch {
    // Body was not JSON; fall through to the status code.
  }
  return `Request failed with status ${response.status}.`
}
