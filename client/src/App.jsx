import { useState, useEffect } from 'react'
import axios from 'axios'
import './index.css'

const api = axios.create({ 
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

function App() {
  const [platform, setPlatform] = useState('LinkedIn')
  const [prompt, setPrompt] = useState('')
  const [content, setContent] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [posting, setPosting] = useState(false)
  const [status, setStatus] = useState({ linkedin: false, facebook: false, instagram: false })
  const [config, setConfig] = useState({ linkedin: false, facebook: false, instagram: false })
  const [message, setMessage] = useState('')
  const [msgType, setMsgType] = useState('info')

  // Manual token states
  const [showManual, setShowManual] = useState(false)
  const [manualPlatform, setManualPlatform] = useState('facebook')
  const [manualToken, setManualToken] = useState('')
  const [manualPageId, setManualPageId] = useState('')
  const [manualIgId, setManualIgId] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const connected = params.get('connected')
    const error = params.get('error')
    if (connected) {
      showMessage('✅ ' + connected.charAt(0).toUpperCase() + connected.slice(1) + ' connected successfully!', 'success')
      window.history.replaceState({}, '', window.location.pathname)
    }
    if (error) {
      showMessage('❌ ' + decodeURIComponent(error), 'error')
      window.history.replaceState({}, '', window.location.pathname)
    }
    fetchStatus()
    fetchConfig()
  }, [])

  const showMessage = (text, type) => {
    setMessage(text)
    setMsgType(type || 'info')
    setTimeout(() => setMessage(''), 10000)
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

  const handleConnect = (p) => {
    if (p === 'linkedin') {
      window.location.href = 'http://localhost:8000/auth/linkedin'
    } else if (p === 'facebook') {
      window.location.href = 'http://localhost:8000/auth/facebook'
    } else if (p === 'instagram') {
      window.location.href = 'http://localhost:8000/auth/instagram'
    }
  }

  const handleDisconnect = async (p) => {
    try {
      await api.post('/disconnect/' + p)
      fetchStatus()
      showMessage(p.charAt(0).toUpperCase() + p.slice(1) + ' Disconnected', 'info')
    } catch (e) {
      showMessage('❌ Disconnect failed', 'error')
    }
  }

  const handleManualToken = async () => {
    if (!manualToken.trim()) {
      showMessage('❌ Token required!', 'error')
      return
    }
    try {
      const payload = {
        platform: manualPlatform,
        token: manualToken,
        page_id: manualPageId,
        ig_user_id: manualIgId,
      }
      const res = await api.post('/manual-token', payload)
      if (res.data.success) {
        showMessage('✅ ' + res.data.message, 'success')
        setShowManual(false)
        setManualToken('')
        setManualPageId('')
        setManualIgId('')
        fetchStatus()
      }
    } catch (e) {
      showMessage('❌ Failed to save token', 'error')
    }
  }

  const handlePost = async () => {
    const pKey = platform.toLowerCase()
    if (pKey === 'instagram' ? !status.instagram : !status[pKey]) {
      showMessage('❌ Connect ' + platform + ' first!', 'error')
      return
    }
    if (pKey === 'instagram' && !imageUrl.trim()) {
      showMessage('❌ Instagram requires an image URL!', 'error')
      return
    }
    setPosting(true)
    setMessage('')

    try {
      const res = await api.post('/post/' + pKey, { 
        content: content,
        image_url: imageUrl 
      })

      if (res.data && res.data.success) {
        showMessage('✅ ' + res.data.message, 'success')
      } else {
        showMessage('✅ Posted successfully!', 'success')
      }
    } catch (e) {
      console.error('Post error:', e)

      if (e.response) {
        const errorDetail = e.response.data?.detail || e.response.data?.message || JSON.stringify(e.response.data)
        showMessage('❌ ' + errorDetail, 'error')
      } else if (e.request) {
        showMessage('⚠️ Post may have succeeded but response was lost. Check your social media.', 'info')
      } else {
        showMessage('❌ ' + e.message, 'error')
      }
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
    btnSmall: { padding: '6px 16px', borderRadius: '6px', border: '1px solid var(--accent-border)', background: 'var(--accent-bg)', color: 'var(--accent)', fontSize: '13px', fontWeight: '600', cursor: 'pointer' },
    btnRed: { padding: '6px 16px', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#ef4444', fontSize: '13px', fontWeight: '600', cursor: 'pointer' },
    msg: { maxWidth: '640px', margin: '0 auto 20px', padding: '12px 16px', borderRadius: '8px', border: '1px solid', fontSize: '14px', textAlign: 'left' },
    content: { background: 'var(--code-bg)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', fontSize: '15px', lineHeight: '1.6', whiteSpace: 'pre-wrap', color: 'var(--text-h)', marginBottom: '16px' },
    postBtn: { width: '100%', padding: '12px', borderRadius: '8px', border: '2px solid var(--accent)', background: 'transparent', color: 'var(--accent)', fontSize: '16px', fontWeight: '600', cursor: 'pointer' },
    manualBox: { background: 'rgba(139,92,246,0.05)', border: '1px dashed var(--accent)', borderRadius: '12px', padding: '20px', margin: '0 auto 20px', maxWidth: '640px', width: '100%', boxSizing: 'border-box' },
    linkBtn: { background: 'none', border: 'none', color: 'var(--accent)', textDecoration: 'underline', cursor: 'pointer', fontSize: '13px', padding: '0' }
  }

  const msgColor = msgType === 'success' ? { bg: 'rgba(34,197,94,0.1)', bd: 'rgba(34,197,94,0.5)' } : msgType === 'error' ? { bg: 'rgba(239,68,68,0.1)', bd: 'rgba(239,68,68,0.5)' } : { bg: 'var(--accent-bg)', bd: 'var(--accent-border)' }

  return (
    <>
      <h1>AI Social Media Automator</h1>
      <p style={{ margin: '0 0 32px', color: 'var(--text)' }}>Generate & post content directly to your social media</p>

      <section style={s.box}>
        <div style={s.field}>
          <label style={s.label}>Select Platform:</label>
          <select value={platform} onChange={e => setPlatform(e.target.value)} style={s.select}>
            <option>LinkedIn</option>
            <option>Instagram</option>
            <option>Facebook</option>
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
              <><span style={s.ok}>✅ Connected</span><button onClick={() => handleDisconnect('linkedin')} style={s.btnRed}>Disconnect</button></>
            ) : config.linkedin ? (
              <button onClick={() => handleConnect('linkedin')} style={s.btnSmall}>Connect</button>
            ) : (
              <span style={s.off}>⚠️ Not Configured</span>
            )}
          </div>
        </div>

        <div style={s.row}>
          <span style={s.name}>🟠 Facebook</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {status.facebook ? (
              <><span style={s.ok}>✅ Connected</span><button onClick={() => handleDisconnect('facebook')} style={s.btnRed}>Disconnect</button></>
            ) : config.facebook ? (
              <button onClick={() => handleConnect('facebook')} style={s.btnSmall}>Connect</button>
            ) : (
              <span style={s.off}>⚠️ Not Configured</span>
            )}
          </div>
        </div>

        <div style={{ ...s.row, borderBottom: 'none' }}>
          <span style={s.name}>🟣 Instagram</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {status.instagram ? (
              <><span style={s.ok}>✅ Connected</span><button onClick={() => handleDisconnect('instagram')} style={s.btnRed}>Disconnect</button></>
            ) : config.instagram ? (
              <button onClick={() => handleConnect('instagram')} style={s.btnSmall}>Connect</button>
            ) : (
              <span style={s.off}>⚠️ Not Configured</span>
            )}
          </div>
        </div>

        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          <button onClick={() => setShowManual(!showManual)} style={s.linkBtn}>
            {showManual ? 'Hide Manual Token Entry' : '⚡ Use Manual Token (Bypass OAuth)'}
          </button>
        </div>
      </section>

      {showManual && (
        <section style={s.manualBox}>
          <h3 style={{ margin: '0 0 12px', color: 'var(--accent)' }}>⚡ Manual Token Entry</h3>
          <p style={{ fontSize: '13px', color: 'var(--text)', marginBottom: '12px' }}>
            Use this if OAuth fails. Get token from{' '}
            <a href="https://developers.facebook.com/tools/explorer" target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>
              Graph API Explorer
            </a>
          </p>
          
          <div style={s.field}>
            <label style={s.label}>Platform:</label>
            <select value={manualPlatform} onChange={e => setManualPlatform(e.target.value)} style={s.select}>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="linkedin">LinkedIn</option>
            </select>
          </div>

          <div style={s.field}>
            <label style={s.label}>Access Token:</label>
            <input 
              value={manualToken} 
              onChange={e => setManualToken(e.target.value)} 
              placeholder="Paste token here..." 
              style={s.input} 
            />
          </div>

          {manualPlatform === 'facebook' && (
            <div style={s.field}>
              <label style={s.label}>Page ID:</label>
              <input 
                value={manualPageId} 
                onChange={e => setManualPageId(e.target.value)} 
                placeholder="Your Facebook Page ID" 
                style={s.input} 
              />
            </div>
          )}

          {manualPlatform === 'instagram' && (
            <div style={s.field}>
              <label style={s.label}>Instagram User ID:</label>
              <input 
                value={manualIgId} 
                onChange={e => setManualIgId(e.target.value)} 
                placeholder="Your Instagram User ID" 
                style={s.input} 
              />
            </div>
          )}

          {manualPlatform === 'linkedin' && (
            <div style={s.field}>
              <label style={s.label}>Person ID (optional):</label>
              <input 
                value={manualPageId} 
                onChange={e => setManualPageId(e.target.value)} 
                placeholder="LinkedIn Person ID" 
                style={s.input} 
              />
            </div>
          )}

          <button onClick={handleManualToken} style={s.btn}>
            💾 Save Token
          </button>
        </section>
      )}

      {message && (
        <div style={{ ...s.msg, background: msgColor.bg, borderColor: msgColor.bd }}>{message}</div>
      )}

      {content && (
        <section style={s.box}>
          <h2 style={{ margin: '0 0 16px' }}>Generated Content</h2>
          <div style={s.content}>{content}</div>

          {platform === 'Instagram' && (
            <div style={s.field}>
              <label style={s.label}>📸 Image URL (Required for Instagram):</label>
              <input 
                value={imageUrl} 
                onChange={e => setImageUrl(e.target.value)} 
                placeholder="https://example.com/your-image.jpg" 
                style={s.input} 
              />
            </div>
          )}

          <button onClick={handlePost} disabled={posting} style={{ ...s.postBtn, opacity: posting ? 0.5 : 1 }}>
            {posting ? '⏳ Posting...' : '🚀 Post to ' + platform}
          </button>
        </section>
      )}
    </>
  )
}

export default App