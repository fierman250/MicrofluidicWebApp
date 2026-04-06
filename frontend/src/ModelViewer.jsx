import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stage, Center } from '@react-three/drei';
import { STLLoader } from 'three-stdlib';
import { useLoader } from '@react-three/fiber';
import * as THREE from 'three';

const ModelParams = ({ url }) => {
  const geometry = useLoader(STLLoader, url);
  
  // Create material once
  const material = useMemo(() => new THREE.MeshStandardMaterial({
    color: '#3b82f6',
    roughness: 0.2,
    metalness: 0.1,
  }), []);

  return (
    <Center>
      <mesh geometry={geometry} material={material} castShadow receiveShadow />
    </Center>
  );
};

const ModelViewer = ({ stlUrl }) => {
  if (!stlUrl) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
        Generate the 3D Model to view it here.
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '300px', cursor: 'grab' }}>
      <Canvas shadows camera={{ position: [0, 0, 150], fov: 50 }}>
        <React.Suspense fallback={null}>
          <Stage environment="city" intensity={0.6}>
            <ModelParams url={stlUrl} />
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
