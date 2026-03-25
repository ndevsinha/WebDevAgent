import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const MathGraph = ({ points }) => {
  const d3Container = useRef(null);

  useEffect(() => {
    if (points && points.length > 0 && d3Container.current) {
      // Clear previous graph
      d3.select(d3Container.current).selectAll('*').remove();

      // Setup dimensions
      const margin = { top: 20, right: 30, bottom: 40, left: 40 };
      const width = 600 - margin.left - margin.right;
      const height = 400 - margin.top - margin.bottom;

      // Append SVG object to the container
      const svg = d3
        .select(d3Container.current)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Determine domains
      const xExtent = d3.extent(points, (d) => d.x);
      const yExtent = d3.extent(points, (d) => d.y);

      // Add a bit of padding to the y domain so the line doesn't touch the top/bottom
      const yPadding = (yExtent[1] - yExtent[0]) * 0.1 || 1;
      
      const xScale = d3
        .scaleLinear()
        .domain([xExtent[0], xExtent[1]])
        .range([0, width]);

      const yScale = d3
        .scaleLinear()
        .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
        .range([height, 0]);

      // Draw X axis
      const xAxis = svg
        .append('g')
        .attr('transform', `translate(0,${yScale(0)})`) // Place it at Y=0
        .call(d3.axisBottom(xScale));

      // Draw Y axis
      const yAxis = svg
        .append('g')
        .attr('transform', `translate(${xScale(0)},0)`) // Place it at X=0
        .call(d3.axisLeft(yScale));

      // Handle cases where the origin is not inside the graph viewport
      if (yScale(0) < 0 || yScale(0) > height) {
        xAxis.attr('transform', `translate(0,${height})`);
      }
      if (xScale(0) < 0 || xScale(0) > width) {
        yAxis.attr('transform', `translate(0,0)`);
      }

      // Add the line
      const line = d3
        .line()
        .x((d) => xScale(d.x))
        .y((d) => yScale(d.y))
        // Filter out extreme values that stretch the graph too much if any
        .defined((d) => !isNaN(d.y) && isFinite(d.y));

      svg
        .append('path')
        .datum(points)
        .attr('fill', 'none')
        .attr('stroke', '#4facfe')
        .attr('stroke-width', 2.5)
        .attr('d', line);

      // Add gridlines (optional but good for math)
      svg.append('g')
        .attr('class', 'grid')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(''))
        .attr('stroke-opacity', 0.1);

      svg.append('g')
        .attr('class', 'grid')
        .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(''))
        .attr('stroke-opacity', 0.1);

    }
  }, [points]);

  return (
    <div
      className="graph-container"
      ref={d3Container}
      style={{
        background: '#fff',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        padding: '10px',
        display: 'inline-block'
      }}
    />
  );
};

export default MathGraph;
