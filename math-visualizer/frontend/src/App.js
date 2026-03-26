import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import './App.css';

function App() {
  const [expression, setExpression] = useState('sin(x) * x');
  const [data, setData] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [xMin, setXMin] = useState(-10);
  const [xMax, setXMax] = useState(10);
  const svgRef = useRef();

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:8005/api/evaluate/', {
        expression: expression,
        x_min: parseFloat(xMin),
        x_max: parseFloat(xMax),
        num_points: 500
      });
      if (response.data.status === 'success') {
        setData(response.data.data);
      } else {
        setError(response.data.message || 'Error fetching data');
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'An error occurred');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (data.length > 0) {
      drawChart();
    }
  }, [data]);

  const drawChart = () => {
    const margin = { top: 30, right: 30, bottom: 50, left: 50 };
    const width = 800 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous

    const container = svg
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
      .domain([d3.min(data, d => d.x), d3.max(data, d => d.x)])
      .range([0, width]);

    const yMin = d3.min(data, d => d.y);
    const yMax = d3.max(data, d => d.y);
    const yPadding = (yMax - yMin) * 0.1 || 1;

    const y = d3.scaleLinear()
      .domain([yMin - yPadding, yMax + yPadding])
      .range([height, 0]);

    // Grid lines
    const makeXGridlines = () => d3.axisBottom(x).ticks(10);
    const makeYGridlines = () => d3.axisLeft(y).ticks(10);

    container.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(makeXGridlines().tickSize(-height).tickFormat(''))
      .style('stroke', '#444')
      .style('stroke-opacity', 0.2);

    container.append('g')
      .attr('class', 'grid')
      .call(makeYGridlines().tickSize(-width).tickFormat(''))
      .style('stroke', '#444')
      .style('stroke-opacity', 0.2);

    // Axes
    const xAxis = d3.axisBottom(x);
    const yAxis = d3.axisLeft(y);

    container.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(xAxis)
      .attr('class', 'axis');

    container.append('g')
      .call(yAxis)
      .attr('class', 'axis');
      
    // 0 Lines
    if (yMin < 0 && yMax > 0) {
      container.append('line')
        .attr('x1', 0)
        .attr('x2', width)
        .attr('y1', y(0))
        .attr('y2', y(0))
        .attr('stroke', '#888')
        .attr('stroke-width', 1);
    }
    
    if (d3.min(data, d => d.x) < 0 && d3.max(data, d => d.x) > 0) {
      container.append('line')
        .attr('x1', x(0))
        .attr('x2', x(0))
        .attr('y1', 0)
        .attr('y2', height)
        .attr('stroke', '#888')
        .attr('stroke-width', 1);
    }

    // Line generator
    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveMonotoneX);

    container.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', '#00ffcc')
      .attr('stroke-width', 2.5)
      .attr('d', line);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchData();
  };

  return (
    <div className="App dark-theme">
      <header className="header">
        <h1>Maths Equation Visualizer</h1>
      </header>
      <main className="main-content">
        <form onSubmit={handleSubmit} className="controls-form">
          <div className="input-group">
            <label>f(x) =</label>
            <input 
              type="text" 
              value={expression} 
              onChange={(e) => setExpression(e.target.value)} 
              placeholder="e.g. x**2, sin(x), x + 5"
              className="expr-input"
            />
          </div>
          <div className="input-row">
            <div className="input-group sm">
              <label>X Min</label>
              <input 
                type="number" 
                value={xMin} 
                onChange={(e) => setXMin(e.target.value)} 
              />
            </div>
            <div className="input-group sm">
              <label>X Max</label>
              <input 
                type="number" 
                value={xMax} 
                onChange={(e) => setXMax(e.target.value)} 
              />
            </div>
            <button type="submit" disabled={loading} className="btn-plot">
              {loading ? 'Plotting...' : 'Plot Equation'}
            </button>
          </div>
        </form>

        {error && <div className="error-box">{error}</div>}

        <div className="graph-container">
          <svg ref={svgRef}></svg>
        </div>
      </main>
    </div>
  );
}

export default App;
