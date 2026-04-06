import React, { useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, Center } from '@react-three/drei';
import { STLLoader } from 'three-stdlib';
import { useLoader } from '@react-three/fiber';
import * as THREE from 'three';

const ModelParams = ({ url, viewMode }) => {
  const geometry = useLoader(STLLoader, url);
  
  // Create material depending on viewMode
  const materialProps = useMemo(() => {
    const props = {
      color: '#3b82f6',
      roughness: 0.2,
      metalness: 0.1,
      transparent: false,
      opacity: 1,
      wireframe: false,
      depthWrite: true,
      side: THREE.DoubleSide
    };

    if (viewMode === 'transparent') {
      props.transparent = true;
      props.opacity = 0.35;
      props.depthWrite = false;
    } else if (viewMode === 'wireframe') {
      props.wireframe = true;
    }

    return props;
  }, [viewMode]);

  return (
    <Center>
      <mesh geometry={geometry} castShadow={viewMode === 'solid'} receiveShadow={viewMode === 'solid'}>
        <meshStandardMaterial {...materialProps} />
      </mesh>
    </Center>
  );
};

const ModelViewer = ({ stlUrl }) => {
  const [viewMode, setViewMode] = useState('transparent'); 
  
  if (!stlUrl) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
        Generate the 3D Model to view it here.
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', flex: 1, display: 'flex', flexDirection: 'column', minHeight: '300px', cursor: 'grab', position: 'relative' }}>
      
      {/* View Controls Toolbar */}
      <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 10, display: 'flex', gap: '5px', background: 'rgba(255, 255, 255, 0.8)', padding: '5px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <button 
          onClick={() => setViewMode('solid')}
          style={{ 
            padding: '4px 10px', cursor: 'pointer', border: 'none', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold',
            background: viewMode === 'solid' ? '#3b82f6' : 'transparent',
            color: viewMode === 'solid' ? 'white' : '#475569'
          }}
        >
          Solid
        </button>
        <button 
          onClick={() => setViewMode('transparent')}
          style={{ 
            padding: '4px 10px', cursor: 'pointer', border: 'none', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold',
            background: viewMode === 'transparent' ? '#3b82f6' : 'transparent',
            color: viewMode === 'transparent' ? 'white' : '#475569'
          }}
        >
          Glass (Transparent)
        </button>
        <button 
          onClick={() => setViewMode('wireframe')}
          style={{ 
            padding: '4px 10px', cursor: 'pointer', border: 'none', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold',
            background: viewMode === 'wireframe' ? '#3b82f6' : 'transparent',
            color: viewMode === 'wireframe' ? 'white' : '#475569'
          }}
        >
          Wireframe
        </button>
      </div>

      <Canvas shadows camera={{ position: [0, 0, 150], fov: 50 }} style={{ flex: 1, height: '100%', width: '100%' }}>
        <React.Suspense fallback={null}>
          <Stage environment="city" intensity={0.6} shadows={false}>
            <ModelParams url={stlUrl} viewMode={viewMode} />
          </Stage>
        </React.Suspense>
        <OrbitControls makeDefault />
      </Canvas>
      
      <div style={{ position: 'absolute', bottom: '10px', right: '10px', fontSize: '12px', color: '#64748b', pointerEvents: 'none' }}>
        Left Click: Rotate | Right Click: Pan | Scroll: Zoom
      </div>
    </div>
  );
};

export default ModelViewer;
