import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';

export default function PartVisualization({ extractedData }) {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    // Trigger animation after mount
    setTimeout(() => setAnimate(true), 300);
  }, []);

  if (!extractedData) return null;

  // Use the exact parameters extracted by the AI
  const analysis = extractedData.diagram_analysis || {};
  const dims = extractedData.dimensions || {};
  
  const holes = analysis.hole_count || 0;
  const slots = analysis.slot_count || 0;
  
  // Create a relative aspect ratio for the SVG box
  const aspect = analysis.aspect_ratio || 1.5;
  const width = 400;
  const height = width / Math.max(1, Math.min(aspect, 3)); 

  // Generate mock positions for holes
  const renderHoles = () => {
    const circles = [];
    const positions = [
      { cx: width * 0.2, cy: height * 0.2 },
      { cx: width * 0.8, cy: height * 0.2 },
      { cx: width * 0.2, cy: height * 0.8 },
      { cx: width * 0.8, cy: height * 0.8 },
      { cx: width * 0.5, cy: height * 0.5 },
      { cx: width * 0.5, cy: height * 0.2 },
      { cx: width * 0.5, cy: height * 0.8 },
      { cx: width * 0.2, cy: height * 0.5 },
    ];
    
    for (let i = 0; i < Math.min(holes, positions.length); i++) {
      circles.push(
        <g key={`hole-${i}`} className={animate ? 'fade-in' : ''} style={{ opacity: animate ? 1 : 0, transition: `opacity 0.5s ease ${1 + i * 0.2}s` }}>
          <circle cx={positions[i].cx} cy={positions[i].cy} r={Math.min(height, width) * 0.08} fill="transparent" stroke="#60A5FA" strokeWidth="2" />
          {/* Crosshairs */}
          <line x1={positions[i].cx - 15} y1={positions[i].cy} x2={positions[i].cx + 15} y2={positions[i].cy} stroke="rgba(96, 165, 250, 0.4)" strokeWidth="1" />
          <line x1={positions[i].cx} y1={positions[i].cy - 15} x2={positions[i].cx} y2={positions[i].cy + 15} stroke="rgba(96, 165, 250, 0.4)" strokeWidth="1" />
        </g>
      );
    }
    return circles;
  };

  // Generate mock positions for slots
  const renderSlots = () => {
    const rects = [];
    if (slots > 0) {
      rects.push(
        <rect 
          key="slot-1" 
          x={width * 0.3} y={height * 0.4} 
          width={width * 0.4} height={height * 0.2} 
          rx={height * 0.1}
          fill="transparent" stroke="#34D399" strokeWidth="2" 
          strokeDasharray="5,5"
          className={animate ? 'fade-in' : ''}
          style={{ opacity: animate ? 1 : 0, transition: `opacity 0.5s ease 2s` }}
        />
      );
    }
    return rects;
  };

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 2 }}>
      <svg 
        viewBox={`0 0 ${width} ${height}`} 
        style={{ 
          width: '100%', 
          maxHeight: '300px',
          filter: 'drop-shadow(0 0 15px rgba(59, 130, 246, 0.2))'
        }}
      >
        {/* Outer Contour */}
        <rect 
          x="10" y="10" 
          width={width - 20} height={height - 20} 
          rx={analysis.fillet_count > 0 ? 15 : 0}
          fill="rgba(19, 28, 49, 0.8)" 
          stroke="#3B82F6" 
          strokeWidth="3"
          className={animate ? 'draw-path' : ''}
        />
        
        {/* Dimension lines (mock) */}
        {animate && (
          <g className="fade-in" style={{ opacity: 0, transition: 'opacity 1s ease 1s' }}>
            {/* Top width */}
            <line x1="10" y1="5" x2={width - 10} y2="5" stroke="#94A3B8" strokeWidth="1" />
            <line x1="10" y1="2" x2="10" y2="8" stroke="#94A3B8" strokeWidth="1" />
            <line x1={width - 10} y1="2" x2={width - 10} y2="8" stroke="#94A3B8" strokeWidth="1" />
            <text x={width / 2} y="-2" fill="#94A3B8" fontSize="12" textAnchor="middle">{dims.length || '?'} mm</text>
          </g>
        )}

        {renderHoles()}
        {renderSlots()}
      </svg>
      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Typography variant="caption" sx={{ color: '#60A5FA', display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ w: 8, h: 8, borderRadius: '50%', bgcolor: '#60A5FA', display: 'inline-block' }} /> Detected Holes ({holes})
        </Typography>
        <Typography variant="caption" sx={{ color: '#34D399', display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ w: 8, h: 8, borderRadius: '50%', bgcolor: '#34D399', display: 'inline-block' }} /> Detected Slots ({slots})
        </Typography>
      </Box>
    </Box>
  );
}
