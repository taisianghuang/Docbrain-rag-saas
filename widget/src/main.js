// Simple embeddable RAG widget (vanilla JS) that uses Shadow DOM
class RAGWidget {
  constructor() {
    this.backend = this._detectBackend()
    this.history = []
    this._mount()
  }

  _detectBackend() {
    try {
      const current = document.currentScript || (function(){const s=document.scripts[document.scripts.length-1];return s})();
      if (current && current.dataset && current.dataset.backend) return current.dataset.backend.replace(/\/$/, '')
    } catch (e) {}
    return 'http://localhost:8000'
  }

  _mount() {
    this.container = document.createElement('div')
    this.container.id = 'rag-widget-root'
    document.body.appendChild(this.container)

    this.shadow = this.container.attachShadow({ mode: 'open' })
    const style = document.createElement('style')
    style.textContent = `
      .rb{position:fixed;right:20px;bottom:20px;z-index:99999}
      .bubble{width:56px;height:56px;border-radius:50%;background:#0066ff;color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.15)}
      .panel{position:fixed;right:20px;bottom:90px;width:350px;height:480px;background:#fff;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.2);display:flex;flex-direction:column;overflow:hidden}
      .messages{flex:1;padding:12px;overflow:auto;font-family:Arial,Helvetica,sans-serif}
      .input{display:flex;padding:8px;border-top:1px solid #eee}
      .input input{flex:1;padding:8px;border:1px solid #ddd;border-radius:6px}
      .input button{margin-left:8px;padding:8px 12px;background:#0066ff;color:#fff;border:none;border-radius:6px}
      .msg-user{background:#eef3ff;padding:8px;border-radius:8px;margin:6px 0;align-self:flex-end}
      .msg-bot{background:#f6f7f8;padding:8px;border-radius:8px;margin:6px 0;align-self:flex-start}
    `
    this.shadow.appendChild(style)

    const wrapper = document.createElement('div')
    wrapper.className = 'rb'

    this.bubble = document.createElement('div')
    this.bubble.className = 'bubble'
    this.bubble.textContent = '💬'
    wrapper.appendChild(this.bubble)

    this.panel = document.createElement('div')
    this.panel.className = 'panel'
    this.panel.style.display = 'none'

    const messages = document.createElement('div')
    messages.className = 'messages'
    this.messages = messages

    const inputBar = document.createElement('div')
    inputBar.className = 'input'
    this.input = document.createElement('input')
    this.input.type = 'text'
    this.input.placeholder = 'Ask me about your documents...'
    const sendBtn = document.createElement('button')
    sendBtn.textContent = 'Send'
    inputBar.appendChild(this.input)
    inputBar.appendChild(sendBtn)

    this.panel.appendChild(messages)
    this.panel.appendChild(inputBar)
    this.shadow.appendChild(wrapper)
    this.shadow.appendChild(this.panel)

    this.bubble.addEventListener('click', () => this._toggle())
    sendBtn.addEventListener('click', () => this._send())
    this.input.addEventListener('keypress', (e) => { if (e.key === 'Enter') this._send() })
  }

  _toggle() {
    this.panel.style.display = this.panel.style.display === 'none' ? 'flex' : 'none'
  }

  _appendMessage(text, from = 'bot') {
    const el = document.createElement('div')
    el.className = from === 'user' ? 'msg-user' : 'msg-bot'
    el.textContent = text
    this.messages.appendChild(el)
    this.messages.scrollTop = this.messages.scrollHeight
  }

  async _send() {
    const text = this.input.value.trim()
    if (!text) return
    this._appendMessage(text, 'user')
    this.input.value = ''
    const url = `${this.backend}/api/chat`

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: this.history })
      })

      if (!res.ok) {
        this._appendMessage('Error: ' + res.statusText, 'bot')
        return
      }

      // Stream response
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let full = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        full += chunk
        // update last bot message (append or create)
        if (this._lastBot) {
          this._lastBot.textContent = full
        } else {
          this._lastBot = document.createElement('div')
          this._lastBot.className = 'msg-bot'
          this._lastBot.textContent = full
          this.messages.appendChild(this._lastBot)
        }
        this.messages.scrollTop = this.messages.scrollHeight
      }

      this.history.push({ user: text, bot: full })
      this._lastBot = null
    } catch (err) {
      this._appendMessage('Network error', 'bot')
      console.error(err)
    }
  }
}

// Auto-initialize
(function () {
  try {
    new RAGWidget()
  } catch (e) {
    console.error('Failed to initialize RAG widget', e)
  }
})()
