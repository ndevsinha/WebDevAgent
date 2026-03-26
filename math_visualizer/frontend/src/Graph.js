import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

const Graph = ({ points }) => {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!points || points.length === 0) return;

    // Sort points by X axis for correct bisecting and rendering
    const sortedPoints = [...points].sort((a, b) => a.x - b.x);

    const width = 850;
    const height = 500;
    const margin = { top: 40, right: 40, bottom: 50, left: 60 };

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous drawing

    // Style the main SVG container
    svg.attr('width', width).attr('height', height)
       .style('background', '#ffffff')
       .style('border-radius', '12px')
       .style('box-shadow', '0 8px 24px rgba(0,0,0,0.12)')
       .style('display', 'block');

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const xExtent = d3.extent(sortedPoints, d => d.x);
    const yExtent = d3.extent(sortedPoints, d => d.y);

    // Padding for extents to ensure lines don't hit the very edge
    const yPad = (yExtent[1] - yExtent[0]) * 0.1 || 1;
    const xPad = (xExtent[1] - xExtent[0]) * 0.05 || 1;

    const xScale = d3.scaleLinear()
      .domain([xExtent[0] - xPad, xExtent[1] + xPad])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .range([innerHeight, 0]);

    // Create tick generators
    const xAxis = d3.axisBottom(xScale).ticks(12);
    const yAxis = d3.axisLeft(yScale).ticks(10);

    // 1. Draw Gridlines
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(12).tickSize(-innerHeight).tickFormat(''))
      .attr('color', '#e9ecef')
      .attr('stroke-opacity', 0.6);

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).ticks(10).tickSize(-innerWidth).tickFormat(''))
      .attr('color', '#e9ecef')
      .attr('stroke-opacity', 0.6);

    // 2. Draw Axes (0-lines) and Values
    // Calculate where the 0 intercept should be, bound within the graph area
    const xZero = Math.max(0, Math.min(innerWidth, xScale(0)));
    const yZero = Math.max(0, Math.min(innerHeight, yScale(0)));

    const xAxisG = g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${yZero})`)
      .call(xAxis);

    const yAxisG = g.append('g')
      .attr('class', 'y-axis')
      .attr('transform', `translate(${xZero},0)`)
      .call(yAxis);

    // Beautify Axis Text and Lines
    g.selectAll('.x-axis text, .y-axis text')
      .attr('font-size', '13px')
      .attr('font-weight', '500')
      .attr('fill', '#495057')
      .style('text-shadow', '1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff'); // Make text readable over grid/lines

    g.selectAll('.x-axis path, .y-axis path')
      .attr('stroke', '#adb5bd')
      .attr('stroke-width', 2);

    g.selectAll('.x-axis line, .y-axis line')
      .attr('stroke', '#adb5bd');

    // 3. Define the line generator
    const line = d3.line()
      .x(d => xScale(d.x))
      .y(d => yScale(d.y))
      .curve(d3.curveMonotoneX); // Smooth the line

    // 4. Add drop shadow filter for the graph line
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', 'shadow').attr('x', '-20%').attr('y', '-20%').attr('width', '140%').attr('height', '140%');
    filter.append('feDropShadow')
        .attr('dx', '0')
        .attr('dy', '4')
        .attr('stdDeviation', '4')
        .attr('flood-color', '#007bff')
        .attr('flood-opacity', '0.4');

    // 5. Draw the function line
    const path = g.append('path')
      .datum(sortedPoints)
      .attr('fill', 'none')
      .attr('stroke', '#007bff')
      .attr('stroke-width', 3)
      .attr('d', line)
      .style('filter', 'url(#shadow)');

    // Animate the line drawing
    const totalLength = path.node().getTotalLength();
    path
      .attr("stroke-dasharray", totalLength + " " + totalLength)
      .attr("stroke-dashoffset", totalLength)
      .transition()
      .duration(1200)
      .ease(d3.easeCubicOut)
      .attr("stroke-dashoffset", 0);

    // 6. Interactivity (Crosshair, Hover Tooltip)
    const focus = g.append('g').style('display', 'none');

    const crosshairX = focus.append('line')
      .attr('stroke', '#adb5bd')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '5,5');

    const crosshairY = focus.append('line')
      .attr('stroke', '#adb5bd')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '5,5');

    const focusCircle = focus.append('circle')
      .attr('r', 6)
      .attr('fill', '#ffffff')
      .attr('stroke', '#007bff')
      .attr('stroke-width', 2.5)
      .style('filter', 'drop-shadow(0px 2px 2px rgba(0,0,0,0.2))');

    // Dynamic Tooltip setup
    const tooltip = d3.select(containerRef.current)
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', 'rgba(33, 37, 41, 0.95)')
      .style('color', '#f8f9fa')
      .style('padding', '10px 14px')
      .style('border-radius', '8px')
      .style('font-size', '14px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('transform', 'translate(-50%, -100%)')
      .style('margin-top', '-15px')
      .style('box-shadow', '0 4px 12px rgba(0,0,0,0.15)')
      .style('z-index', '10')
      .style('white-space', 'nowrap');

    const bisect = d3.bisector(d => d.x).left;

    // Invisible overlay to catch mouse events
    g.append('rect')
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .attr('fill', 'none')
      .attr('pointer-events', 'all')
      .on('mouseover', () => {
        focus.style('display', null);
        tooltip.style('visibility', 'visible');
      })
      .on('mouseout', () => {
        focus.style('display', 'none');
        tooltip.style('visibility', 'hidden');
      })
      .on('mousemove', (event) => {
        const x0 = xScale.invert(d3.pointer(event)[0]);
        const i = bisect(sortedPoints, x0, 1);
        const d0 = sortedPoints[i - 1];
        const d1 = sortedPoints[i];
        
        if (!d0 || !d1) return;
        
        // Find closest point
        const d = x0 - d0.x > d1.x - x0 ? d1 : d0;
        
        const cx = xScale(d.x);
        const cy = yScale(d.y);

        // Move circle
        focusCircle.attr('cx', cx).attr('cy', cy);

        // Update crosshairs
        crosshairX.attr('x1', cx).attr('y1', 0).attr('x2', cx).attr('y2', innerHeight);
        crosshairY.attr('x1', 0).attr('y1', cy).attr('x2', innerWidth).attr('y2', cy);

        // Position tooltip relative to the wrapper div
        const tooltipX = cx + margin.left;
        const tooltipY = cy + margin.top;

        tooltip
          .html(`<div style="margin-bottom:4px"><span style="color:#adb5bd">x:</span> ${d.x.toFixed(4)}</div>
                 <div><span style="color:#adb5bd">f(x):</span> <span style="color:#4dabf7">${d.y.toFixed(4)}</span></div>`)
          .style('left', `${tooltipX}px`)
          .style('top', `${tooltipY}px`);
      });

      // Cleanup tooltip on unmount or re-render
      return () => {
        d3.select(containerRef.current).selectAll('.d3-tooltip').remove();
      }

  }, [points]);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '30px', marginBottom: '30px' }}>
      <div ref={containerRef} style={{ position: 'relative', display: 'inline-block' }}>
        <svg ref={svgRef}></svg>
      </div>
    </div>
  );
};

export default Graph;
