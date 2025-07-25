// App.js
import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setResponse('');

    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setResponse(data.answer);
    } catch (err) {
      setResponse('Error: Unable to get a response.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>CAM Chatbot</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
      <div className="response response-box">
        {response && <pre>{response}</pre>}
      </div>
    </div>
  );
}

export default App;
