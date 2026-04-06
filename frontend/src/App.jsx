import React, { useState, useRef } from 'react';
import axios from 'axios';
import GridSelector from './GridSelector';
import ModelViewer from './ModelViewer';
import { Play, Download, Trash2, Box, Activity, Eye, X } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [cdepth, setCdepth] = useState(0.16);
  const [cwidth, setCwidth] = useState(0.4);
  const [cspace, setCspace] = useState(0.4);
  
  const [selectedPoints, setSelectedPoints] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [flowImage, setFlowImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isModelLoading, setIsModelLoading] = useState(false);
  const [stlBlobUrl, setStlBlobUrl] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const clearGridRef = useRef(null);

  const propertyNames = [
    { id: 'E11', name: "Young's Modulus (X)", type: 'Mechanical' },
    { id: 'YS11', name: "Yield Strength (X)", type: 'Mechanical' },
    { id: 'v11', name: "Poisson's Ratio (X)", type: 'Mechanical' },
    { id: 'E22', name: "Young's Modulus (Y)", type: 'Mechanical' },
    { id: 'YS22', name: "Yield Strength (Y)", type: 'Mechanical' },
    { id: 'v22', name: "Poisson's Ratio (Y)", type: 'Mechanical' },
    { id: 'k11', name: "Thermal Cond. (X)", type: 'Thermal' },
    { id: 'k22', name: "Thermal Cond. (Y)", type: 'Thermal' },
    { id: 'k33', name: "Thermal Cond. (Z)", type: 'Thermal' },
    { id: 'CTE11', name: "Thermal Exp. (X)", type: 'Thermal' },
    { id: 'CTE22', name: "Thermal Exp. (Y)", type: 'Thermal' },
    { id: 'CTE33', name: "Thermal Exp. (Z)", type: 'Thermal' }
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
        // Just send empty coordinates, backend will use dictionary point names if we map them
        // Wait, backend expects tuples of floats?
        // Ah, the desktop app `interpret_points` uses the names "1A", "2B"
        // Let's modify the frontend payload. Wait, `main.py` expects `List[Tuple[float, float]]`
        // Oh! In `MicrofluidicGUI_v4.py`, it calculates the tuple from the dictionary.
        // Let's just send the point strings and calculate in the backend?
        // Wait, I forgot `interpret_points` is in the GUI not backend!
        // No, I need to send the names! Let me check `main.py` soon.
        selected_points: selectedPoints
      };
      
      const response = await axios.post(`${API_BASE_URL}/api/predict`, payload);
      setPredictions(response.data.predictions);
      setFlowImage(response.data.image_base64);
    } catch (err) {
      console.error(err);
      alert("Prediction failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateModel = async () => {
    if (!flowImage && selectedPoints.length === 0) {
      alert("Please generate a pattern first before generating 3D Model.");
      return;
    }
    
    setIsModelLoading(true);
    try {
      const payload = {
        cdepth: parseFloat(cdepth),
        cwidth: parseFloat(cwidth),
        cspace: parseFloat(cspace),
        selected_points: selectedPoints
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
      setIsModalOpen(true);
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
    setFlowImage(null);
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
            <h2><Activity size={24} color="var(--primary)" /> Parameters</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Channel Depth</label>
                <input type="number" step="0.01" className="input-field" value={cdepth} onChange={e => setCdepth(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Channel Width</label>
                <input type="number" step="0.01" className="input-field" value={cwidth} onChange={e => setCwidth(e.target.value)} />
              </div>
              <div className="input-group">
                <label className="input-label">Channel Space</label>
                <input type="number" step="0.01" className="input-field" value={cspace} onChange={e => setCspace(e.target.value)} />
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
          
          <div className="glass-panel preview-area">
            <h2>Flow Visualization</h2>
            <div className="preview-box">
              {isLoading && (
                <div className="loading-overlay">
                  <div className="spinner"></div>
                </div>
              )}
              {flowImage ? (
                <img src={flowImage} alt="Flow Path Visualization" className="preview-img" />
              ) : (
                <div style={{ color: '#94a3b8' }}>Awaiting pattern generation...</div>
              )}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.5rem', gap: '1rem', flexWrap: 'wrap' }}>
              {stlBlobUrl && (
                <button 
                  className="btn" 
                  onClick={() => setIsModalOpen(true)}
                  style={{ background: 'rgba(255,255,255,0.1)' }}
                >
                  <Eye size={18} /> View 3D Model
                </button>
              )}
              <button 
                className="btn btn-accent" 
                onClick={handleGenerateModel}
                disabled={isModelLoading || (!flowImage && selectedPoints.length === 0)}
              >
                <Box size={18} /> {isModelLoading ? "Working..." : "Generate 3D Model"}
              </button>
              {stlBlobUrl && (
                <button 
                  className="btn btn-primary" 
                  onClick={handleDownloadModel}
                  disabled={!stlBlobUrl}
                >
                  <Download size={18} /> Download STL
                </button>
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

          <div className="glass-panel">
            <h2><Box size={24} color="var(--primary)" /> Predictions</h2>
            {predictions ? (
              <>
                <h3>Mechanical</h3>
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
                
                <h3>Thermal</h3>
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
          
        </div>
      </div>
    </div>
  );
}

export default App;
