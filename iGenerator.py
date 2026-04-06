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

    def plot_flow_path(self, points, distance, linewidths, include_extra=True):
        """
        Plot the flow path.
        Args:
            points: flow path coordinates
            distance: LSpace
            linewidths: LWidth
            include_extra: If True, draws border, inlet/outlet circles, and connectors (for UI/3D).
                          If False, draws only the channel pattern (for DL Prediction).
        """
        XGrid, YGrid = XGRID, YGRID
        fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=PATTERN_FIGSIZE, dpi=PATTERN_DPI)
        plt.subplots_adjust(wspace=0)

        if self.axis:
            for ax in [ax_left, ax_right]:
                ax.axis('off')

        x_coords, y_coords = zip(*points)
        outside_pattern, inside_pattern = self.offset(points, distance)
        
        # Metadata for extras
        Y_COOR_VAL = 142   #Default 139.5
        HOLE_RADIUS_PX = 150 #Default 150
        HOLE_RAD_COORD = HOLE_RADIUS_PX / 5.0

        for ax, mirror, xlim in zip([ax_right, ax_left], [1, -1], 
                                     [(0, XGrid), (-XGrid, 0)]):
            
            if include_extra:
                # 1. Draw Outer Channel Lines (individually adjustable)
                
                # X-direction channels (horizontal: top and bottom)
                x_channel_lw = linewidths * 5  # Adjust X channel linewidth here
                ax.plot([0, mirror * XGrid], [-YGrid/2, -YGrid/2], 'black', linewidth=x_channel_lw)  # Top
                ax.plot([0, mirror * XGrid], [YGrid/2, YGrid/2], 'black', linewidth=x_channel_lw)    # Bottom
                
                # Y-direction channels (vertical: left and right)
                y_left_lw = linewidths * 1.25   # Adjust Y-left channel linewidth here
                y_right_lw = linewidths * 2.5  # Adjust Y-right channel linewidth here
                ax.plot([0, 0], [-YGrid/2, YGrid/2], 'black', linewidth=y_left_lw)                     # Y-left (center edge)
                ax.plot([mirror * XGrid, mirror * XGrid], [-YGrid/2, YGrid/2], 'black', linewidth=y_right_lw)  # Y-right (outer edge)

                # 2. Draw Inlet and Outlet Circles
                inlet_circle = plt.Circle((mirror * points[0][0], -Y_COOR_VAL), HOLE_RAD_COORD, color='black', fill=True)
                outlet_circle = plt.Circle((mirror * points[-1][0], Y_COOR_VAL), HOLE_RAD_COORD, color='black', fill=True)
                ax.add_patch(inlet_circle)
                ax.add_patch(outlet_circle)

                # 3. Draw Vertical connectors to inlet/outlet
                ax.plot([mirror * points[0][0], mirror * points[0][0]], [points[0][1], -Y_COOR_VAL], 'black', linewidth=linewidths)
                ax.plot([mirror * points[-1][0], mirror * points[-1][0]], [points[-1][1], Y_COOR_VAL], 'black', linewidth=linewidths)

            # 4. Draw main path
            ax.plot(mirror * np.array(x_coords), np.array(y_coords), 
                   'black', linestyle='-', linewidth=linewidths)
            
            # 5. Draw fill patterns
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
            tuple: (predictions, dl_input_img, img_output_buf, selected_points)
        """
        variables = self.variables
        
        # 1. Generate CLEAN image for prediction ONLY (no border/circles)
        img_for_model_buf = self.plot_flow_path(
            selected_points, 
            distance=variables['LSpace'], 
            linewidths=variables['LWidth'],
            include_extra=False
        )
        dl_input_img = self.process_image(img_for_model_buf)
        
        # 2. Generate FULL image for visualization (with border/circles)
        img_output_buf = self.plot_flow_path(
            selected_points, 
            distance=variables['LSpace'], 
            linewidths=variables['LWidth'],
            include_extra=True
        )
        
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
        
        return predictions, dl_input_img, img_output_buf, selected_points