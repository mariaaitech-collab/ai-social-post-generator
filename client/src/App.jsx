import { useState, useEffect } from 'react'
import axios from 'axios'
import './index.css'

const api = axios.create({ baseURL: 'http://localhost:8000' })

function App() {
  const [platform, setPlatform] = useState('LinkedIn')
  const [prompt, setPrompt] = useState('')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [posting, setPosting] = useState(false)
  const [status, setStatus] = useState({ linkedin: false, facebook: false, instagram: false })
  const [config, setConfig] = useState({ linkedin: false, facebook: false, instagram: false })
  const [message, setMessage] = useState('')
  const [msgType, setMsgType] = useState('info')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const connected = params.get('connected')
    const error = params.get('error')
    if (connected) {
      showMessage('✅ ' + connected + ' connected successfully!', 'success')
      window.history.replaceState({}, '', window.location.pathname)
    }
    if (error) {
      showMessage('❌ ' + error, 'error')
      window.history.replaceState({}, '', window.location.pathname)
    }
    fetchStatus()
    fetchConfig()
  }, [])

  const showMessage = (text, type) => {
    setMessage(text)
    setMsgType(type || 'info')
    setTimeout(() => setMessage(''), 8000)
  }

  const fetchStatus = async () => {
    try {
      const res = await api.get('/status')
      setStatus(res.data)
    } catch (e) { console.error(e) }
  }

  const fetchConfig = async () => {
    try {
      const res = await api.get('/config')
      setConfig(res.data)
    } catch (e) { console.error(e) }
  }

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setMessage('')
    try {
      const res = await api.post('/generate', { prompt, platform })
      if (res.data.content.startsWith('Error:')) {
        showMessage(res.data.content, 'error')
      } else {
        setContent(res.data.content)
      }
    } catch (e) {
      showMessage('❌ Network Error', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleConnect = () => {
    window.open('http://localhost:8000/auth/linkedin', '_blank')
  }

  const handleDisconnect = async () => {
    try {
      await api.post('/disconnect/linkedin')
      fetchStatus()
      showMessage('LinkedIn Disconnected', 'info')
    } catch (e) {
      showMessage('❌ Disconnect failed', 'error')
    }
  }

  const handlePost = async () => {
    if (!status.linkedin) {
      showMessage('❌ Connect LinkedIn first!', 'error')
      return
    }
    setPosting(true)
    setMessage('')
    try {
      const res = await api.post('/post/linkedin', { content })
      showMessage(res.data.message, 'success')
    } catch (e) {
      showMessage('❌ ' + (e.response?.data?.detail || e.message), 'error')
    } finally {
      setPosting(false)
    }
  }

  const s = {
    box: { background: 'var(--social-bg)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', margin: '0 auto 20px', maxWidth: '640px', width: '100%', boxSizing: 'border-box', textAlign: 'left' },
    field: { marginBottom: '16px' },
    label: { display: 'block', marginBottom: '6px', fontSize: '14px', fontWeight: '600', color: 'var(--text-h)' },
    select: { width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-h)', fontSize: '16px', boxSizing: 'border-box' },
    input: { width: '100%', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-h)', fontSize: '16px', boxSizing: 'border-box', outline: 'none' },
    btn: { width: '100%', padding: '12px', borderRadius: '8px', border: 'none', background: 'var(--accent)', color: '#fff', fontSize: '16px', fontWeight: '600', cursor: 'pointer' },
    row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' },
    name: { fontSize: '16px', fontWeight: '500', color: 'var(--text-h)' },
    ok: { fontSize: '13px', color: '#22c55e', fontWeight: '500' },
    off: { fontSize: '13px', color: '#f59e0b', fontWeight: '500' },
    btnSmall: { padding: '6px 16px', borderRadius: '6px', border: '1px solid ' + 'var(--accent-border)', background: 'var(--accent-bg)', color: 'var(--accent)', fontSize: '13px', fontWeight: '600', cursor: 'pointer' },
    btnRed: { padding: '6px 16px', borderRadius: '6px', border: '1px solid ' + 'rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#ef4444', fontSize: '13px', fontWeight: '600', cursor: 'pointer' },
    msg: { maxWidth: '640px', margin: '0 auto 20px', padding: '12px 16px', borderRadius: '8px', border: '1px solid', fontSize: '14px', textAlign: 'left' },
    content: { background: 'var(--code-bg)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', fontSize: '15px', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: 'var(--text-h)', marginBottom: '16px' },
    postBtn: { width: '100%', padding: '12px', borderRadius: '8px', border: '2px solid var(--accent)', background: 'transparent', color: 'var(--accent)', fontSize: '16px', fontWeight: '600', cursor: 'pointer' }
  }

  const msgColor = msgType === 'success' ? { bg: 'rgba(34,197,94,0.1)', bd: 'rgba(34,197,94,0.5)' } : msgType === 'error' ? { bg: 'rgba(239,68,68,0.1)', bd: 'rgba(239,68,68,0.5)' } : { bg: 'var(--accent-bg)', bd: 'var(--accent-border)' }

  return (
    <>
      <h1>AI Social Media Automator</h1>
      <p style={{ margin: '0 0 32px', color: 'var(--text)' }}>Generate & post content directly to LinkedIn</p>

      <section style={s.box}>
        <div style={s.field}>
          <label style={s.label}>Select Platform:</label>
          <select value={platform} onChange={e => setPlatform(e.target.value)} style={s.select}>
            <option>LinkedIn</option>
          </select>
        </div>
        <div style={s.field}>
          <label style={s.label}>What is the post about?</label>
          <input value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleGenerate()} placeholder="e.g. AI for women, tech trends..." style={s.input} />
        </div>
        <button onClick={handleGenerate} disabled={loading || !prompt.trim()} style={{ ...s.btn, opacity: loading || !prompt.trim() ? 0.5 : 1 }}>
          {loading ? '⏳ Generating...' : '🔄 Generate Content'}
        </button>
      </section>

      <section style={s.box}>
        <h2 style={{ margin: '0 0 16px' }}>Connected Accounts</h2>
        <div style={s.row}>
          <span style={s.name}>🔵 LinkedIn</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {status.linkedin ? (
              <><span style={s.ok}>✅ Connected</span><button onClick={handleDisconnect} style={s.btnRed}>Disconnect</button></>
            ) : config.linkedin ? (
              <button onClick={handleConnect} style={s.btnSmall}>Connect</button>
            ) : (
              <span style={s.off}>⚠️ Not Configured</span>
            )}
          </div>
        </div>
      </section>

      {message && (
        <div style={{ ...s.msg, background: msgColor.bg, borderColor: msgColor.bd }}>{message}</div>
      )}

      {content && (
        <section style={s.box}>
          <h2 style={{ margin: '0 0 16px' }}>Generated Content</h2>
          <div style={s.content}>{content}</div>
          <button onClick={handlePost} disabled={posting} style={{ ...s.postBtn, opacity: posting ? 0.5 : 1 }}>
            {posting ? '⏳ Posting...' : '🚀 Post to LinkedIn'}
          </button>
        </section>
      )}
    </>
  )
}

export default App