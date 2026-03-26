import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import axios from 'axios';

const EquationVisualizer = ({ equation }) => {
  const d3Container = useRef(null);
  const [error, setError] = useState(null);
  const [dataPoints, setDataPoints] = useState([]);

  // Fetch data when equation changes
  useEffect(() => {
    const fetchPoints = async () => {
      try {
        setError(null);
        const res = await axios.post('http://localhost:8001/api/plot/', {
          equation: equation,
          x_min: -10,
          x_max: 10,
          steps: 200
        });
        
        if (res.data.error) {
          setError(res.data.error);
        } else {
          setDataPoints(res.data.points);
        }
      } catch (err) {
        setError("Failed to communicate with backend server.");
        console.error(err);
      }
    };
    
    if (equation) {
      fetchPoints();
    }
  }, [equation]);

  // Render D3 visualization when dataPoints update
  useEffect(() => {
    if (dataPoints.length === 0 || !d3Container.current) return;

    // Clear previous SVG contents
    d3.select(d3Container.current).selectAll("*").remove();

    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    const width = 800 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    const svg = d3.select(d3Container.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Determine scale domains
    const xExtent = d3.extent(dataPoints, d => d.x);
    // Add a bit of padding to Y to make the graph look nicer
    const yExtent = d3.extent(dataPoints, d => d.y);
    const yPadding = (yExtent[1] - yExtent[0]) * 0.1 || 1; // avoid 0 padding for constants
    
    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPadding, yExtent[1] + yPadding])
      .range([height, 0]);

    // Add X axis
    const xAxis = svg.append("g")
      .attr("transform", `translate(0,${height / 2})`);
      
    // Create actual zero crossing if it's within range, else put it at bottom/top
    const zeroY = (0 >= yScale.domain()[0] && 0 <= yScale.domain()[1]) ? yScale(0) : height;
    xAxis.attr("transform", `translate(0,${zeroY})`)
      .call(d3.axisBottom(xScale));

    // Add Y axis
    const zeroX = (0 >= xScale.domain()[0] && 0 <= xScale.domain()[1]) ? xScale(0) : 0;
    const yAxis = svg.append("g")
      .attr("transform", `translate(${zeroX},0)`)
      .call(d3.axisLeft(yScale));

    // Style the axes gridlines slightly
    svg.selectAll(".tick line")
      .attr("opacity", 0.2)
      .attr("stroke-dasharray", "4,4");
      
    // Add horizontal grid lines
    svg.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(""))
      .attr("opacity", 0.1);

    // Add vertical grid lines
    svg.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(""))
      .attr("opacity", 0.1);

    // Line generator
    const line = d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.y))
      .curve(d3.curveMonotoneX);

    // Append path (the line itself)
    const path = svg.append("path")
      .datum(dataPoints)
      .attr("fill", "none")
      .attr("stroke", "#ff5722")
      .attr("stroke-width", 3)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .attr("d", line);

    // Animation: Line drawing effect
    const totalLength = path.node().getTotalLength();

    path
      .attr("stroke-dasharray", totalLength + " " + totalLength)
      .attr("stroke-dashoffset", totalLength)
      .transition()
      .duration(2000)
      .ease(d3.easeCubicInOut)
      .attr("stroke-dashoffset", 0);
      
    // Add tooltip / interactive circle
    const focus = svg.append("g")
        .append("circle")
        .style("fill", "#1e3c72")
        .attr("stroke", "#fff")
        .attr("r", 6)
        .style("opacity", 0);

    const tooltipText = svg.append("text")
        .style("opacity", 0)
        .attr("text-anchor", "left")
        .attr("alignment-baseline", "middle")
        .attr("font-family", "monospace")
        .attr("font-size", "14px")
        .attr("fill", "#333");

    // Interactive area
    svg.append("rect")
      .attr("width", width)
      .attr("height", height)
      .style("fill", "none")
      .style("pointer-events", "all")
      .on("mouseover", () => {
        focus.style("opacity", 1);
        tooltipText.style("opacity", 1);
      })
      .on("mouseout", () => {
        focus.style("opacity", 0);
        tooltipText.style("opacity", 0);
      })
      .on("mousemove", (event) => {
        const x0 = xScale.invert(d3.pointer(event)[0]);
        // Find closest point
        const bisect = d3.bisector(d => d.x).left;
        const i = bisect(dataPoints, x0, 1);
        const d0 = dataPoints[i - 1];
        const d1 = dataPoints[i];
        if (!d0 || !d1) return;
        const d = x0 - d0.x > d1.x - x0 ? d1 : d0;

        focus.attr("cx", xScale(d.x))
             .attr("cy", yScale(d.y));

        tooltipText
          .attr("x", xScale(d.x) + 15)
          .attr("y", yScale(d.y) - 15)
          .text(`(${d.x.toFixed(2)}, ${d.y.toFixed(2)})`);
      });

  }, [dataPoints]);

  return (
    <div className="visualizer-container">
      {error && <div className="error-message">{error}</div>}
      <svg
        className="d3-component"
        ref={d3Container}
      />
    </div>
  );
};

export default EquationVisualizer;
