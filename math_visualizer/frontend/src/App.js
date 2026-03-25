import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import MathGraph from './MathGraph';

function App() {
  const [equation, setEquation] = useState('x^2 + 2*x - 5');
  const [points, setPoints] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Range options
  const [xMin, setXMin] = useState(-10);
  const [xMax, setXMax] = useState(10);

  const fetchPoints = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/calculate/', {
        equation: equation,
        x_min: parseFloat(xMin),
        x_max: parseFloat(xMax),
      });

      if (response.data.status === 'success') {
        setPoints(response.data.points);
      } else {
        setError(response.data.error || 'Unknown error');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchPoints();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchPoints();
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Math Equation Visualizer</h1>
        <p>Type any algebraic expression (e.g., x^3, sin(x), exp(x), x**2 + 5*x)</p>
      </header>
      
      <main>
        <form onSubmit={handleSubmit} className="controls">
          <div className="input-group">
            <label>y = </label>
            <input 
              type="text" 
              value={equation}
              onChange={(e) => setEquation(e.target.value)}
              placeholder="x^2"
              required
            />
          </div>
          
          <div className="input-group inline">
            <label>x min:</label>
            <input 
              type="number" 
              value={xMin}
              onChange={(e) => setXMin(e.target.value)}
              step="1"
            />
          </div>
          <div className="input-group inline">
            <label>x max:</label>
            <input 
              type="number" 
              value={xMax}
              onChange={(e) => setXMax(e.target.value)}
              step="1"
            />
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Plotting...' : 'Plot'}
          </button>
        </form>

        {error && <div className="error-box">Error: {error}</div>}

        <div className="graph-section">
          {points.length > 0 ? (
            <MathGraph points={points} />
          ) : (
            !loading && <p>No data to display.</p>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
