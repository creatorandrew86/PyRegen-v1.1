import dearpygui.dearpygui as dpg
import ctypes

# Resize nozzle type inputs
def _resize_nozzle_type_inputs():
    if not dpg.does_item_exist("input_nozzle_angle"):
        return
    
    cell_width = dpg.get_item_width("main_window") / 4
    label_w = 30
    checkbox_w = 20
    input_w = int((cell_width - label_w - checkbox_w - 40) * 0.5)

    dpg.configure_item("input_nozzle_angle", width=input_w)
    dpg.configure_item("input_nozzle_length_percentage", width=input_w)

# Resize the throat-sizing inputs
def _resize_throat_sizing_inputs():
    if not dpg.does_item_exist("input_mass_flow_rate"):
        return
    
    cell_width = dpg.get_item_width("main_window") / 4

    input_w = cell_width * 0.35
    unit_w = cell_width * 0.18

    dpg.configure_item("input_mass_flow_rate", width=input_w)
    dpg.configure_item("input_Rt", width=input_w)

    dpg.configure_item("unit_mass_flow_rate", width=unit_w)
    dpg.configure_item("unit_Rt", width=unit_w)

# Resize the wall material inputs 
def _resize_wall_material_inputs():
    if not dpg.does_item_exist("input_wall_material"):
        return

    cell_width = dpg.get_item_width("main_window") / 4

    wall_material_combo_w  = int(cell_width * 0.29)
    wall_thickness_input_w = int(cell_width * 0.25)
    wall_thickness_unit_w  = 53

    dpg.configure_item("input_wall_material",  width=wall_material_combo_w)
    dpg.configure_item("input_wall_thickness", width=wall_thickness_input_w)
    dpg.configure_item("unit_wall_thickness",  width=wall_thickness_unit_w)


# Rulers
def _draw_horizontal_ruler(nozzle_length_m, scale_x, draw_area_left, axis_line_y):
    num_horizontal_ticks = 14
    ruler_baseline_y     = axis_line_y
    tick_height          = 8
    label_y_offset       = 12

    # Baseline
    dpg.draw_line(
        (draw_area_left, ruler_baseline_y),
        (draw_area_left + nozzle_length_m * scale_x, ruler_baseline_y),
        color=(180, 180, 180), thickness=2, parent="nozzle_canvas"
    )

    step_m = nozzle_length_m / num_horizontal_ticks

    for i in range(num_horizontal_ticks + 1):
        x_value_m = i * step_m
        pixel_x   = draw_area_left + x_value_m * scale_x

        is_endpoint = (i == 0 or i == num_horizontal_ticks)
        tick_h      = tick_height * 1.5 if is_endpoint else tick_height
        tick_color  = (220, 180, 80) if is_endpoint else (180, 180, 180)

        dpg.draw_line((pixel_x, ruler_baseline_y), (pixel_x, ruler_baseline_y + tick_h), color=tick_color, thickness=2, parent="nozzle_canvas")
        dpg.draw_text((pixel_x - 14, ruler_baseline_y + label_y_offset), f"{round(x_value_m * 100)}cm", size=13, color=tick_color, parent="nozzle_canvas")

def _draw_vertical_ruler(nozzle_max_radius_m, scale_r, axis_line_y, vertical_ruler_width):
    num_vertical_ticks  = 5
    ruler_baseline_x    = vertical_ruler_width
    tick_width          = 8
    label_x_offset      = 5

    total_radius_height = nozzle_max_radius_m * scale_r
    ruler_top_y         = axis_line_y - total_radius_height

    # Baseline (vertical line)
    dpg.draw_line((ruler_baseline_x, axis_line_y), (ruler_baseline_x, ruler_top_y), color=(180, 180, 180), thickness=2, parent="nozzle_canvas")

    step_r_m = nozzle_max_radius_m / num_vertical_ticks

    for i in range(num_vertical_ticks + 1):
        r_value_m = i * step_r_m
        pixel_y   = axis_line_y - r_value_m * scale_r

        is_endpoint = (i == 0 or i == num_vertical_ticks)
        tick_w      = tick_width * 1.5 if is_endpoint else tick_width
        tick_color  = (220, 180, 80) if is_endpoint else (180, 180, 180)

        dpg.draw_line((ruler_baseline_x, pixel_y), (ruler_baseline_x - tick_w, pixel_y),color=tick_color, thickness=2, parent="nozzle_canvas")
        dpg.draw_text((label_x_offset, pixel_y - 7), f"{round(r_value_m * 100)}cm", size=13, color=tick_color, parent="nozzle_canvas")





# Live resize of main window
def resize_main_window(sender=None, app_data=None, user_data=None):
    if not dpg.does_item_exist("main_window"):
        return
    dpg.set_item_pos("main_window", [0, 0])
    dpg.set_item_width("main_window", dpg.get_viewport_client_width())
    dpg.set_item_height("main_window", dpg.get_viewport_client_height())

    _resize_nozzle_type_inputs()
    _resize_throat_sizing_inputs()
    _resize_wall_material_inputs()

    if user_data is not None and user_data["nozzle_parameters"]["x"] is not None:
        update_nozzle_canvas(user_data)


# Sizing and centering the viewport
def center_viewport_on_screen():
    user32 = ctypes.windll.user32
    screen_width  = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    vp_width = screen_width * 0.9
    vp_height = screen_height * 0.75

    dpg.set_viewport_width(width=vp_width)
    dpg.set_viewport_height(height=vp_height)

    dpg.set_viewport_pos([(screen_width - vp_width) // 2, (screen_height - vp_height) // 2])
    dpg.set_viewport_pos([200, 80])



# Live update nozzle canvas
def update_nozzle_canvas(state: dict):
    dpg.delete_item("nozzle_canvas", children_only=True)

    x_array = state["nozzle_parameters"]["x"]
    Rx_array = state["nozzle_parameters"]["R_x"]

    vertical_ruler_width = 50
    margin_top = 5
    margin_right = 30
    margin_bottom = 40

    draw_area_left = vertical_ruler_width
    draw_area_top = margin_top

    x_min, x_max = float(min(x_array)), float(max(x_array))
    nozzle_length_m = x_max - x_min
    nozzle_max_radius_m = float(max(Rx_array))

    size = dpg.get_item_rect_size("nozzle_canvas_window")
    canvas_width = size[0]

    if canvas_width == 0:
        return

    # Scale the drawing and canvas
    draw_area_width = canvas_width - vertical_ruler_width - margin_right
    draw_area_height = draw_area_width * nozzle_max_radius_m / nozzle_length_m
    canvas_height = int(draw_area_top + draw_area_height + margin_bottom)

    dpg.configure_item("nozzle_canvas", width=canvas_width, height=canvas_height)

    scale_x = draw_area_width  / nozzle_length_m
    scale_r = draw_area_height * 0.75 / nozzle_max_radius_m

    # Axis line
    axis_line_y = draw_area_top + draw_area_height * 0.85

    def to_pixel(x_m, r_m):
        pixel_x = draw_area_left + (x_m - x_min) * scale_x
        pixel_y = axis_line_y - r_m * scale_r
        return pixel_x, pixel_y

    # Draw axis line
    dpg.draw_line((draw_area_left, axis_line_y), (draw_area_left + draw_area_width, axis_line_y), color=(100, 100, 100), thickness=1, parent="nozzle_canvas")

    # Draw nozzle contour
    contour_pixels = [to_pixel(x, r) for x, r in zip(x_array, Rx_array)]
    dpg.draw_polyline(contour_pixels, color=(200, 200, 200), thickness=2, parent="nozzle_canvas")

    # Draw rulers
    _draw_horizontal_ruler(nozzle_length_m, scale_x, draw_area_left, axis_line_y)
    _draw_vertical_ruler(nozzle_max_radius_m, scale_r, axis_line_y, vertical_ruler_width)