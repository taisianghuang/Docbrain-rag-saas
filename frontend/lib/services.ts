import { ChatMessage } from "./types"

export async function chatWithBackend(message: string, history: ChatMessage[], onChunk: (chunk: string) => void) {
  const res = await fetch(`/api/py/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  })

  if (!res.ok || !res.body) {
    throw new Error("Chat request failed")
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (value) {
        const chunk = decoder.decode(value)
        onChunk(chunk)
      }
    }
  } finally {
    try {
      reader.releaseLock()
    } catch (e) {}
  }
}
