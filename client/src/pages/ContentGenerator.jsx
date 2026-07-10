import { useState } from 'react';
import api from '../services/api';

export default function ContentGenerator() {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('LinkedIn'); // Default platform
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false); // Loading state

  const generateContent = async () => {
    setLoading(true);
    setResult('Generating brilliant content... Please wait ⏳');
    try {
      // Backend ko topic aur platform dono bhej rahe hain
      const response = await api.post('/generate', { prompt: topic, platform: platform });
      setResult(response.data.content);
    } catch (error) {
      console.error("Error generating content:", error);
      setResult("Error! Make sure your backend is running and API key is correct.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '40px', maxWidth: '600px', margin: '0 auto', textAlign: 'center', fontFamily: 'sans-serif' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '10px' }}>AI Social Media Automator</h1>
      <p style={{ marginBottom: '20px', color: '#666' }}>Generate tailored posts for your favorite platforms using Google Gemini AI.</p>
      
      <div style={{ marginBottom: '15px', textAlign: 'left' }}>
        <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Select Platform:</label>
        <select 
          value={platform} 
          onChange={(e) => setPlatform(e.target.value)}
          style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        >
          <option value="LinkedIn">LinkedIn</option>
          <option value="Instagram">Instagram</option>
          <option value="Facebook">Facebook</option>
        </select>
      </div>

      <div style={{ marginBottom: '15px', textAlign: 'left' }}>
        <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>What is the post about?</label>
        <textarea 
          style={{ width: '100%', height: '100px', padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., ai for women..." 
        />
      </div>

      <button 
        onClick={generateContent} 
        disabled={loading || !topic}
        style={{ 
          padding: '12px 24px', 
          backgroundColor: loading || !topic ? '#ccc' : '#007bff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '5px',
          cursor: loading || !topic ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
          width: '100%'
        }}>
        {loading ? 'Generating...' : 'Generate Content 🚀'}
      </button>

      <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f9f9f9', border: '1px solid #eee', borderRadius: '8px', minHeight: '100px', whiteSpace: 'pre-wrap', textAlign: 'left', color: 'black' }}>
        {result || <span style={{ color: '#aaa' }}>Your AI-generated post will appear here...</span>}
      </div>
    </div>
  );
}