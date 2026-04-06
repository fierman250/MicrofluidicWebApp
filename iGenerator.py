"""
Flow path generation and deep learning prediction.
Contains iGenerator class.
"""

# ==========================================================================================
# SECTION 1: IMPORT LIBRARIES AND CONFIGURATION
# ==========================================================================================
import os
import numpy as np
import io
import torch
import joblib
from PIL import Image, ImageOps
from torchvision.transforms import ToTensor
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from Repository.cnums_lookup import cnums_lookup
from Repository.pointinterpreter import get_points_sets
from Repository.DLModel import CombinedNet

# Pattern coordinate system
XGRID = 112.5
YGRID = 360

# Pattern generation settings
PATTERN_FIGSIZE = (11.25, 18)  # Figure size in inches
PATTERN_DPI = 100  # DPI for pattern generation
PATTERN_SAVE_DPI = 50  # DPI for saving pattern image

DL_MODEL = 'TRCodev3GA-Run2'

# ==========================================================================================
# SECTION 2: iGenerator CLASS
# ==========================================================================================
class iGenerator:
    """
    Generator class for creating flow path visualizations and making predictions.
    """
    
    def __init__(self, cdepth, cwidth, cspace):
        """Initialize the iGenerator with given channel parameters."""
        self.cdepth = cdepth
        self.cwidth = cwidth
        self.cspace = cspace
        self.axis = True
        self.image_shape = (int(480 * 0.625), 480)  # (300, 480)
        self.variables = self.calc_variables()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_model_and_scaler()

    def get_cnums(self):
        """Retrieve the cnums based on the given width and space."""
        return cnums_lookup.get((self.cwidth, self.cspace), "No match found")

    def offset(self, points, distance):
        """Create offset lines for the given points at specified distances."""
        line = LineString(points)
        outside_pattern = [line.parallel_offset(i * distance, 'left', join_style=2) 
                          for i in range(1, 40)]
        inside_pattern = [line.parallel_offset(i * distance, 'right', join_style=2) 
                         for i in range(1, 40)]
        return outside_pattern, inside_pattern

    def plot_flow_path(self, points, distance, linewidths):
        """Plot the flow path based on the given points, distance, and line widths."""
        XGrid, YGrid = XGRID, YGRID
        fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=PATTERN_FIGSIZE, dpi=PATTERN_DPI)
        plt.subplots_adjust(wspace=0)

        if self.axis:
            for ax in [ax_left, ax_right]:
                ax.axis('off')

        x_coords, y_coords = zip(*points)
        outside_pattern, inside_pattern = self.offset(points, distance)
        
        for ax, mirror, xlim in zip([ax_right, ax_left], [1, -1], 
                                     [(0, XGrid), (-XGrid, 0)]):
            ax.plot(mirror * np.array(x_coords), np.array(y_coords), 
                   'black', linestyle='-', linewidth=linewidths)
            for pattern in [outside_pattern, inside_pattern]:
                for line in pattern:
                    ax.plot(mirror * np.array(line.coords.xy[0]), 
                           np.array(line.coords.xy[1]), 
                           'black', linestyle='-', linewidth=linewidths)
            ax.set_xlim(xlim)
            ax.set_ylim(-YGrid / 2, YGrid / 2)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=PATTERN_SAVE_DPI, bbox_inches='tight', pad_inches=0.02)
        buf.seek(0)
        plt.close(fig)
        return buf

    def calc_variables(self):
        """Calculate various parameters including grid dimensions and spacing."""
        Cnums = self.get_cnums()
        xbasic = ((self.cwidth * Cnums) + (self.cspace * Cnums)) * 10
        ybasic = ((self.cwidth * Cnums) + (self.cspace * Cnums)) * 10
        LWidth = round((29.5 * self.cwidth) - 0.75, 2)
        LSpace = round((self.cspace + self.cwidth) * 10, 2)
        points_sets = get_points_sets(xbasic, ybasic)
        return {
            'points_sets': points_sets,
            'LWidth': LWidth,
            'LSpace': LSpace
        }

    def process_image(self, buf):
        """Process the image from buffer, convert to grayscale, and apply padding."""
        image = Image.open(buf).convert("L")
        padded_image = ImageOps.expand(image, border=10, fill=0)
        resized_image = padded_image.resize(self.image_shape)
        img_array = ToTensor()(resized_image)
        img_array = img_array.unsqueeze(0)
        return img_array

    def load_model_and_scaler(self):
        """Load the pre-trained DL model and scaler from the Repository directory."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_dir = os.path.join(script_dir, 'Repository')
        model_path = os.path.join(repo_dir, f'best_model_{DL_MODEL}.pth')
        scaler_path = os.path.join(repo_dir, f'best_scaler_{DL_MODEL}.pkl')
        
        self.dl_model = CombinedNet().to(self.device)
        self.dl_model.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.dl_model.eval()
        self.y_scaler = joblib.load(scaler_path)

    def get_prediction(self, selected_points, nparams):
        """
        Generate prediction for all 12 material properties using custom points.
        
        Args:
            selected_points (list): List of (x, y) coordinate tuples for the flow path
            nparams (list): Numerical parameters [cdepth, cwidth, cspace]
            
        Returns:
            tuple: (predictions, dl_input_img, img_input_buf, selected_points)
        """
        variables = self.variables
        
        # Generate flow path visualization using provided points
        img_input_buf = self.plot_flow_path(
            selected_points, 
            distance=variables['LSpace'], 
            linewidths=variables['LWidth']
        )
        
        # Process image for model input
        dl_input_img = self.process_image(img_input_buf)
        
        # Prepare numerical parameters as tensor
        nparams_tensor = torch.tensor(
            np.array(nparams).reshape(1, -1), 
            dtype=torch.float32
        )

        # Make prediction with model
        with torch.no_grad():
            outputs = self.dl_model(
                dl_input_img.to(self.device), 
                nparams_tensor.to(self.device)
            )
        
        # Inverse transform all 12 properties from scaled output
        predictions = []
        for i in range(12):
            pred = (outputs[0][i].item() * self.y_scaler.scale_[i] + 
                   self.y_scaler.center_[i])
            predictions.append(pred)
        
        return predictions, dl_input_img, img_input_buf, selected_points