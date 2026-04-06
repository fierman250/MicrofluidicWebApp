import os
import io
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Tuple
from iGenerator import iGenerator
from ModelGenerator import ModelGenerator3D

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

@app.post("/api/generate-model")
async def generate_model(request: PredictionRequest):
    try:
        # 1. First, regenerate the flow path image since we need it for the middle mask
        igen = iGenerator(request.cdepth, request.cwidth, request.cspace)
        Cnums = igen.get_cnums()
        variables = igen.variables
        
        # Calculate bases
        xbasic = ((request.cwidth * Cnums) + (request.cspace * Cnums)) * 10
        ybasic = ((request.cwidth * Cnums) + (request.cspace * Cnums)) * 10
        
        physical_points = interpret_points_backend(request.selected_points, xbasic, ybasic)
        
        # Get the flow path image buffer
        img_input_buf = igen.plot_flow_path(
            physical_points,
            distance=variables['LSpace'],
            linewidths=variables['LWidth']
        )
        
        # Determine inlet and outlet positions
        inlet_pos = None
        outlet_pos = None
        if len(physical_points) > 0:
            inlet_pos = physical_points[0]
            outlet_pos = physical_points[-1]
            
        # 2. Generate the 3D Model
        model_gen = ModelGenerator3D(slices_folder="Repository")
        output_filename = "Microfluidic_Geometry"
        
        model, volume = model_gen.generate_model(
            upper_thickness=4, 
            middle_thickness=4, 
            bottom_thickness=4,
            apply_smoothing=False, 
            output_filename=output_filename, 
            save_stl=True,  # We want to save it so we can return the file
            middle_image_buf=img_input_buf,
            inlet_pos=inlet_pos,
            outlet_pos=outlet_pos
        )
        
        stl_path = f"{output_filename}.stl"
        if not os.path.exists(stl_path):
            raise FileNotFoundError("STL file was not created properly.")
            
        # 3. Return the generic file response
        return FileResponse(path=stl_path, media_type='application/octet-stream', filename="Microfluidic_Geometry.stl")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
