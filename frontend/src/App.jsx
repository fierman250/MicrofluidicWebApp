import React, { useState, useRef } from 'react';
import axios from 'axios';
import GridSelector from './GridSelector';
import ModelViewer from './ModelViewer';
import { Play, Download, Trash2, Box, Activity, Eye, X } from 'lucide-react';

// 127.0.0.1:8000 for local dev fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function App() {
  const [cdepth, setCdepth] = useState(0.16);
  const [cwidth, setCwidth] = useState(0.4);
  const [cspace, setCspace] = useState(0.4);
  
  const [selectedPoints, setSelectedPoints] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isModelLoading, setIsModelLoading] = useState(false);
  const [stlBlobUrl, setStlBlobUrl] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 3D Model Parameters
  const [upperThickness, setUpperThickness] = useState(0.5);
  const [bottomThickness, setBottomThickness] = useState(0.5);
  const [inletDiameter, setInletDiameter] = useState(6.0);
  const [inletYDist, setInletYDist] = useState(16.5);
  const [isDualChip, setIsDualChip] = useState(false);
  const [showModelGuide, setShowModelGuide] = useState(false);
  
  const clearGridRef = useRef(null);

  const propertyNames = [
    { id: 'E11', name: "Young's Modulus (X)", type: 'Mechanical' },
    { id: 'YS11', name: "Yield Strength (X)", type: 'Mechanical' },
    { id: 'v11', name: "Poisson's Ratio (X)", type: 'Mechanical' },
    { id: 'E22', name: "Young's Modulus (Y)", type: 'Mechanical' },
    { id: 'YS22', name: "Yield Strength (Y)", type: 'Mechanical' },
    { id: 'v22', name: "Poisson's Ratio (Y)", type: 'Mechanical' },
    { id: 'k11', name: "Thermal Conductivity (X)", type: 'Thermal' },
    { id: 'k22', name: "Thermal Conductivity (Y)", type: 'Thermal' },
    { id: 'k33', name: "Thermal Conductivity (Z)", type: 'Thermal' },
    { id: 'CTE11', name: "Coefficient of Thermal Expansion (X)", type: 'Thermal' },
    { id: 'CTE22', name: "Coefficient of Thermal Expansion (Y)", type: 'Thermal' },
    { id: 'CTE33', name: "Coefficient of Thermal Expansion (Z)", type: 'Thermal' }
  ];

  const handlePredict = async () => {
    if (selectedPoints.length === 0) {
      alert("Please select at least one point in the pattern grid.");
      return;
    }
    
    setIsLoading(true);
    setPredictions(null);
    try {
      const payload = {
        cdepth: parseFloat(cdepth),
        cwidth: parseFloat(cwidth),
        cspace: parseFloat(cspace),
        selected_points: selectedPoints
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/predict`, payload);
      setPredictions(response.data.predictions);
    } catch (err) {
      console.error(err);
      alert("Prediction failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateModel = async () => {
    if (!predictions && selectedPoints.length === 0) {
      alert("Please generate a prediction or select points first before generating 3D Model.");
      return;
    }
    
    setIsModelLoading(true);
    try {
      const payload = {
        cdepth: parseFloat(cdepth),
        cwidth: parseFloat(cwidth),
        cspace: parseFloat(cspace),
        selected_points: selectedPoints,
        upper_thickness: parseFloat(upperThickness),
        bottom_thickness: parseFloat(bottomThickness),
        inlet_diameter: parseFloat(inletDiameter),
        inlet_y_dist: parseFloat(inletYDist),
        is_dual_chip: isDualChip
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/generate-model`, payload, {
        responseType: 'blob' // Important for saving files
      });
      
      // Free old blob url
      if (stlBlobUrl) {
          URL.revokeObjectURL(stlBlobUrl);
      }
      
      // Create blob link to save to state for the viewer
      const url = window.URL.createObjectURL(new Blob([response.data]));
      setStlBlobUrl(url);
    } catch (err) {
      console.error(err);
      alert("Model generation failed.");
    } finally {
      setIsModelLoading(false);
    }
  };

  const handleDownloadModel = () => {
      if (!stlBlobUrl) return;
      const link = document.createElement('a');
      link.href = stlBlobUrl;
      link.setAttribute('download', 'Microfluidic_Geometry.stl');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
  };

  const handleClear = () => {
    if (clearGridRef.current) clearGridRef.current();
    setPredictions(null);
    setStlBlobUrl(null);
    setIsModalOpen(false);
  };

  return (
    <div className="app-container">
      <h1>Microfluidic Property Prediction</h1>
      
      <div className="main-layout">
        {/* Left Column - Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', overflowY: 'auto', maxHeight: 'calc(100vh - 10rem)', paddingRight: '4px' }}>
          
          <div className="glass-panel" style={{ flex: 'none' }}>
            <h2><Activity size={24} color="var(--primary)" /> Microfluidic Channel Parameters</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Channel Depth <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(0.08 – 0.20 mm)</span></label>
                <input type="number" step="0.01" min="0.08" max="0.20" className="input-field" value={cdepth} onChange={e => setCdepth(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Channel Width <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(0.1 – 0.4 mm)</span></label>
                <input type="number" step="0.01" min="0.1" max="0.4" className="input-field" value={cwidth} onChange={e => setCwidth(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Channel Space <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(0.1 – 0.4 mm)</span></label>
                <input type="number" step="0.01" min="0.1" max="0.4" className="input-field" value={cspace} onChange={e => setCspace(e.target.value)} />
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              <button 
                className="btn btn-primary" 
                style={{ flex: 1 }}
                onClick={handlePredict}
                disabled={isLoading}
              >
                <Play size={18} /> {isLoading ? "Processing..." : "Generate & Predict"}
              </button>
              <button 
                className="btn" 
                style={{ background: 'var(--danger)', color: 'white', borderColor: 'var(--danger)' }}
                onClick={handleClear}
                disabled={isLoading}
              >
                <Trash2 size={18} /> Clear
              </button>
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <GridSelector onSelectionChange={setSelectedPoints} onClearRef={clearGridRef} />
          </div>
          
        </div>
        
        {/* Right Column - Outputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', overflowY: 'auto', maxHeight: 'calc(100vh - 10rem)', paddingRight: '4px' }}>
          
          <div className="glass-panel">
            <h2><Box size={24} color="var(--primary)" /> Prediction Results</h2>
            {predictions ? (
              <>
                <h3>Mechanical Properties</h3>
                <div className="properties-grid" style={{ marginBottom: '1.5rem' }}>
                  {propertyNames.filter(p => p.type === 'Mechanical').map((prop, idx) => {
                    const absIdx = propertyNames.findIndex(p => p.id === prop.id);
                    return (
                      <div key={prop.id} className="property-card">
                        <div className="property-name">{prop.id}</div>
                        <div className="property-desc">{prop.name}</div>
                        <div className="property-value">{predictions[absIdx].toFixed(6)}</div>
                      </div>
                    );
                  })}
                </div>
                
                <h3>Thermal Properties</h3>
                <div className="properties-grid">
                  {propertyNames.filter(p => p.type === 'Thermal').map((prop, idx) => {
                    const absIdx = propertyNames.findIndex(p => p.id === prop.id);
                    return (
                      <div key={prop.id} className="property-card">
                        <div className="property-name">{prop.id}</div>
                        <div className="property-desc">{prop.name}</div>
                        <div className="property-value">{predictions[absIdx].toFixed(6)}</div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
                Run prediction to see material properties.
              </div>
            )}
          </div>

          <div className="glass-panel preview-area">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}><Box size={24} color="var(--primary)" /> Microfludic 3D Model Overview</h2>
              <div style={{ display: 'flex', gap: '0.6rem' }}>
                <button
                  onClick={() => setIsDualChip(v => !v)}
                  style={{
                    background: isDualChip ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                    border: isDualChip ? '1px solid rgba(59, 130, 246, 0.6)' : '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    color: isDualChip ? '#93c5fd' : '#94a3b8',
                    cursor: 'pointer',
                    padding: '0.4rem 0.85rem',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    transition: 'all 0.2s',
                    flexShrink: 0,
                    boxShadow: isDualChip ? '0 0 12px rgba(59, 130, 246, 0.2)' : 'none',
                  }}
                  title="Enable Dual Channel mirroring"
                >
                  <Activity size={14} style={{ color: isDualChip ? 'var(--primary)' : 'inherit' }} />
                  Dual Channel: {isDualChip ? 'ON' : 'OFF'}
                </button>
                <button
                  onClick={() => setShowModelGuide(v => !v)}
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
                    flexShrink: 0,
                  }}
                >
                  {showModelGuide ? '✕ Hide' : '? 3D Model Guide'}
                </button>
              </div>
            </div>

            {showModelGuide && (
              <div style={{
                marginBottom: '1rem',
                borderRadius: '10px',
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.08)',
                background: 'rgba(0,0,0,0.25)',
              }}>
                <img
                  src="/3dmodel_guide.png"
                  alt="3D Model Guide"
                  style={{ width: '100%', display: 'block' }}
                />
              </div>
            )}

            <div className="preview-box" style={{ padding: 0, overflow: 'hidden', width: '100%', aspectRatio: '2 / 1', display: 'flex', flexDirection: 'column' }}>
              {isLoading || isModelLoading ? (
                <div className="loading-overlay">
                  <div className="spinner"></div>
                </div>
              ) : stlBlobUrl ? (
                <ModelViewer stlUrl={stlBlobUrl} />
              ) : (
                <div style={{ padding: '2rem', color: '#94a3b8' }}>Awaiting 3D Model generation...</div>
              )}
            </div>

            {/* 3D Geometry Parameters - Embedded */}
            <div style={{ 
                display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', 
                marginTop: '1.25rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', 
                borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' 
            }}>
              <div className="input-group">
                <label className="input-label">Inlet Diameter <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(mm)</span></label>
                <input type="number" step="0.1" className="input-field" value={inletDiameter} onChange={e => setInletDiameter(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Inlet Y Position <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(mm)</span></label>
                <input type="number" step="0.1" className="input-field" value={inletYDist} onChange={e => setInletYDist(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Upper Thickness <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(mm)</span></label>
                <input type="number" step="0.05" className="input-field" value={upperThickness} onChange={e => setUpperThickness(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Bottom Thickness <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>(mm)</span></label>
                <input type="number" step="0.05" className="input-field" value={bottomThickness} onChange={e => setBottomThickness(e.target.value)} />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem', gap: '0.75rem', flexWrap: 'nowrap' }}>
              {stlBlobUrl && (
                <button 
                  className="btn" 
                  onClick={() => setIsModalOpen(true)}
                  style={{ background: 'rgba(255,255,255,0.1)', padding: '0.6rem 0.8rem', whiteSpace: 'nowrap' }}
                >
                  <Eye size={18} /> View Full Screen
                </button>
              )}
              <button 
                className="btn btn-accent" 
                onClick={handleGenerateModel}
                disabled={isModelLoading || (!predictions && selectedPoints.length === 0)}
                style={{ padding: '0.6rem 0.8rem', whiteSpace: 'nowrap' }}
              >
                <Box size={18} /> {isModelLoading ? "Working..." : "Generate 3D Model"}
              </button>
              {stlBlobUrl && (
                <>
                  <button 
                    className="btn btn-primary" 
                    onClick={handleDownloadModel}
                    disabled={!stlBlobUrl}
                    style={{ padding: '0.6rem 0.8rem', whiteSpace: 'nowrap' }}
                  >
                    <Download size={18} /> Download STL
                  </button>
                  <a 
                    className="btn btn-primary" 
                    href={`${API_BASE_URL}/api/download-step`}
                    download="Microfluidic_Geometry.step"
                    style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 0.8rem', whiteSpace: 'nowrap' }}
                  >
                    <Download size={18} /> Download STEP
                  </a>
                </>
              )}
            </div>
          </div>

          {/* Modal Pop-up */}
          {isModalOpen && stlBlobUrl && (
            <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
              <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                  <div className="modal-title">
                    <Box size={24} color="var(--primary)" /> 
                    3D Model Viewer
                  </div>
                  <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                    <X size={24} />
                  </button>
                </div>
                <div className="modal-body">
                  <ModelViewer stlUrl={stlBlobUrl} />
                </div>
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}

export default App;
