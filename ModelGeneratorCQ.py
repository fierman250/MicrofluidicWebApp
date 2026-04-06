"""
True-MM Vector Solid Model Generator using CadQuery.
Generates industrial-grade STEP files and flawless STL files for the WebApp.
"""

import os
import numpy as np
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
import cadquery as cq

class ModelGeneratorCQ:
    def __init__(self, 
                 chip_width=25.0, 
                 chip_height=40.0,
                 glass_padding=1.0,
                 upper_thickness=0.4,
                 bottom_thickness=0.4,
                 inlet_diameter=6.0,
                 inlet_y_dist=16.5,
                 outer_x_thickness=0.6,
                 outer_y_thickness=0.8,
                 inner_bridge_thickness=0.5,
                 funnel_length_y=8.0,
                 funnel_length_x=6.0,
                 funnel_tangent_ratio=0.3,
                 is_dual_chip=False):
        self.chip_width = chip_width
        self.chip_height = chip_height
        self.glass_padding = glass_padding
        self.upper_thickness = upper_thickness
        self.bottom_thickness = bottom_thickness
        self.inlet_diameter = inlet_diameter
        self.inlet_y_dist = inlet_y_dist
        self.outer_x_thickness = outer_x_thickness
        self.outer_y_thickness = outer_y_thickness
        self.inner_bridge_thickness = inner_bridge_thickness
        self.funnel_length_y = funnel_length_y
        self.funnel_length_x = funnel_length_x
        self.funnel_tangent_ratio = funnel_tangent_ratio
        self.is_dual_chip = is_dual_chip

    def _clean_pts(self, coords):
        pts = []
        for p in coords:
            if not pts:
                pts.append(p)
            else:
                if np.linalg.norm(np.array(p) - np.array(pts[-1])) > 1e-5:
                    pts.append(p)
        if len(pts) > 1 and np.linalg.norm(np.array(pts[-1]) - np.array(pts[0])) < 1e-5:
            pts.pop()
        return pts

    def _extrude_polygon_to_cq(self, poly, height):
        ext_pts = self._clean_pts(list(poly.exterior.coords))
        wp = cq.Workplane("XY").polyline(ext_pts).close()
        for interior in poly.interiors:
            int_pts = self._clean_pts(list(interior.coords))
            if len(int_pts) >= 3:  
                wp = wp.polyline(int_pts).close()
        return wp.extrude(height)

    def _create_perimeter_fluid_channel(self, outer_w, outer_h, thick_x, thick_y):
        outer_box = box(-outer_w/2, -outer_h/2, outer_w/2, outer_h/2)
        inner_box = box(-(outer_w - 2*thick_x)/2, -(outer_h - 2*thick_y)/2, 
                        (outer_w - 2*thick_x)/2, (outer_h - 2*thick_y)/2)
        channel_ring = outer_box.difference(inner_box)
        return channel_ring, outer_box

    def _make_funnel_polygon(self, y_hole, direction, r, w, length, tangent_ratio):
        half_w = w / 2.0
        P0_L = (-r, y_hole)
        P3_L = (-half_w, y_hole + direction * length)
        P1_L = (-r, y_hole + direction * length * tangent_ratio)
        P2_L = (-half_w, y_hole + direction * length * tangent_ratio)
        
        P0_R = (r, y_hole)
        P3_R = (half_w, y_hole + direction * length)
        P1_R = (r, y_hole + direction * length * tangent_ratio)
        P2_R = (half_w, y_hole + direction * length * tangent_ratio)
        
        t = np.linspace(0, 1, 20)
        left_x = (1-t)**3 * P0_L[0] + 3*(1-t)**2 * t * P1_L[0] + 3*(1-t)*t**2 * P2_L[0] + t**3 * P3_L[0]
        left_y = (1-t)**3 * P0_L[1] + 3*(1-t)**2 * t * P1_L[1] + 3*(1-t)*t**2 * P2_L[1] + t**3 * P3_L[1]
        
        right_x = (1-t)**3 * P0_R[0] + 3*(1-t)**2 * t * P1_R[0] + 3*(1-t)*t**2 * P2_R[0] + t**3 * P3_R[0]
        right_y = (1-t)**3 * P0_R[1] + 3*(1-t)**2 * t * P1_R[1] + 3*(1-t)*t**2 * P2_R[1] + t**3 * P3_R[1]
        
        pts = []
        for lx, ly in zip(left_x, left_y):
            pts.append((lx, ly))
        for rx, ry in zip(right_x[::-1], right_y[::-1]):
            pts.append((rx, ry))
            
        return Polygon(pts)

    def _make_x_funnel_polygon(self, y_hole, manifold_inner_y, r, length, tangent_ratio):
        P0_R = (r, y_hole)
        P3_R = (r + length, manifold_inner_y)
        P1_R = (r, manifold_inner_y) 
        P2_R = (r + length * tangent_ratio, manifold_inner_y)  # Horizontal Tangency Focus
        
        t = np.linspace(0, 1, 20)
        rx = (1-t)**3 * P0_R[0] + 3*(1-t)**2 * t * P1_R[0] + 3*(1-t)*t**2 * P2_R[0] + t**3 * P3_R[0]
        ry = (1-t)**3 * P0_R[1] + 3*(1-t)**2 * t * P1_R[1] + 3*(1-t)*t**2 * P2_R[1] + t**3 * P3_R[1]
        
        pts = []
        for x, y in zip(rx, ry):
            pts.append((x, y))
            
        lx = -rx[::-1]
        ly = ry[::-1]
        for x, y in zip(lx, ly):
            pts.append((x, y))
            
        return Polygon(pts)

    def generate_model_cq(self, cwidth, cdepth, shapely_data, output_filename="Microfluidic_Geometry"):
        middle_thickness = cdepth
        total_thickness = self.bottom_thickness + middle_thickness + self.upper_thickness
        
        # 1. Base mathematical layouts
        buffer_dist = cwidth / 2.0
        all_paths = [shapely_data['main_path']]
        all_paths.extend(shapely_data['outside_pattern'])
        all_paths.extend(shapely_data['inside_pattern'])
        
        left_polys = [path.buffer(buffer_dist, cap_style=2, join_style=2) for path in all_paths]
        left_mask = unary_union(left_polys)
        
        # Prevent crossing mirror artifacts
        left_bounding_box = box(0.0, -self.chip_height*2, self.chip_width*2, self.chip_height*2)
        left_mask_chopped = left_mask.intersection(left_bounding_box)
        
        right_polys = []
        geoms = left_mask_chopped.geoms if hasattr(left_mask_chopped, 'geoms') else [left_mask_chopped]
        for g in geoms:
            coords = np.array(g.exterior.coords)
            mirrored = coords.copy()
            mirrored[:, 0] *= -1
            right_polys.append(Polygon(mirrored[::-1]))
            
        pattern_mask_2d = unary_union([left_mask_chopped] + right_polys)
        
        # 2. Construct Manifold, Bridge & Funnels
        manifold_w = self.chip_width
        manifold_h = self.chip_height
        
        perimeter_channel, manifold_outer_box = self._create_perimeter_fluid_channel(
            manifold_w, manifold_h, thick_x=self.outer_x_thickness, thick_y=self.outer_y_thickness
        )
        
        bridge_path = LineString([(0.0, -manifold_h/2), (0.0, manifold_h/2)])
        bridge_poly = bridge_path.buffer(self.inner_bridge_thickness / 2.0, cap_style=2, join_style=2)
        
        inlet_y = -self.inlet_y_dist
        outlet_y = self.inlet_y_dist
        
        funnel_inlet_y = self._make_funnel_polygon(y_hole=inlet_y, direction=1, r=self.inlet_diameter/2.0, w=self.inner_bridge_thickness, length=self.funnel_length_y, tangent_ratio=self.funnel_tangent_ratio)
        funnel_outlet_y = self._make_funnel_polygon(y_hole=outlet_y, direction=-1, r=self.inlet_diameter/2.0, w=self.inner_bridge_thickness, length=self.funnel_length_y, tangent_ratio=self.funnel_tangent_ratio)
        
        manifold_inner_y_top = (manifold_h / 2.0) - self.outer_y_thickness
        manifold_inner_y_bot = -(manifold_h / 2.0) + self.outer_y_thickness
        
        funnel_outlet_x = self._make_x_funnel_polygon(y_hole=outlet_y, manifold_inner_y=manifold_inner_y_top, r=self.inlet_diameter/2.0, length=self.funnel_length_x, tangent_ratio=self.funnel_tangent_ratio)
        funnel_inlet_x = self._make_x_funnel_polygon(y_hole=inlet_y, manifold_inner_y=manifold_inner_y_bot, r=self.inlet_diameter/2.0, length=self.funnel_length_x, tangent_ratio=self.funnel_tangent_ratio)
        
        pattern_mask_clipped = pattern_mask_2d.intersection(manifold_outer_box)
        
        channels_mask_2d = unary_union([
            pattern_mask_clipped, perimeter_channel, bridge_poly, 
            funnel_inlet_y, funnel_outlet_y, 
            funnel_inlet_x, funnel_outlet_x
        ])
        
        
        # 3. OpenCASCADE Solid Builder
        # Step 1: Create the base chip body (core 25x40 frame)
        chip = cq.Workplane("XY").box(self.chip_width, self.chip_height, total_thickness).translate((0, 0, total_thickness/2.0))
        
        def cut_polygon_from_chip(master_chip, poly):
            if poly.is_empty or poly.geom_type != 'Polygon':
                return master_chip
            solid = self._extrude_polygon_to_cq(poly, middle_thickness)
            solid = solid.translate((0, 0, self.bottom_thickness))
            return master_chip.cut(solid)

        if hasattr(channels_mask_2d, 'geoms'):
            for p in channels_mask_2d.geoms:
                chip = cut_polygon_from_chip(chip, p)
        else:
            chip = cut_polygon_from_chip(chip, channels_mask_2d)
        
        # 4. Drilling analytical holes
        hole_centers = [
            (0.0, inlet_y),   
            (0.0, outlet_y),  
        ]
        
        holes_start_z = total_thickness + 1.0
        drill_depth = 1.0 + self.upper_thickness + middle_thickness
        hole_radius = self.inlet_diameter / 2.0
        
        holes = (
            cq.Workplane("XY")
            .workplane(offset=holes_start_z)
            .pushPoints(hole_centers)
            .circle(hole_radius)
            .extrude(-drill_depth) 
        )
        chip = chip.cut(holes)
        
        # --- MIRROR OPERATION ---
        if self.is_dual_chip:
            # Since the chip is centered, move it so the left edge (X = -12.5) is at X = 0
            shift_x = self.chip_width / 2.0
            center_space = 0.5 / 2.0
            chip = chip.translate((shift_x + center_space, 0, 0))
            # Mirror across the origin's YZ plane and union
            chip = chip.mirror("YZ", union=True)
            
            # --- FILL THE CENTER HOLE ---
            filler = (
                cq.Workplane("XY")
                .box(center_space * 2, self.chip_height, total_thickness)
                .translate((0, 0, total_thickness / 2.0))
            )
            chip = chip.union(filler)

        # --- ADD PADDING AFTER MIRROR ---
        if self.glass_padding > 0:
            # Calculate final assembly width (one chip or dual + center space)
            if self.is_dual_chip:
                base_total_w = (self.chip_width * 2) + 0.5
            else:
                base_total_w = self.chip_width
            base_total_h = self.chip_height
            
            final_w = base_total_w + (2 * self.glass_padding)
            final_h = base_total_h + (2 * self.glass_padding)
            
            # Create a hollow frame to avoid filling internal holes/channels
            frame = (
                cq.Workplane("XY")
                .box(final_w, final_h, total_thickness)
                .cut(cq.Workplane("XY").box(base_total_w, base_total_h, total_thickness + 1.0))
                .translate((0, 0, total_thickness / 2.0))
            )
            # Union the frame with our assembly
            chip = chip.union(frame)
        
        # 5. Saving pure mathematical STEP + STL file
        out_step = f"{output_filename}.step"
        out_stl = f"{output_filename}.stl"
        
        cq.exporters.export(chip, out_step)
        cq.exporters.export(chip, out_stl)
        
        return chip, out_step, out_stl
