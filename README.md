# Microfluidic Property Prediction — Web App

A web-based platform for predicting material properties (mechanical & thermal) of microfluidic channel geometries using deep learning. Built with **FastAPI** (backend) and **React** (frontend).

> [!NOTE]
> Model weights (`*.pth`, ~140 MB) are stored using **Git LFS**. Run `git lfs pull` after cloning to download them.

---

## Features

- **Pattern Selection Grid** — Draw your microfluidic channel path on a 9×3 interactive grid (drag to select, like a phone pattern lock)
- **Deep Learning Prediction** — Predicts 12 material properties (Young's Modulus, Yield Strength, Poisson's Ratio, Thermal Conductivity, Thermal Expansion) from the pattern
- **Flow Path Visualization** — Renders the generated flow path image after prediction
- **3D Model Viewer** — Generates and displays an interactive transparent 3D model in your browser
- **CAD Downloads** — Export the perfectly engineered microfluidic manifold as industrial `.step` or 3D-printable `.stl` files

---

## Requirements

### System
- **Python** 3.8 or higher
- **Node.js** 18 or higher (with npm)
- A **conda** environment (recommended) or virtualenv

### Python Packages (Backend)
Install all backend dependencies:

```bash
pip install -r requirements.txt
```

Key packages:
| Package | Purpose |
|---|---|
| `fastapi` | Web API framework |
| `uvicorn` | ASGI server |
| `torch` | Deep learning inference |
| `numpy` | Numerical computation |
| `Pillow` | Image processing |
| `matplotlib` | Flow path rendering |
| `cadquery` | Microfluidic true-MM physical solid modeling |
| `shapely` | Geometric path offsetting |
| `scikit-learn` | Data scaling |
| `joblib` | Model/scaler loading |

### Node.js Packages (Frontend)
Install all frontend dependencies:

```bash
cd frontend
npm install
```

---

## How to Run

### Step 1 — Start the Backend

Open a terminal in the project root (`WebAPP/`) and run:

```bash
python -m uvicorn main:app --reload
```

The backend API will be available at: `http://127.0.0.1:8000`

> If using conda, activate your environment first:
> ```bash
> conda activate <your_env_name>
> ```

---

### Step 2 — Start the Frontend

Open a **second terminal** in the `frontend/` directory and run:

```bash
cd frontend
npm run dev
```

The web app will be available at: `http://localhost:5173`

Open this URL in your browser.

---

## Usage

1. **Set Parameters** — Enter Channel Depth, Width, and Space values in the Parameters panel.
2. **Draw Pattern** — Click and drag across dots on the Pattern Selection grid (row 1 → 9, up to 2 dots per row). Click **"? How to Use"** for a guide.
3. **Generate & Predict** — Click the **"Generate & Predict"** button to run the deep learning model.
4. **View Results** — The Flow Visualization image and predicted material properties will appear on the right.
5. **Generate 3D Model** — Click **"Generate 3D Model"** to build and open the interactive 3D viewer popup.
6. **Download STL or STEP** — Use the respective download buttons to save your fully analytic 3D files.

---

## Project Structure

```
WebAPP/
├── main.py                  # FastAPI backend entry point
├── iGenerator.py            # Flow path generation & DL prediction
├── ModelGeneratorCQ.py        # Flawless CAD engine (CadQuery) scaling True MMs
├── requirements.txt         # Python dependencies
├── Repository/
│   ├── DLModel.py           # PyTorch model architecture (CombinedNet)
│   ├── best_model_TRCodev3GA-Run2.pth   # Pre-trained model weights
│   ├── best_scaler_TRCodev3GA-Run2.pkl  # Output scaler
│   ├── cnums_lookup.py      # Channel number lookup table
│   ├── pointinterpreter.py  # Grid point → physical coordinate mapping
│   └── howtousepointselector.png  # In-app usage guide image
└── frontend/
    ├── src/
    │   ├── App.jsx           # Main React application
    │   ├── GridSelector.jsx  # Pattern selection grid component
    │   ├── ModelViewer.jsx   # 3D STL viewer (Three.js / R3F)
    │   └── index.css         # Global styles (glassmorphism theme)
    └── public/
        └── howtousepointselector.png
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predict` | Run prediction & return properties + flow image |
| `POST` | `/api/generate-model` | Generate 3D geometry, return browser-ready STL |
| `GET` | `/api/download-step` | Download generated analytical CAD STEP file |
