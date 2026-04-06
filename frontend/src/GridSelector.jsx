import React, { useState, useEffect, useRef, useCallback } from 'react';

const GridSelector = ({ onSelectionChange, onClearRef }) => {
  const rows = 9;
  const cols = 3;
  const columns = ['A', 'B', 'C'];

  const [selectedPoints, setSelectedPoints] = useState([]);
  const [connections, setConnections] = useState([]);
  const [layoutVersion, setLayoutVersion] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [showGuide, setShowGuide] = useState(false); // live drag position for "in-progress" line

  const containerRef = useRef(null);
  const isDraggingRef = useRef(false);
  const selectedRef = useRef([]); // mirror of selectedPoints for use inside event handlers
  const connectionsRef = useRef([]);

  // Keep refs in sync with state
  useEffect(() => { selectedRef.current = selectedPoints; }, [selectedPoints]);
  useEffect(() => { connectionsRef.current = connections; }, [connections]);

  // Expose clear function to parent
  useEffect(() => {
    if (onClearRef) onClearRef.current = handleClear;
  }, [onClearRef]);

  // Watch for layout changes to keep SVG lines aligned
  useEffect(() => {
    const bump = () => setLayoutVersion(v => v + 1);
    const observer = new ResizeObserver(bump);
    if (containerRef.current) observer.observe(containerRef.current);
    observer.observe(document.body);
    window.addEventListener('scroll', bump, true);
    return () => {
      observer.disconnect();
      window.removeEventListener('scroll', bump, true);
    };
  }, []);

  // Stop drag when mouse/touch released anywhere on the page
  useEffect(() => {
    const stopDrag = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        setIsDragging(false);
        setCursor(null);
      }
    };
    window.addEventListener('mouseup', stopDrag);
    window.addEventListener('touchend', stopDrag);
    return () => {
      window.removeEventListener('mouseup', stopDrag);
      window.removeEventListener('touchend', stopDrag);
    };
  }, []);

  const handleClear = () => {
    setSelectedPoints([]);
    setConnections([]);
    selectedRef.current = [];
    connectionsRef.current = [];
    onSelectionChange([]);
  };

  // Core logic: try to add a point
  const tryAddPoint = useCallback((row, col) => {
    const colStr = columns[col];
    const pointId = `${row}${colStr}`;
    const current = selectedRef.current;

    // Skip if already selected
    if (current.some(p => p.id === pointId)) return;

    const rowNum = parseInt(row);

    // Max 2 per row
    if (current.filter(p => parseInt(p.r) === rowNum).length >= 2) return;

    // Must not go backwards
    if (current.length > 0) {
      const lastRow = parseInt(current[current.length - 1].r);
      if (rowNum < lastRow) return;
    }

    const newPoint = { id: pointId, r: row, c: colStr };
    const next = [...current, newPoint];
    const newConns = current.length > 0 ? [...connectionsRef.current, [current[current.length - 1], newPoint]] : connectionsRef.current;

    selectedRef.current = next;
    connectionsRef.current = newConns;
    setSelectedPoints(next);
    setConnections(newConns);
    onSelectionChange(next.map(p => p.id));
  }, [onSelectionChange]);

  // --- Mouse handlers ---
  const handleMouseDown = (row, col, e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    tryAddPoint(row, col);
  };

  const handleMouseEnter = (row, col) => {
    if (isDraggingRef.current) {
      tryAddPoint(row, col);
    }
  };

  const handleMouseMove = useCallback((e) => {
    if (!isDraggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setCursor({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  // --- Touch handlers ---
  const handleTouchStart = (row, col, e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    tryAddPoint(row, col);
  };

  const handleTouchMove = useCallback((e) => {
    if (!isDraggingRef.current || !containerRef.current) return;
    e.preventDefault();
    const touch = e.touches[0];
    const rect = containerRef.current.getBoundingClientRect();
    setCursor({ x: touch.clientX - rect.left, y: touch.clientY - rect.top });

    // Find DOM element under the touch
    const el = document.elementFromPoint(touch.clientX, touch.clientY);
    if (el && el.dataset.row && el.dataset.col) {
      tryAddPoint(parseInt(el.dataset.row), parseInt(el.dataset.col));
    }
  }, [tryAddPoint]);

  // Compute line coords from DOM at render time
  const getLineCoords = (conn) => {
    const p1 = document.getElementById(`point-${conn[0].id}`);
    const p2 = document.getElementById(`point-${conn[1].id}`);
    if (p1 && p2 && containerRef.current) {
      const contRect = containerRef.current.getBoundingClientRect();
      const r1 = p1.getBoundingClientRect();
      const r2 = p2.getBoundingClientRect();
      return {
        x1: r1.left + r1.width / 2 - contRect.left,
        y1: r1.top + r1.height / 2 - contRect.top,
        x2: r2.left + r2.width / 2 - contRect.left,
        y2: r2.top + r2.height / 2 - contRect.top,
      };
    }
    return null;
  };

  // Get center of last selected point (for the live "in-progress" trailing line)
  const getLastPointCenter = () => {
    const last = selectedPoints[selectedPoints.length - 1];
    if (!last) return null;
    const el = document.getElementById(`point-${last.id}`);
    if (!el || !containerRef.current) return null;
    const contRect = containerRef.current.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    return { x: r.left + r.width / 2 - contRect.left, y: r.top + r.height / 2 - contRect.top };
  };

  const renderGrid = () => {
    const points = [];
    for (let r = rows; r >= 1; r--) {
      for (let c = 0; c < cols; c++) {
        const colStr = columns[c];
        const pointId = `${r}${colStr}`;
        const isSelected = selectedPoints.some(p => p.id === pointId);
        const orderIndex = selectedPoints.findIndex(p => p.id === pointId);

        points.push(
          <div
            key={pointId}
            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', userSelect: 'none' }}
          >
            <div
              id={`point-${pointId}`}
              data-row={r}
              data-col={c}
              className={`grid-point ${isSelected ? 'selected' : ''}`}
              onMouseDown={(e) => handleMouseDown(r, c, e)}
              onMouseEnter={() => handleMouseEnter(r, c)}
              onTouchStart={(e) => handleTouchStart(r, c, e)}
              style={{ cursor: isDragging ? 'crosshair' : 'pointer', position: 'relative' }}
            >
              {/* Show order number badge */}
              {isSelected && (
                <span style={{
                  position: 'absolute',
                  top: '-6px', right: '-6px',
                  background: 'var(--primary)',
                  color: 'white',
                  borderRadius: '50%',
                  width: '14px', height: '14px',
                  fontSize: '8px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 'bold',
                  pointerEvents: 'none',
                }}>
                  {orderIndex + 1}
                </span>
              )}
            </div>
            <span style={{ marginTop: '8px', fontSize: '10px', color: '#94a3b8', fontWeight: 'bold', pointerEvents: 'none' }}>
              {pointId}
            </span>
          </div>
        );
      }
    }
    return points;
  };

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h2>Pattern Selection</h2>

      {/* How-to-use guide toggle */}
      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={() => setShowGuide(v => !v)}
          style={{
            background: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.4)',
            borderRadius: '8px',
            color: '#93c5fd',
            cursor: 'pointer',
            padding: '0.4rem 0.85rem',
            fontSize: '0.8rem',
            fontWeight: 600,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s',
          }}
        >
          {showGuide ? '✕ Hide' : '? How to Use'}
        </button>

        {showGuide && (
          <div style={{
            marginTop: '0.75rem',
            borderRadius: '10px',
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'rgba(0,0,0,0.25)',
          }}>
            <img
              src="/howtousepointselector.png"
              alt="How to use the point selector"
              style={{ width: '100%', display: 'block' }}
            />
          </div>
        )}
      </div>

      <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        Click &amp; drag across points (row 1→9, up to 2 per row). Or tap each point individually.
      </p>

      <div
        ref={containerRef}
        className="grid-container"
        onMouseMove={handleMouseMove}
        onTouchMove={handleTouchMove}
        style={{
          flex: 1,
          position: 'relative',
          paddingLeft: '0',
          paddingRight: '0',
          gridTemplateRows: `repeat(${rows}, 1fr)`,
          cursor: isDragging ? 'crosshair' : 'default',
          touchAction: 'none', // prevent scroll while drawing
        }}
      >
        {renderGrid()}

        {/* SVG: completed lines + live trailing line while dragging */}
        <svg
          key={layoutVersion}
          style={{
            position: 'absolute', top: 0, left: 0,
            width: '100%', height: '100%',
            pointerEvents: 'none', zIndex: 1, overflow: 'visible',
          }}
        >
          {/* Completed connection lines */}
          {connections.map((conn, idx) => {
            const coords = getLineCoords(conn);
            if (!coords) return null;
            return (
              <line
                key={idx}
                x1={coords.x1} y1={coords.y1}
                x2={coords.x2} y2={coords.y2}
                stroke="var(--accent)"
                strokeWidth="4"
                strokeLinecap="round"
                filter="drop-shadow(0px 0px 4px var(--accent-glow))"
              />
            );
          })}

          {/* Live trailing line from last selected point to cursor while dragging */}
          {isDragging && cursor && selectedPoints.length > 0 && (() => {
            const last = getLastPointCenter();
            if (!last) return null;
            return (
              <line
                x1={last.x} y1={last.y}
                x2={cursor.x} y2={cursor.y}
                stroke="var(--accent)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray="6 4"
                opacity="0.6"
              />
            );
          })()}
        </svg>
      </div>

      {selectedPoints.length > 0 && (
        <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#94a3b8' }}>
          <strong style={{ color: 'var(--accent)' }}>{selectedPoints.length} points</strong> selected:{' '}
          {selectedPoints.map(p => p.id).join(' → ')}
        </div>
      )}
    </div>
  );
};

export default GridSelector;
