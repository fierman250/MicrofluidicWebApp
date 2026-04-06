# Microfluidic Property Prediction & CAD Solid Modeling

A high-performance, web-based engineering platform for predicting material properties (mechanical & thermal) and generating industrial-grade 3D CAD models of microfluidic systems.

This application combines **Deep Learning** (for property prediction) with **Analytical Solid Modeling** (via CadQuery) to bridge the gap between AI-driven design and physical manufacturing.

> [!IMPORTANT]
> **CadQuery Integration**: This version uses a pure vector-based OpenCASCADE engine. Exported `.step` files are manifold-solid and ready for industrial CNC/SLA production.

---

## 🚀 Key Features

- **Interactive Pattern Grid** — Define complex microfluidic paths on a 9×3 grid with a smooth, drag-to-select interface.
- **AI Property Prediction** — Instantly predicts 12 critical mechanical and thermal properties using a pre-trained Deep Learning model.
- **True-MM 3D Engine** — Generates precise 3D solids based on real-world millimeter dimensions (depth, width, and spacing).
- **Dual Channel Mode** — One-click mirroring to create perfectly symmetrical, dual-system microfluidic chips with internal partition walls.
- **Industrial CAD Export** — Export functional designs as analytical `.step` files or high-fidelity `.stl` meshes.
- **Integrated 3D Viewer** — Real-time high-fidelity 3D visualization within the web interface (powered by React Three Fiber).

---

## 🛠️ Technology Stack

### Backend (Python/FastAPI)

- **FastAPI/Uvicorn** — High-performance asynchronous API layer.
- **CadQuery & OpenCASCADE** — Industrial-grade analytical solid modeling.
- **Shapely** — 2D vector path offsetting and boolean operations.
- **PyTorch** — Deep Learning inference engine for property prediction.
- **Numpy/Pillow** — Matrix math and image-based pattern representation.

### Frontend (React/Vite)

- **Three.js / React Three Fiber** — High-fidelity 3D rendering in the browser.
- **Lucide Icons** — Beautiful, consistent UI iconography.
- **Vanilla CSS** — Custom premium glassmorphism design system.

---

## ⚙️ Installation & Setup

### 1. Backend Setup

We recommend using **Conda** to manage Python dependencies (required for CadQuery).

```bash
# Clone the repository
git clone <repo-url>
cd Microfluidic-WebApp

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🏃 How to Run

1. **Start Backend**: From the root directory:
   ```bash
   python -m uvicorn main:app --reload
   ```
2. **Start Frontend**: From the `frontend/` directory:
   ```bash
   npm run dev
   ```
3. **Open Browser**: Navigate to `http://localhost:5173`

---

## 📖 Usage Guide

1. **Configure Fluidics**: Set your channel depth, width, and spacing in the main panel.
2. **Define Pattern**: Draw your fluid path on the interactive grid. Use the **"? How to Use"** guide for path rules.
3. **Predict Properties**: Click **"Generate & Predict"** to calculate material behaviors.
4. **Tune 3D Geometry**: Adjust physical parameters in the **3D Model Overview** panel:
   - **Inlet Diameter**: Size of the fluid ports.
   - **Inlet Y-Position**: Distance of ports from the chip center.
   - **Layer Thicknesses**: Upper, middle, and bottom plate dimensions.
5. **Enable Dual Channel**: Click the **"Dual Channel"** toggle in the header to mirror your system.
6. **Generate & Export**: Click **"Generate 3D Model"** to view and download your engineered STEP/STL files.

---

## 📂 Project Structure

```
WebAPP/
├── main.py                  # API entry point & coordinate interpreter
├── ModelGeneratorCQ.py      # Core Solid Modeling Engine (CadQuery/OpenCASCADE)
├── iGenerator.py            # AI Prediction & Fluid Mask Generator
├── Repository/
│   ├── best_model_*.pth      # Trained DL weights (Mechanical/Thermal)
│   ├── 3dmodel_guide.png     # Geometry config help image
│   └── howtousepointselector.png  # Interactive grid help image
├── 3DModelDev/              # Analytical sandbox for mirroring experiments
└── frontend/
    ├── src/
    │   ├── App.jsx           # Main UI & state orchestration
    │   ├── ModelViewer.jsx   # Integrated R3F 3D viewing component
    │   └── GridSelector.jsx  # 2D pattern selection logic
    └── public/               # Static assets & help guides
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
