import React, { useState } from 'react';
import axios from 'axios';
import Graph from './Graph';
import './App.css';

function App() {
  const [equation, setEquation] = useState('sin(x) * x');
  const [xMin, setXMin] = useState('-10');
  const [xMax, setXMax] = useState('10');
  const [step, setStep] = useState('0.1');
  
  const [points, setPoints] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const response = await axios.post('http://localhost:8000/api/calculate/', {
        equation,
        x_min: parseFloat(xMin),
        x_max: parseFloat(xMax),
        step: parseFloat(step)
      });
      
      if (response.data.status === 'success') {
        setPoints(response.data.points);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError('Failed to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Math Equation Visualizer</h1>
      </header>
      <main className="container">
        <form onSubmit={handleSubmit} className="equation-form">
          <div className="form-group">
            <label htmlFor="equation">f(x) = </label>
            <input 
              type="text" 
              id="equation" 
              value={equation} 
              onChange={(e) => setEquation(e.target.value)}
              placeholder="e.g. x**2 + 2*x"
              required 
            />
          </div>
          <div className="form-row">
            <div className="form-group small">
              <label htmlFor="xMin">x Min</label>
              <input 
                type="number" 
                id="xMin" 
                value={xMin} 
                onChange={(e) => setXMin(e.target.value)}
                required 
              />
            </div>
            <div className="form-group small">
              <label htmlFor="xMax">x Max</label>
              <input 
                type="number" 
                id="xMax" 
                value={xMax} 
                onChange={(e) => setXMax(e.target.value)}
                required 
              />
            </div>
            <div className="form-group small">
              <label htmlFor="step">Step</label>
              <input 
                type="number" 
                id="step" 
                step="0.01"
                min="0.01"
                value={step} 
                onChange={(e) => setStep(e.target.value)}
                required 
              />
            </div>
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Calculating...' : 'Plot Graph'}
          </button>
        </form>
        
        {error && <div className="error-message">{error}</div>}
        
        {points.length > 0 && <Graph points={points} />}
        
        <div className="tips">
          <p><strong>Tips for writing equations:</strong></p>
          <ul>
            <li>Use <code>**</code> for exponents (e.g., <code>x**2</code> for x²)</li>
            <li>Use <code>*</code> for multiplication (e.g., <code>2*x</code> instead of 2x)</li>
            <li>Available functions: <code>sin(x)</code>, <code>cos(x)</code>, <code>tan(x)</code>, <code>exp(x)</code>, <code>log(x)</code></li>
          </ul>
        </div>
      </main>
    </div>
  );
}

export default App;
