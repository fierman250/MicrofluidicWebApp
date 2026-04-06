import os
import io
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Tuple
from iGenerator import iGenerator

app = FastAPI(title="Microfluidic Property Prediction API")

# Setup CORS to allow React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from Repository.pointinterpreter import INTERPRETER

class PredictionRequest(BaseModel):
    cdepth: float
    cwidth: float
    cspace: float
    selected_points: List[str]
    # Optional 3D Geometry parameters
    upper_thickness: float = 0.5
    bottom_thickness: float = 0.5
    inlet_diameter: float = 6.0
    inlet_y_dist: float = 16.5
    is_dual_chip: bool = False

def interpret_points_backend(point_names: List[str], xbasic: float, ybasic: float) -> List[Tuple[float, float]]:
    points = []
    
    # Add inlet point
    inlet_expr = INTERPRETER['i1']
    inlet_expr_eval = inlet_expr.replace('xbasic', str(xbasic)).replace('ybasic', str(ybasic))
    points.append(eval(inlet_expr_eval))
    
    # Add selected points
    for point_name in point_names:
        if point_name in INTERPRETER:
            point_expr = INTERPRETER[point_name]
            point_expr_eval = point_expr.replace('xbasic', str(xbasic)).replace('ybasic', str(ybasic))
            points.append(eval(point_expr_eval))
            
    # Add outlet point
    outlet_expr = INTERPRETER['o1']
    outlet_expr_eval = outlet_expr.replace('xbasic', str(xbasic)).replace('ybasic', str(ybasic))
    points.append(eval(outlet_expr_eval))
    
    return points

@app.post("/api/predict")
async def predict_properties(request: PredictionRequest):
    try:
        # Initialize iGenerator
        igen = iGenerator(request.cdepth, request.cwidth, request.cspace)
        
        # Calculate bases
        Cnums = igen.get_cnums()
        xbasic = ((request.cwidth * Cnums) + (request.cspace * Cnums)) * 10
        ybasic = ((request.cwidth * Cnums) + (request.cspace * Cnums)) * 10
        
        physical_points = interpret_points_backend(request.selected_points, xbasic, ybasic)
        
        # Prepare parameters
        nparams = [request.cdepth, request.cwidth, request.cspace]
        
        # Run prediction
        predictions, dl_input_img, img_input_buf, selected_points_used = igen.get_prediction(
            physical_points, nparams
        )
        
        # Convert image buffer to base64
        img_input_buf.seek(0)
        img_base64 = base64.b64encode(img_input_buf.read()).decode('utf-8')
        
        return {
            "predictions": predictions,
            "image_base64": f"data:image/png;base64,{img_base64}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from ModelGeneratorCQ import ModelGeneratorCQ

@app.post("/api/generate-model")
async def generate_model(request: PredictionRequest):
    try:
        # 1. Initialize iGenerator
        igen = iGenerator(request.cdepth, request.cwidth, request.cspace)
        Cnums = igen.get_cnums()
        
        # Calculate bases in True Millimeters natively!
        xbasic_mm = (request.cwidth + request.cspace) * Cnums
        ybasic_mm = (request.cwidth + request.cspace) * Cnums
        physical_points_mm = interpret_points_backend(request.selected_points, xbasic_mm, ybasic_mm)
        
        # Get raw shapely objects for vector modeling at literal mm scale
        shape_offset_mm = request.cwidth + request.cspace
        shapely_data = igen.get_shapely_objects(physical_points_mm, shape_offset_mm)
        
        # 2. Generate the 3D Model using CadQuery
        model_gen = ModelGeneratorCQ(
            chip_width=25.0,
            chip_height=40.0,
            glass_padding=1.0,
            upper_thickness=request.upper_thickness,
            bottom_thickness=request.bottom_thickness,
            inlet_diameter=request.inlet_diameter,
            inlet_y_dist=request.inlet_y_dist,
            is_dual_chip=request.is_dual_chip,
            outer_x_thickness=0.6,
            outer_y_thickness=0.8,
            inner_bridge_thickness=0.5,
            funnel_length_y=8.0,
            funnel_length_x=6.0,
            funnel_tangent_ratio=0.3
        )
        
        output_filename = "Microfluidic_Geometry"
        
        chip, step_path, stl_path = model_gen.generate_model_cq(
            cwidth=request.cwidth,
            cdepth=request.cdepth,
            shapely_data=shapely_data,
            output_filename=output_filename
        )
        
        if not os.path.exists(stl_path):
            raise FileNotFoundError("CadQuery STL file was not created properly.")
            
        # 3. Return the file
        return FileResponse(path=stl_path, media_type='application/octet-stream', filename="Microfluidic_Geometry.stl")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-step")
async def download_step():
    step_path = "Microfluidic_Geometry.step"
    if not os.path.exists(step_path):
        raise HTTPException(status_code=404, detail="STEP file not found. Generate a model first.")
    return FileResponse(path=step_path, media_type='application/octet-stream', filename="Microfluidic_Geometry.step")

if __name__ == "__main__":
    import uvicorn
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
