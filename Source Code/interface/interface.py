import dearpygui.dearpygui as dpg
from pathlib import Path
import ctypes

from output.files import write_full_cea_output, write_full_pyregen_output
from output.graphs import main_graph, nozzle_graph


oxidizer_items = ["LOX", "GOX", "N2O4", "N2O", "IRFNA", "H2O2", "Peroxide90", "Peroxide98", "MON3", "MON15", "MON25"]
fuel_items = ["RP1", "LH2", "CH4", "MMH", "N2H4", "UDMH", "A50", "Ethanol", "Methanol", "GH2", "GCH4", "JetA", "JP10"]
coolant_items = ["Hydrogen", "Methane", "Ethane", "Ethanol", "Methanol", "Water", "Ammonia", "Nitrogen", "Helium", "Oxygen", "n-Dodecane", "n-Decane", "n-Octane"]

wall_material_items = ["Copper", "GRCop 42", "GRCop 84"]
interpolation_type_items = ["Linear", "Piecewise Constant"]

graph_x_items = ["Axial position (x) (cm)", "Cold wall temperature (K)", "Hot wall temperature (K)", "Heat flux (MW/m²)", "Coolant temperature (K)", "Coolant pressure (bar)", "Coolant velocity (m/s)", "Coolant Re"]
graph_y_items = ["Cold wall temperature (K)", "Hot wall temperature (K)", "Gas HTC (×10⁴ W/m²K)", "Coolant HTC (×10⁴ W/m²K)", "Heat flux (MW/m²)", "Coolant temperature (K)", "Coolant pressure (bar)", "Coolant velocity (m/s)", "Coolant Re", "Channel width (mm)", "Channel height (mm)", "Landwidth (mm)"]

pressure_drop_model_items = ["Colebrook-Petukhov", "Filonenko-Petukhov", "Colebrook"]
cold_side_model_items = ["Sieder-Tate", "Bishop et al.", "Jackson", "Dittus-Boelter", "Gnielinski"]
hot_side_model_items = ["Bartz", "Bartz Corrected"]
wall_model_items = ["1D"]

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "Inter-VariableFont_opsz,wght.ttf"



# Getter functions for retrieving input values from the interface

def get_inputs_on_generate() -> dict:
    return {
        "oxidizer" : dpg.get_value("input_oxidizer"),
        "fuel" : dpg.get_value("input_fuel"),
        "Pc" : dpg.get_value("input_Pc"),
        "unit_Pc" : dpg.get_value("unit_Pc"),
        "MR" : dpg.get_value("input_MR"),
        "throat_sizing_method" : "mass_flow" if dpg.get_value("check_mass_flow_rate") else "given_radius" if dpg.get_value("check_Rt") else None,
        "mass_flow_rate" : dpg.get_value("input_mass_flow_rate"),
        "unit_mass_flow_rate" : dpg.get_value("unit_mass_flow_rate"),
        "Rt" : dpg.get_value("input_Rt"),
        "unit_Rt" : dpg.get_value("unit_Rt"),
        "eps" : dpg.get_value("input_eps"),
        "CR" : dpg.get_value("input_CR"),
        "L_star" : dpg.get_value("input_L_star"),
        "unit_L_star" : dpg.get_value("unit_L_star"),
        "nozzle_type" : "conical" if dpg.get_value("check_conical") else "bell" if dpg.get_value("check_bell") else None,
        "nozzle_length_percentage" : dpg.get_value("input_nozzle_length_percentage"),
        "nozzle_angle" : dpg.get_value("input_nozzle_angle"),
        "nozzle_resolution" : dpg.get_value("input_nozzle_resolution"),
    }

def get_inputs_on_solve() -> dict:
    return {
        "coolant" : dpg.get_value("input_coolant"),
        "coolant_mass_flow_rate" : dpg.get_value("input_coolant_mass_flow"),
        "unit_coolant_mass_flow_rate" : dpg.get_value("unit_mass_flow_rate"),
        "coolant_inlet_temperature" : dpg.get_value("input_coolant_inlet_temperature"),
        "unit_coolant_inlet_temperature" : dpg.get_value("unit_coolant_inlet_temperature"),
        "coolant_inlet_pressure" : dpg.get_value("input_coolant_inlet_pressure"),
        "unit_coolant_inlet_pressure" : dpg.get_value("unit_coolant_inlet_pressure"),
        "wall_material" : dpg.get_value("input_wall_material"),
        "wall_thickness" : dpg.get_value("input_wall_thickness"),
        "unit_wall_thickness" : dpg.get_value("unit_wall_thickness"),
        "N_cooling_channels" : dpg.get_value("input_N_cooling_channels"),
        "jacket_resolution" : dpg.get_value("input_jacket_resolution"),
        "channel_roughness" : dpg.get_value("input_channel_roughness"),
        "interpolation_type" : dpg.get_value("interpolation_type"),
        "pressure_drop_model" : dpg.get_value("input_pressure_drop_model"),
        "cold_side_model" : dpg.get_value("input_cold_side_model"),
        "hot_side_model" : dpg.get_value("input_hot_side_model"),
        "wall_model" : dpg.get_value("input_wall_model"),
        "channel_roughness" : dpg.get_value("input_channel_roughness"),
        "N_injectors" : dpg.get_value("input_N_injectors"),
        "injector_velocity_ratio" : dpg.get_value("input_injector_velocity_ratio"),
    }

def get_control_points() -> list[dict]:
    return control_points


# Local callbacks
def on_generate_graph(state: dict):
    values = {
        "x_value" : dpg.get_value("combo_graph_x"),
        "y_value" : dpg.get_value("combo_graph_y"),
        "y2_value" : dpg.get_value("combo_graph_y2"),
    }

    main_graph(state, values)

def on_pressure_drop_model_change(sender, app_data):
    model = app_data

    if model in (["Colebrook-Petukhov", "Colebrook"]):
        set_enabled("input_channel_roughness")
    else:
        set_disabled("input_channel_roughness")

def on_hot_side_model_change(sender, app_data):
    model = app_data

    if model == "Bartz Corrected":
        set_enabled("input_N_injectors")
        set_enabled("input_injector_velocity_ratio")
    else:
        set_disabled("input_N_injectors")
        set_disabled("input_injector_velocity_ratio")




# Control Points Logic and Display
control_points = [
    {"id": "inlet",  "label": "Coolant Inlet",  "fixed": True, "position": 0.0, "unit_position": "cm", "cw": 0.0, "unit_cw": "mm", "ch": 0.0, "unit_ch": "mm"},
    {"id": "outlet", "label": "Coolant Outlet", "fixed": True, "position": 0.0, "unit_position": "cm", "cw": 0.0, "unit_cw": "mm", "ch": 0.0, "unit_ch": "mm"},
]
next_control_point_id = 0


# Add Control Point - Logic Function
def add_control_point(control_point_after_id: str):
    global next_control_point_id
    current_id = next(i for i, p in enumerate(control_points) if p["id"] == control_point_after_id)
    control_points.insert(current_id + 1, {
        "id"            : f"cp_{next_control_point_id}",
        "label"         : "Control Point",
        "fixed"         : False,
        "position"      : 0.0, "unit_position": "cm",
        "cw"            : 0.0, "unit_cw" : "mm",
        "ch"            : 0.0, "unit_ch" : "mm",
    })
    next_control_point_id += 1
    build_cards()


# Delete Control Point - Logic Function
def delete_control_point(control_point_id: str):
    global control_points
    control_points = [p for p in control_points if p["id"] != control_point_id]
    build_cards()


# Update fields 
def update_control_point_field(control_point_id: str, field: str, value):
    for point in control_points:
        if point["id"] == control_point_id:
            point[field] = value
            return



# Build the cards
def build_cards():
    dpg.delete_item("control_points_window", children_only=True)

    with dpg.group(horizontal=True, parent="control_points_window"):
        for point in control_points:
            with dpg.group():
                with dpg.child_window(width=250, no_scrollbar=True):

                    dpg.add_text(point["label"])
                    dpg.add_separator()

                    dpg.add_spacer(height=5)
                    dpg.add_text("Position (Distance from IP)")
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            tag=f"input_pos_{point['id']}",
                            default_value=point["position"],
                            width=-65, format="%.2f", min_value=0.0, min_clamped=True,
                            callback=lambda s, v, u: update_control_point_field(u, "position", v),
                            user_data=point["id"]
                        )
                        dpg.add_combo(
                            tag=f"unit_position_{point['id']}",
                            items=["cm", "m", "mm", "in", "ft"],
                            default_value=point["unit_position"],
                            width=60,
                            callback=lambda s, v, u: update_control_point_field(u, "unit_position", v),
                            user_data=point["id"]
                        )

                    dpg.add_spacer(height=5)
                    dpg.add_text("Channel Width")
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            tag=f"input_cw_{point['id']}",
                            default_value=point["cw"],
                            width=-65, format="%.2f", min_value=0.0, min_clamped=True,
                            callback=lambda s, v, u: update_control_point_field(u, "cw", v),
                            user_data=point["id"]
                        )
                        dpg.add_combo(
                            tag=f"unit_cw_{point['id']}",
                            items=["cm", "mm", "in"],
                            default_value=point["unit_cw"],
                            width=60,
                            callback=lambda s, v, u: update_control_point_field(u, "unit_cw", v),
                            user_data=point["id"]
                        )

                    dpg.add_spacer(height=5)
                    dpg.add_text("Channel Height")
                    with dpg.group(horizontal=True):
                        dpg.add_input_float(
                            tag=f"input_ch_{point['id']}",
                            default_value=point["ch"],
                            width=-65, format="%.2f", min_value=0.0, min_clamped=True,
                            callback=lambda s, v, u: update_control_point_field(u, "ch", v),
                            user_data=point["id"]
                        )
                        dpg.add_combo(
                            tag=f"unit_ch_{point['id']}",
                            items=["cm", "mm", "in"],
                            default_value=point["unit_ch"],
                            width=60,
                            callback=lambda s, v, u: update_control_point_field(u, "unit_ch", v),
                            user_data=point["id"]
                        )

                    dpg.add_spacer(height=5)
                    if point["id"] != "outlet":
                        dpg.add_button(
                            label="Add Control Point",
                            width=-1,
                            callback=lambda s, a, u: add_control_point(u),
                            user_data=point["id"]
                        )

                    dpg.add_spacer(height=5)
                    if not point["fixed"]:
                        dpg.add_button(
                            label="Delete",
                            width=-1,
                            callback=lambda s, a, u: delete_control_point(u),
                            user_data=point["id"]
                        )

                    


# Theme build function
def build_themes():
        with dpg.theme(tag="disabled_float_entry_theme"):
            with dpg.theme_component(dpg.mvInputFloat, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (110, 110, 110, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (10, 10, 10, 255))

        with dpg.theme(tag="disabled_combo_theme"):
            with dpg.theme_component(dpg.mvCombo, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (110, 110, 110, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (10, 10, 10, 255))

        with dpg.theme(tag="disabled_int_entry_theme"):
            with dpg.theme_component(dpg.mvInputInt, enabled_state=False):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 0, 0, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (110, 110, 110, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (10, 10, 10, 255))

        with dpg.theme(tag="button_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        (30,  60,  110, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (40,  70,  125, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  (20,  50,  95,  255))



# Setter functions for enabled/disabled entries
def set_enabled(tag):
    dpg.configure_item(tag, enabled=True)
    dpg.bind_item_theme(tag, 0)  

def set_disabled(tag):
    dpg.configure_item(tag, enabled=False)
    if "Combo" in dpg.get_item_type(tag):
        dpg.bind_item_theme(tag, "disabled_combo_theme")
    elif "Int" in dpg.get_item_type(tag):
        dpg.bind_item_theme(tag, "disabled_int_entry_theme")
    else:
        dpg.bind_item_theme(tag, "disabled_float_entry_theme")



# Nozzle Type Selection Callback
def on_nozzle_type(sender, app_data, user_data):
    if (sender == "check_conical"):
        dpg.set_value("check_conical", True)
        dpg.set_value("check_bell", False)

        set_enabled("input_nozzle_angle")
        set_disabled("input_nozzle_length_percentage")
        

    elif (sender == "check_bell"):
        dpg.set_value("check_conical", False)
        dpg.set_value("check_bell", True)

        set_enabled("input_nozzle_length_percentage")
        set_disabled("input_nozzle_angle")


# Throat sizing method selection callback
def on_throat_sizing_method(sender, app_data, user_data):
    if (sender == "check_mass_flow_rate"):
        dpg.set_value("check_mass_flow_rate", True)
        dpg.set_value("check_Rt", False)

        set_enabled("input_mass_flow_rate")
        set_disabled("input_Rt")

        set_enabled("unit_mass_flow_rate")
        set_disabled("unit_Rt")
        
    elif (sender == "check_Rt"):
        dpg.set_value("check_mass_flow_rate", False)
        dpg.set_value("check_Rt", True)

        set_enabled("input_Rt")
        set_disabled("input_mass_flow_rate")

        set_enabled("unit_Rt")
        set_disabled("unit_mass_flow_rate")


# Graph option callback
def on_graph_checkbox(sender, app_data):
    enabled = dpg.get_value("check_generate_graph")
    dpg.configure_item("combo_graph_x", enabled=enabled)
    dpg.configure_item("combo_graph_y", enabled=enabled)




# Resize nozzle type inputs
def resize_nozzle_type_inputs():
    if not dpg.does_item_exist("input_nozzle_angle"):
        return
    
    cell_width = dpg.get_item_width("main_window") / 4
    label_w = 30
    checkbox_w = 20
    input_w = int((cell_width - label_w - checkbox_w - 40) * 0.5)

    dpg.configure_item("input_nozzle_angle", width=input_w)
    dpg.configure_item("input_nozzle_length_percentage", width=input_w)

# Resize the throat-sizing inputs
def resize_throat_sizing_inputs():
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
def resize_wall_material_inputs():
    if not dpg.does_item_exist("input_wall_material"):
        return

    cell_width = dpg.get_item_width("main_window") / 4

    wall_material_combo_w  = int(cell_width * 0.29)
    wall_thickness_input_w = int(cell_width * 0.25)
    wall_thickness_unit_w  = 53

    dpg.configure_item("input_wall_material",  width=wall_material_combo_w)
    dpg.configure_item("input_wall_thickness", width=wall_thickness_input_w)
    dpg.configure_item("unit_wall_thickness",  width=wall_thickness_unit_w)



def resize_main_window(sender=None, app_data=None, user_data=None):
    if not dpg.does_item_exist("main_window"):
        return
    dpg.set_item_pos("main_window", [0, 0])
    dpg.set_item_width("main_window", dpg.get_viewport_client_width())
    dpg.set_item_height("main_window", dpg.get_viewport_client_height())
    

    resize_nozzle_type_inputs()
    resize_throat_sizing_inputs()
    resize_wall_material_inputs()

    if user_data is not None and user_data["nozzle_parameters"]["x"] is not None:
        update_nozzle_canvas(user_data)

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



def build_interface(on_generate_nozzle: callable, on_solve: callable, state):
    with dpg.window(tag="main_window", no_title_bar=True, no_resize=True, no_move=True, no_scrollbar=False, width=1200, height=760):

        with dpg.tab_bar(tag="main_tab_bar"):

            # ===================================================================================
            # TAB 1: INPUTS
            # ===================================================================================

            with dpg.tab(label="Inputs"):
                with dpg.table(header_row=False, borders_innerV=True, policy=dpg.mvTable_SizingStretchProp):

                    dpg.add_table_column(init_width_or_weight=0.5)
                    dpg.add_table_column(init_width_or_weight=0.5)

                    with dpg.table_row():

                        # -----------------------------------------------------------------------------------
                        # Left Column - Engine Parameters
                        # -----------------------------------------------------------------------------------

                        with dpg.table_cell():
                            dpg.add_spacer(height=5)
                            dpg.add_text("Engine Definition", indent=7)
                            dpg.add_separator()

                            with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                                dpg.add_table_column(init_width_or_weight=0.5)
                                dpg.add_table_column(init_width_or_weight=0.5)

                                # Oxidizer  |  Expansion Ratio
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=8)
                                        dpg.add_text("Oxidizer")
                                        dpg.add_combo(tag="input_oxidizer", items=oxidizer_items, default_value=oxidizer_items[0], width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=8)
                                        dpg.add_text("Expansion Ratio")
                                        dpg.add_input_float(tag="input_eps", width=-1, format="%.2f", min_value=1.0, default_value=15.0, min_clamped=True)

                                # Fuel  |  Contraction Ratio
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Fuel")
                                        dpg.add_combo(tag="input_fuel", items=fuel_items, default_value=fuel_items[2], width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Contraction Ratio")
                                        dpg.add_input_float(tag="input_CR", width=-1, format="%.2f", min_value=1.0, default_value=3.0, min_clamped=True)

                                # Mixture Ratio  |  Characteristic Length
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Mixture Ratio (O/F)")
                                        dpg.add_input_float(tag="input_MR", width=-1, format="%.2f", min_value=0.0, default_value=3.6, min_clamped=True)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Characteristic Length")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_L_star", width=-65, format="%.2f", min_value=0.0, default_value=80.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_L_star", items=["cm", "m", "mm", "in", "ft"], default_value="cm", width=60)

                                # Chamber Pressure  |  Nozzle Resolution
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Chamber Pressure")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_Pc", width=-65, format="%.2f", min_value=0.0, default_value=150.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_Pc", items=["Pa", "kPa", "bar", "MPa", "psi", "atm"], default_value="bar", width=60)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Nozzle Resolution")
                                        dpg.add_input_int(tag="input_nozzle_resolution", width=-1, min_value=0, default_value=700, min_clamped=True, step=1, step_fast=10)

                                # Throat Sizing - Mass Flow Rate  |  Nozzle Type - Conical
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Throat Sizing")
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Mass Flow Rate", tag="check_mass_flow_rate", callback=on_throat_sizing_method)
                                            dpg.add_spacer(width=2)
                                            dpg.add_input_float(tag="input_mass_flow_rate", format="%.2f", min_value=0.0, min_clamped=True, enabled=False)
                                            dpg.add_combo(tag="unit_mass_flow_rate", items=["kg/s", "g/s", "kg/min", "lb/s"], default_value="kg/s", width=60, enabled=False)
                                            set_disabled("input_mass_flow_rate")
                                            set_disabled("unit_mass_flow_rate")
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Nozzle Type")
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Conical", tag="check_conical", callback=on_nozzle_type)
                                            dpg.add_spacer(width=10)
                                            dpg.add_text("Angle (°)")
                                            dpg.add_input_float(tag="input_nozzle_angle", format="%.1f", min_value=0.0, min_clamped=True, enabled=False)
                                            set_disabled("input_nozzle_angle")

                                # Throat Sizing - Throat Radius  |  Nozzle Type - Bell
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Throat Radius", tag="check_Rt", callback=on_throat_sizing_method)
                                            dpg.add_spacer(width=14)
                                            dpg.add_input_float(tag="input_Rt", format="%.2f", min_value=0.0, min_clamped=True, enabled=False)
                                            dpg.add_combo(tag="unit_Rt", items=["cm", "m", "mm", "in", "ft"], default_value="cm", width=60, enabled=False)
                                            set_disabled("input_Rt")
                                            set_disabled("unit_Rt")
                                    with dpg.table_cell():
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Bell", tag="check_bell", callback=on_nozzle_type)
                                            dpg.add_spacer(width=20)
                                            dpg.add_text("Length (%)")
                                            dpg.add_input_float(tag="input_nozzle_length_percentage", format="%.1f", min_value=0.0, min_clamped=True, enabled=False)
                                            set_disabled("input_nozzle_length_percentage")

                            dpg.add_spacer(height=4)
                            dpg.add_separator()

                            dpg.add_spacer(height=4)
                            dpg.add_button(tag="generate_nozzle_button", label="Generate Nozzle", callback=on_generate_nozzle, width=-1)
                            dpg.bind_item_theme("generate_nozzle_button", "button_theme")

                            dpg.add_spacer(height=4)
                            dpg.add_text("Nozzle", indent=7)
                            dpg.add_spacer(height=4)
                            with dpg.child_window(tag="nozzle_canvas_window", width=-1, height=-1, border=True, no_scrollbar=True):
                                with dpg.drawlist(tag="nozzle_canvas", width=100, height=100):
                                    pass

                        # -----------------------------------------------------------------------------------
                        # Right Column - Cooling Parameters
                        # -----------------------------------------------------------------------------------

                        with dpg.table_cell():
                            dpg.add_spacer(height=5)
                            dpg.add_text("Cooling Jacket Definition", indent=7)
                            dpg.add_separator()

                            with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                                dpg.add_table_column(init_width_or_weight=0.5)
                                dpg.add_table_column(init_width_or_weight=0.5)

                                # Coolant  |  Coolant Mass Flow Rate
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant")
                                        dpg.add_combo(tag="input_coolant", width=-1, items=coolant_items, default_value=coolant_items[1])
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Mass Flow Rate")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_mass_flow", width=-65, format="%.1f", min_value=0.0, default_value=10.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_mass_flow", items=["kg/s", "g/s", "kg/min", "lb/s"], default_value="kg/s", width=60)

                                # Coolant Inlet Temperature  |  Coolant Inlet Pressure
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Inlet Temperature")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_inlet_temperature", width=-65, format="%.1f", min_value=0.0, default_value=100.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_inlet_temperature", items=["K", "C", "F"], default_value="K", width=60)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Inlet Pressure")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_inlet_pressure", width=-65, format="%.1f", min_value=0.0, default_value=220.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_inlet_pressure", items=["Pa", "kPa", "bar", "MPa", "psi", "atm"], default_value="bar", width=60)

                                # Wall Material  |  Number of Channels
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Wall Material")
                                        with dpg.group(horizontal=True):
                                            dpg.add_combo(tag="input_wall_material", items=wall_material_items, default_value=wall_material_items[0])
                                            dpg.add_spacer(width=2)
                                            dpg.add_text("Thickness:")
                                            dpg.add_input_float(tag="input_wall_thickness", format="%.1f", min_value=0.0, default_value=1.2, min_clamped=True)
                                            dpg.add_combo(tag="unit_wall_thickness", items=["mm", "cm", "in"], default_value="mm")
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Number of Channels")
                                        dpg.add_input_int(tag="input_N_cooling_channels", width=-1, min_value=0, default_value=250, min_clamped=True, step=1)

                            dpg.add_spacer(height=4)
                            dpg.add_separator()

                            dpg.add_spacer(height=4)
                            dpg.add_text("Cooling Channels Definition", indent=7)

                            with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                                dpg.add_table_column(init_width_or_weight=0.5)
                                dpg.add_table_column(init_width_or_weight=0.5)

                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=5)
                                        dpg.add_text("Channel Width/Height Interpolation Type:")
                                        dpg.add_combo(tag="interpolation_type", items=interpolation_type_items, default_value=interpolation_type_items[0], width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=5)
                                        dpg.add_text("Jacket Resolution (Number of Stations): ")
                                        dpg.add_input_int(tag="input_jacket_resolution", width=-1, min_value=0, default_value=250, min_clamped=True, step=1, step_fast=10)

                            with dpg.child_window(width=-1, height=325, tag="control_points_window", horizontal_scrollbar=True):
                                pass

                            build_cards()

            # ===================================================================================
            # TAB 2: SOLVER & RESULTS
            # ===================================================================================

            with dpg.tab(label="Solver & Results"):
                dpg.add_spacer(height=6)

                # --- Model Configuration ---
                dpg.add_text("Model Configuration", indent=7)
                dpg.add_separator()
                dpg.add_spacer(height=4)

                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)

                    with dpg.table_row():
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Pressure Drop Model:")
                                dpg.add_combo(tag="input_pressure_drop_model", items=pressure_drop_model_items, callback=on_pressure_drop_model_change, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Cold Side Model:")
                                dpg.add_combo(tag="input_cold_side_model", items=cold_side_model_items, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Hot Side Model:")
                                dpg.add_combo(tag="input_hot_side_model", items=hot_side_model_items, callback=on_hot_side_model_change, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Wall Model:")
                                dpg.add_combo(tag="input_wall_model", items=wall_model_items, width=-1)

                dpg.add_spacer(height=6)

                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)
                    dpg.add_table_column(init_width_or_weight=0.25)

                    with dpg.table_row():
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Channel Roughness (μm):")
                                dpg.add_input_float(tag="input_channel_roughness", width=-1, format="%.1f", min_value=0.0, min_clamped=True)
                                set_disabled("input_channel_roughness")
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Number of Injectors:")
                                dpg.add_input_int(tag="input_N_injectors", width=-1, min_value=0, min_clamped=True)
                                set_disabled("input_N_injectors")
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Injector Velocity Ratio:")
                                dpg.add_input_float(tag="input_injector_velocity_ratio", width=-1, format="%.1f", min_value=0.0, min_clamped=True)
                                set_disabled("input_injector_velocity_ratio")
                        with dpg.table_cell():
                            pass


                dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_spacer(height=5)

                # --- Solve ---
                dpg.add_button(tag="solve_button", label="Solve", callback=on_solve, width=-1)
                dpg.bind_item_theme("solve_button", "button_theme")

                dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_spacer(height=5)

                # --- Output Options ---
                dpg.add_text("Output Options", indent=7)

                with dpg.table(header_row=False, policy=dpg.mvTable_SizingStretchProp):
                    dpg.add_table_column(init_width_or_weight=0.2)
                    dpg.add_table_column(init_width_or_weight=0.2)
                    dpg.add_table_column(init_width_or_weight=0.15)
                    dpg.add_table_column(init_width_or_weight=0.15)
                    dpg.add_table_column(init_width_or_weight=0.15)
                    dpg.add_table_column(init_width_or_weight=0.15)

                    with dpg.table_row():
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            with dpg.group(horizontal=True):
                                dpg.add_text("X Axis:")
                                dpg.add_combo(tag="combo_graph_x", items=graph_x_items, width=-1)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Y Axis:")
                                dpg.add_combo(tag="combo_graph_y", items=graph_y_items, width=-1)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Generate Graph", width=-1, callback=lambda s, a, u: on_generate_graph(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Print Full Output", width=-1, callback=lambda s, a, u: write_full_pyregen_output(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Print CEA Output", width=-1, callback=lambda s, a, u: write_full_cea_output(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Show Nozzle Graph", width=-1, callback=lambda s, a, u: nozzle_graph(state=u), user_data=state)

                dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_spacer(height=5)

                # --- Results Output ---
                dpg.add_text("Results", indent=7)
                dpg.add_spacer(height=4)


                with dpg.child_window(tag="results_output_window", width=-1, height=-1, border=True):
                    pass


# Upload the Nozzle Contour to the Interface
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
    draw_horizontal_ruler(nozzle_length_m, scale_x, draw_area_left, axis_line_y)
    draw_vertical_ruler(nozzle_max_radius_m, scale_r, axis_line_y, vertical_ruler_width)



def draw_horizontal_ruler(nozzle_length_m, scale_x, draw_area_left, axis_line_y):
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

def draw_vertical_ruler(nozzle_max_radius_m, scale_r, axis_line_y, vertical_ruler_width):
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
    


def show_errors(errors):
    if dpg.does_item_exist("error_popup"):
        dpg.delete_item("error_popup")

    print(errors)

    with dpg.window(tag="error_popup", label="Input Errors", modal=True, no_resize=True, width=400):
        for e in errors:
            dpg.add_text(f"• {e}", color=(255, 80, 80), wrap=370)
        dpg.add_spacer(height=8)
        dpg.add_button(label="OK", width=-1, callback=lambda: dpg.delete_item("error_popup"))



def run_interface(on_generate_nozzle: callable, on_solve: callable, state: dict):
    dpg.create_context()

    with dpg.font_registry():
        if FONT_PATH.exists():
            default_font = dpg.add_font(str(FONT_PATH), 16)
            dpg.bind_font(default_font)

    build_themes()
    build_interface(on_generate_nozzle, on_solve, state)

    dpg.create_viewport(title="PyRegen v1.1")
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_viewport_pos([200, 0])
    center_viewport_on_screen()
    dpg.set_viewport_resize_callback(resize_main_window, user_data=state)
    resize_main_window(user_data=state)
    dpg.set_primary_window("main_window", False)

    dpg.start_dearpygui()
    dpg.destroy_context()