import React, { useState } from 'react';
import './App.css';
import EquationVisualizer from './EquationVisualizer';

function App() {
  const [equation, setEquation] = useState('sin(x)');
  const [inputVal, setInputVal] = useState('sin(x)');

  const handleSubmit = (e) => {
    e.preventDefault();
    setEquation(inputVal);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Interactive Math Visualizer</h1>
        <p>Explore mathematics with interactive, animated graphs.</p>
        
        <form onSubmit={handleSubmit} className="equation-form">
          <span className="func-label">f(x) =</span>
          <input 
            type="text" 
            value={inputVal} 
            onChange={(e) => setInputVal(e.target.value)} 
            placeholder="e.g. x^2, sin(x), 2*x + 3"
            className="equation-input"
          />
          <button type="submit" className="plot-button">Plot & Animate</button>
        </form>
      </header>
      
      <main className="App-main">
        <EquationVisualizer equation={equation} />
      </main>
      
      <footer className="App-footer">
        <p>Powered by React, D3.js & Django</p>
      </footer>
    </div>
  );
}

export default App;
