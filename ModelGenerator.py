"""
3D model generation from image slices.
Contains ModelGenerator3D and ModelViewerPopup classes.
"""

# ==========================================================================================
# SECTION 1: IMPORT LIBRARIES AND CONFIGURATION
# ==========================================================================================
import os
import numpy as np
import io
from PIL import Image
from Repository.vox2STL import vox2stl

# Default pattern image dimensions
PATTERN_WIDTH = 1125
PATTERN_HEIGHT = 1800

# Pattern coordinate system
XGRID = 112.5
YGRID = 360

# Inlet/Outlet position control
Y_COOR = 142  # Y coordinate offset for inlet/outlet positions (Default 139.5)
HOLE_RADIUS = 58  # Radius of inlet/outlet holes in pixels (Default 58 - Not in PX)
BORDER_WIDTH = 10  # Width of white border added to middle mask

# ==========================================================================================
# SECTION 2: MODEL GENERATOR CLASS
# ==========================================================================================
class ModelGenerator3D:
    """Handles 3D model generation from image masks."""
    
    def __init__(self, slices_folder="Repository"):
        self.slices_folder = slices_folder
        self.image_files = {
            "upper": "MUpper_Mask.png",
            "middle": "MMiddle_Mask.png",
            "bottom": "MBottom_Mask.png"
        }
    
    def get_pimage_size(self, pattern_image_buf):
        """Get the size of the pattern image.
        
        Args:
            pattern_image_buf: BytesIO buffer containing the pattern image
            
        Returns:
            tuple: (width, height) in pixels
        """
        pattern_image_buf.seek(0)
        with Image.open(pattern_image_buf) as img:
            size = img.size
        pattern_image_buf.seek(0)
        return size
    
    def add_border(self, image_buf, border_width=BORDER_WIDTH):
        """Add white border around the image to ensure microfluidic channels are covered.
        The border is added inward, keeping the image size the same.
        
        Args:
            image_buf: BytesIO buffer containing the image
            border_width: Width of the border in pixels (default: from config)
            
        Returns:
            BytesIO: Buffer containing the image with white border
        """
        image_buf.seek(0)
        img = Image.open(image_buf).convert('L')
        img_array = np.array(img, dtype=np.uint8)
        
        # Create white border by setting edge pixels to white (255)
        # Top border
        img_array[:border_width, :] = 255
        # Bottom border
        img_array[-border_width:, :] = 255
        # Left border
        img_array[:, :border_width] = 255
        # Right border
        img_array[:, -border_width:] = 255
        
        # Convert back to image
        bordered_img = Image.fromarray(img_array, mode='L')
        
        # Save to new buffer
        buf = io.BytesIO()
        bordered_img.save(buf, format='png')
        buf.seek(0)
        return buf
    
    def generate_bottom_mask(self, width, height):
        """Generate a fully white bottom image (solid material).
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            BytesIO: Buffer containing the white (solid) image
        """
        # Create fully white image (white = solid material)
        img_array = np.ones((height, width), dtype=np.uint8) * 255
        img = Image.fromarray(img_array, mode='L')
        
        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format='png')
        buf.seek(0)
        return buf
    
    def generate_upper_mask(self, width, height, inlet_pos=None, outlet_pos=None, hole_radius=HOLE_RADIUS):
        """Generate upper mask with white background (solid) and black circles (void) for inlet/outlet.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            inlet_pos: (x, y) position for inlet hole in pattern coordinates (optional)
            outlet_pos: (x, y) position for outlet hole in pattern coordinates (optional)
            hole_radius: Radius of the holes in pixels (default: from config)
            
        Returns:
            BytesIO: Buffer containing the upper image
        """
        # Create white background (white = solid material)
        img_array = np.ones((height, width), dtype=np.uint8) * 255
        
        # Pattern coordinate system: XGrid=112.5, YGrid=360
        # Pattern image has two mirrored sides, so we need to place holes on both sides
        XGrid, YGrid = XGRID, YGRID
        
        # Calculate scaling factors from pattern coordinates to image pixels
        # Pattern image width represents 2*XGrid (left + right sides)
        # Pattern image height represents YGrid
        scale_x = width / (2 * XGrid)  # Total width covers both sides
        scale_y = height / YGrid
        
        # Default positions based on pattern layout
        # Inlet is typically at the top, outlet at the bottom
        # In pattern coordinates: inlet around (0, -YGrid/2), outlet around (0, YGrid/2)
        
        # Determine inlet position
        if inlet_pos is None:
            # Use default position based on Y_COOR
            inlet_x_pattern = 0
            inlet_y_pattern = -Y_COOR
        else:
            # Use x-coordinate from flow path, but y-coordinate from Y_COOR to control vertical position
            inlet_x_pattern = inlet_pos[0]  # Use x from flow path
            inlet_y_pattern = -Y_COOR  # Use Y_COOR for y (ignore flow path y)
        
        # Determine outlet position
        if outlet_pos is None:
            # Use default position based on Y_COOR
            outlet_x_pattern = 0
            outlet_y_pattern = Y_COOR
        else:
            # Use x-coordinate from flow path, but y-coordinate from Y_COOR to control vertical position
            outlet_x_pattern = outlet_pos[0]  # Use x from flow path
            outlet_y_pattern = Y_COOR  # Use Y_COOR for y (ignore flow path y)
       
        # Convert pattern coordinates to image pixel coordinates
        # Pattern x=0 is at the center, so we offset by XGrid
        # Pattern y=-YGrid/2 is at top, y=YGrid/2 is at bottom
        inlet_x_pixel = int((inlet_x_pattern + XGrid) * scale_x)
        inlet_y_pixel = int((inlet_y_pattern + YGrid / 2) * scale_y)
        outlet_x_pixel = int((outlet_x_pattern + XGrid) * scale_x)
        outlet_y_pixel = int((outlet_y_pattern + YGrid / 2) * scale_y)
        
        # Create black circles for inlet and outlet (black = void/holes) on both left and right sides
        y_coords, x_coords = np.ogrid[:height, :width]
        
        # Inlet circles (black = void) - one on left side, one on right side
        # Left side inlet
        left_inlet_x = inlet_x_pixel
        inlet_mask_left = (x_coords - left_inlet_x)**2 + (y_coords - inlet_y_pixel)**2 <= hole_radius**2
        img_array[inlet_mask_left] = 0  # Black = void (hole)
        
        # # Right side inlet (mirrored)
        # right_inlet_x = width - inlet_x_pixel
        # inlet_mask_right = (x_coords - right_inlet_x)**2 + (y_coords - inlet_y_pixel)**2 <= hole_radius**2
        # img_array[inlet_mask_right] = 0  # Black = void (hole)
        
        # Outlet circles (black = void) - one on left side, one on right side
        # Left side outlet
        left_outlet_x = outlet_x_pixel
        outlet_mask_left = (x_coords - left_outlet_x)**2 + (y_coords - outlet_y_pixel)**2 <= hole_radius**2
        img_array[outlet_mask_left] = 0  # Black = void (hole)
        
        # # Right side outlet (mirrored)
        # right_outlet_x = width - outlet_x_pixel
        # outlet_mask_right = (x_coords - right_outlet_x)**2 + (y_coords - outlet_y_pixel)**2 <= hole_radius**2
        # img_array[outlet_mask_right] = 0  # Black = void (hole)
        
        img = Image.fromarray(img_array, mode='L')
        
        # Save to buffer
        buf = io.BytesIO()
        img.save(buf, format='png')
        buf.seek(0)
        return buf
    
    def load_and_preprocess_image(self, image_path=None, image_buf=None):
        """Load image and convert to grayscale array for voxel processing.
        
        Color interpretation:
        - Black (0) = void (empty space, no material)
        - White (255) = solid (material, creates geometry)
        
        Args:
            image_path: Path to image file (optional)
            image_buf: BytesIO buffer containing image (optional)
        """
        if image_buf is not None:
            img = np.array(Image.open(image_buf).convert('RGB').convert('L'))
        elif image_path is not None:
            img = np.array(Image.open(image_path).convert('RGB').convert('L'))
        else:
            raise ValueError("Either image_path or image_buf must be provided")
        # No inversion: black = void, white = solid
        return img.astype(np.uint8)
    
    def create_region_slices(self, image_path=None, image_buf=None, thickness=1):
        """Create a region by repeating an image multiple times.
        
        Args:
            image_path: Path to image file (optional)
            image_buf: BytesIO buffer containing image (optional)
            thickness: Number of slices to create
        """
        if image_buf is not None:
            base_slice = self.load_and_preprocess_image(image_buf=image_buf)
        elif image_path is not None:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            base_slice = self.load_and_preprocess_image(image_path=image_path)
        else:
            raise ValueError("Either image_path or image_buf must be provided")
        return [base_slice.copy() for _ in range(thickness)]
    
    def pad_slices_to_same_size(self, slices):
        """Pad all slices to the same dimensions."""
        if not slices:
            return []
        max_h = max(s.shape[0] for s in slices)
        max_w = max(s.shape[1] for s in slices)
        padded = []
        for s in slices:
            pad = np.zeros((max_h, max_w), dtype=s.dtype)
            pad[:s.shape[0], :s.shape[1]] = s
            padded.append(pad)
        return padded
    
    def create_3d_volume(self, all_slices):
        """Stack all slices into 3D voxel volume."""
        if len(all_slices) == 0:
            raise ValueError("No slices provided!")
        if len(all_slices) == 1:
            all_slices = [all_slices[0], all_slices[0].copy(), all_slices[0].copy()]
        
        padded_slices = self.pad_slices_to_same_size(all_slices)
        volume = np.stack(padded_slices, axis=0)
        
        if np.sum(volume > 0) == 0:
            raise ValueError("No solid voxels detected!")
        
        return volume.astype(np.uint8)
    
    def build_geometry(self, upper_thickness, middle_thickness, bottom_thickness, 
                                   middle_image_buf=None, inlet_pos=None, outlet_pos=None):
        """Build the complete microfluidic geometry with three regions.
        
        Args:
            upper_thickness: Number of slices for upper region
            middle_thickness: Number of slices for middle region
            bottom_thickness: Number of slices for bottom region
            middle_image_buf: Optional BytesIO buffer for custom middle pattern image
            inlet_pos: Optional (x, y) position for inlet hole in pattern coordinates
            outlet_pos: Optional (x, y) position for outlet hole in pattern coordinates
        """
        all_slices = []
        
        # Get pattern image size for generating upper and bottom images
        if middle_image_buf is not None:
            pattern_width, pattern_height = self.get_pimage_size(middle_image_buf)
        else:
            # Use default size from config
            pattern_width, pattern_height = PATTERN_WIDTH, PATTERN_HEIGHT
        
        # Generate upper image (white background = solid, black circles = void/holes for inlet/outlet)
        upper_image_buf = self.generate_upper_mask(
            pattern_width, pattern_height, 
            inlet_pos=inlet_pos, 
            outlet_pos=outlet_pos
        )
        all_slices.extend(self.create_region_slices(image_buf=upper_image_buf, thickness=upper_thickness))
        
        # Middle region (use custom pattern if provided, otherwise template)
        if middle_image_buf is not None:
            # Add white border to ensure microfluidic channels are covered at edges
            middle_image_buf = self.add_border(middle_image_buf, border_width=BORDER_WIDTH)
            # Use generated pattern from user input
            all_slices.extend(self.create_region_slices(image_buf=middle_image_buf, thickness=middle_thickness))
        else:
            # Use template image
            middle_path = os.path.join(self.slices_folder, self.image_files["middle"])
            if os.path.exists(middle_path):
                all_slices.extend(self.create_region_slices(image_path=middle_path, thickness=middle_thickness))
        
        # Generate bottom image (fully white = solid material)
        bottom_image_buf = self.generate_bottom_mask(pattern_width, pattern_height)
        all_slices.extend(self.create_region_slices(image_buf=bottom_image_buf, thickness=bottom_thickness))
        
        return all_slices
    
    def generate_model(self, upper_thickness, middle_thickness, bottom_thickness, 
                     apply_smoothing=False, output_filename="Microfluidic_Geometry", save_stl=False,
                     middle_image_buf=None, inlet_pos=None, outlet_pos=None):
        """Generate 3D model from slices.
        
        Args:
            upper_thickness: Number of slices for upper region
            middle_thickness: Number of slices for middle region
            bottom_thickness: Number of slices for bottom region
            apply_smoothing: Whether to apply smoothing
            output_filename: Output filename for STL
            save_stl: Whether to save STL file
            middle_image_buf: Optional BytesIO buffer for custom middle pattern image
            inlet_pos: Optional (x, y) position for inlet hole in pattern coordinates
            outlet_pos: Optional (x, y) position for outlet hole in pattern coordinates
        """
        all_slices = self.build_geometry(
            upper_thickness, middle_thickness, bottom_thickness, 
            middle_image_buf=middle_image_buf,
            inlet_pos=inlet_pos,
            outlet_pos=outlet_pos
        )
        if len(all_slices) == 0:
            raise ValueError("No slices found! Please check the slices folder.")
        
        volume = self.create_3d_volume(all_slices)
        model = vox2stl(vox=volume, loc='.', filename=output_filename, save=save_stl, smooth=apply_smoothing)
        return model, volume

# ==========================================================================================
# SECTION 3: MODEL VIEWER POPUP CLASS
# ==========================================================================================
class ModelViewerPopup:
    """Popup window for detailed 3D model visualization."""
    
    def __init__(self, parent, model):
        self.model = model
        self.window = tk.Toplevel(parent)
        self.window.title("3D Model Viewer - Detailed Visualization")
        self.window.geometry("1000x800")
        self.window.configure(bg='#f5f5f5')
        
        # Title
        tk.Label(self.window, text="3D Model Detailed View", font=('Arial', 16, 'bold'),
                bg='#f5f5f5', fg='black').pack(pady=10)
        
        # Controls
        controls_frame = tk.Frame(self.window, bg='#f5f5f5')
        controls_frame.pack(pady=5, padx=10, fill=tk.X)
        
        tk.Label(controls_frame, text="View Mode:", font=('Arial', 10, 'bold'),
                bg='#f5f5f5', fg='black').pack(side=tk.LEFT, padx=5)
        
        self.view_mode_var = tk.StringVar(value="solid")
        tk.OptionMenu(controls_frame, self.view_mode_var, "solid", "wireframe",
                     "solid + wireframe", command=self.update_view).pack(side=tk.LEFT, padx=5)
        
        # View buttons
        view_buttons = tk.Frame(controls_frame, bg='#f5f5f5')
        view_buttons.pack(side=tk.LEFT, padx=10)
        
        for text, command in [("XY", self.view_xy), ("XZ", self.view_xz),
                              ("YZ", self.view_yz), ("Reset", self.reset_view)]:
            tk.Button(view_buttons, text=text, command=command, bg='#87CEEB',
                     font=('Arial', 9), padx=5, pady=2).pack(side=tk.LEFT, padx=2)
        
        # Canvas
        canvas_frame = tk.Frame(self.window, bg='#e8e8e8')
        canvas_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.canvas = vispy.scene.SceneCanvas(keys='interactive', show=False,
                                             parent=canvas_frame, bgcolor='white')
        self.canvas.native.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.view = self.canvas.central_widget.add_view(bgcolor='white')
        self.canvas.show()
        self.use_vispy = True
        self.visualize_model_vispy()
    
    def visualize_model_vispy(self):
        """Visualize model using Vispy."""
        if self.view is not None:
            self.view.parent = None
        self.view = self.canvas.central_widget.add_view(bgcolor='white')
        
        vertices = self.model.vertices.astype('float32')
        faces = self.model.faces.astype('uint32')
        view_mode = self.view_mode_var.get()
        types = [s.strip() for s in view_mode.split('+')]
        
        for plot_type in types:
            if plot_type == "solid":
                model_visual = vispy.scene.visuals.Mesh(vertices=vertices, faces=faces,
                                                       shading='smooth', color='lightblue')
                self.view.add(model_visual)
            elif plot_type == "wireframe":
                n_faces = len(faces)
                ix = np.tile([0, 1, 1, 2, 2, 0], n_faces) + np.repeat(np.arange(0, 3*n_faces, 3), 6)
                edges = faces.reshape(-1)[ix]
                edge_visual = vispy.scene.visuals.Line(pos=vertices[edges], connect="segments",
                                                       color='darkblue', width=1)
                self.view.add(edge_visual)
        
        self.view.camera = vispy.scene.TurntableCamera(parent=self.view.scene)
        self.view.camera.set_range()
    
    def update_view(self, view_mode=None):
        """Update model view when view mode changes."""
        self.visualize_model_vispy()
    
    def view_xy(self):
        if self.use_vispy and self.view and self.view.camera:
            self.view.camera.elevation = 90
            self.view.camera.azimuth = -90
            self.view.camera.roll = 0
    
    def view_xz(self):
        if self.use_vispy and self.view and self.view.camera:
            self.view.camera.elevation = 0
            self.view.camera.azimuth = -90
            self.view.camera.roll = 0
    
    def view_yz(self):
        if self.use_vispy and self.view and self.view.camera:
            self.view.camera.elevation = 0
            self.view.camera.azimuth = 0
            self.view.camera.roll = 0
    
    def reset_view(self):
        if self.use_vispy and self.view and self.view.camera:
            self.view.camera.reset()
