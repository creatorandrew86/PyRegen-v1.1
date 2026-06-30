import dearpygui.dearpygui as dpg
import core.constants as ct

import ui.callbacks as callbacks
import ui.themes as themes



def get_control_points() -> list[dict]:
    return control_points

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
    control_points[:] = [p for p in control_points if p["id"] != control_point_id]
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
                                        dpg.add_combo(tag="input_oxidizer", items=ct.OXIDIZER_ITEMS, width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=8)
                                        dpg.add_text("Expansion Ratio")
                                        dpg.add_input_float(tag="input_eps", width=-1, format="%.2f", min_value=1.0, min_clamped=True)

                                # Fuel  |  Contraction Ratio
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Fuel")
                                        dpg.add_combo(tag="input_fuel", items=ct.FUEL_ITEMS, width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Contraction Ratio")
                                        dpg.add_input_float(tag="input_CR", width=-1, format="%.2f", min_value=1.0, min_clamped=True)

                                # Mixture Ratio  |  Characteristic Length
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Mixture Ratio (O/F)")
                                        dpg.add_input_float(tag="input_MR", width=-1, format="%.2f", min_value=0.0, min_clamped=True)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Characteristic Length")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_L_star", width=-65, format="%.2f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_L_star", items=["cm", "m", "mm", "in", "ft"], width=60)

                                # Chamber Pressure  |  Nozzle Resolution
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Chamber Pressure")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_Pc", width=-65, format="%.2f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_Pc", items=["Pa", "kPa", "bar", "MPa", "psi", "atm"], width=60)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Nozzle Resolution")
                                        dpg.add_input_int(tag="input_nozzle_resolution", width=-1, min_value=0, min_clamped=True, step=1, step_fast=10)

                                # Throat Sizing - Mass Flow Rate  |  Nozzle Type - Conical
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Throat Sizing")
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Mass Flow Rate", tag="check_mass_flow_rate", callback=callbacks.on_throat_sizing_method)
                                            dpg.add_spacer(width=2)
                                            dpg.add_input_float(tag="input_mass_flow_rate", format="%.2f", min_value=0.0, min_clamped=True, enabled=False)
                                            dpg.add_combo(tag="unit_mass_flow_rate", items=["kg/s", "g/s", "kg/min", "lb/s"], width=60, enabled=False)
                                            themes.set_disabled("input_mass_flow_rate")
                                            themes.set_disabled("unit_mass_flow_rate")
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Nozzle Type")
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Conical", tag="check_conical", callback=callbacks.on_nozzle_type)
                                            dpg.add_spacer(width=10)
                                            dpg.add_text("Angle (°)")
                                            dpg.add_input_float(tag="input_nozzle_angle", format="%.1f", min_value=0.0, min_clamped=True, enabled=False)
                                            themes.set_disabled("input_nozzle_angle")

                                # Throat Sizing - Throat Radius  |  Nozzle Type - Bell
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Throat Radius", tag="check_Rt", callback=callbacks.on_throat_sizing_method)
                                            dpg.add_spacer(width=14)
                                            dpg.add_input_float(tag="input_Rt", format="%.2f", min_value=0.0, min_clamped=True, enabled=False)
                                            dpg.add_combo(tag="unit_Rt", items=["cm", "m", "mm", "in", "ft"], width=60, enabled=False)
                                            themes.set_disabled("input_Rt")
                                            themes.set_disabled("unit_Rt")
                                    with dpg.table_cell():
                                        with dpg.group(horizontal=True):
                                            dpg.add_checkbox(label="Bell", tag="check_bell", callback=callbacks.on_nozzle_type)
                                            dpg.add_spacer(width=20)
                                            dpg.add_text("Length (%)")
                                            dpg.add_input_float(tag="input_nozzle_length_percentage", format="%.1f", min_value=0.0, min_clamped=True, enabled=False)
                                            themes.set_disabled("input_nozzle_length_percentage")

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
                                        dpg.add_combo(tag="input_coolant", width=-1, items=ct.COOLANT_ITEMS)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Mass Flow Rate")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_mass_flow", width=-65, format="%.1f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_mass_flow", items=["kg/s", "g/s", "kg/min", "lb/s"], width=60)

                                # Coolant Inlet Temperature  |  Coolant Inlet Pressure
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Inlet Temperature")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_inlet_temperature", width=-65, format="%.1f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_inlet_temperature", items=["K", "C", "F"], width=60)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Coolant Inlet Pressure")
                                        with dpg.group(horizontal=True):
                                            dpg.add_input_float(tag="input_coolant_inlet_pressure", width=-65, format="%.1f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_coolant_inlet_pressure", items=["Pa", "kPa", "bar", "MPa", "psi", "atm"], width=60)

                                # Wall Material  |  Number of Channels
                                with dpg.table_row():
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Wall Material")
                                        with dpg.group(horizontal=True):
                                            dpg.add_combo(tag="input_wall_material", items=ct.WALL_MATERIAL_ITEMS)
                                            dpg.add_spacer(width=2)
                                            dpg.add_text("Thickness:")
                                            dpg.add_input_float(tag="input_wall_thickness", format="%.1f", min_value=0.0, min_clamped=True)
                                            dpg.add_combo(tag="unit_wall_thickness", items=["mm", "cm", "in"])
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=6)
                                        dpg.add_text("Number of Channels")
                                        dpg.add_input_int(tag="input_N_cooling_channels", width=-1, min_value=0, min_clamped=True, step=1)

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
                                        dpg.add_combo(tag="interpolation_type", items=ct.INTERPOLATION_TYPE_ITEMS, width=-1)
                                    with dpg.table_cell():
                                        dpg.add_spacer(height=5)
                                        dpg.add_text("Jacket Resolution (Number of Stations): ")
                                        dpg.add_input_int(tag="input_jacket_resolution", width=-1, min_value=0, min_clamped=True, step=1, step_fast=10)

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
                                dpg.add_combo(tag="input_pressure_drop_model", items=ct.PRESSURE_DROP_MODEL_ITEMS, callback=callbacks.on_pressure_drop_model_change, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Cold Side Model:")
                                dpg.add_combo(tag="input_cold_side_model", items=ct.COLD_SIDE_MODEL_ITEMS, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Hot Side Model:")
                                dpg.add_combo(tag="input_hot_side_model", items=ct.HOT_SIDE_MODEL_ITEMS, callback=callbacks.on_hot_side_model_change, width=-1)
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Wall Model:")
                                dpg.add_combo(tag="input_wall_model", items=ct.WALL_MODEL_ITEMS, width=-1)

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
                                themes.set_disabled("input_channel_roughness")
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Number of Injectors:")
                                dpg.add_input_int(tag="input_N_injectors", width=-1, min_value=0, min_clamped=True)
                                themes.set_disabled("input_N_injectors")
                        with dpg.table_cell():
                            with dpg.group(horizontal=True):
                                dpg.add_text("Injector Velocity Ratio:")
                                dpg.add_input_float(tag="input_injector_velocity_ratio", width=-1, format="%.1f", min_value=0.0, min_clamped=True)
                                themes.set_disabled("input_injector_velocity_ratio")
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
                                dpg.add_combo(tag="combo_graph_x", items=ct.GRAPH_X_ITEMS, width=-1)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            with dpg.group(horizontal=True):
                                dpg.add_text("Y Axis:")
                                dpg.add_combo(tag="combo_graph_y", items=ct.GRAPH_Y_ITEMS, width=-1)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Generate Graph", width=-1, callback=lambda s, a, u: callbacks.on_generate_main_graph(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Print Full Output", width=-1, callback=lambda s, a, u: callbacks.on_write_full_pyregen_output(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Print CEA Output", width=-1, callback=lambda s, a, u: callbacks.on_write_full_cea_output(state=u), user_data=state)
                        with dpg.table_cell():
                            dpg.add_spacer(height=4)
                            dpg.add_button(label="Show Nozzle Graph", width=-1, callback=lambda s, a, u: callbacks.on_generate_nozzle_graph(state=u), user_data=state)

                dpg.add_spacer(height=5)
                dpg.add_separator()
                dpg.add_spacer(height=5)

                # --- Results Output ---
                dpg.add_text("Results", indent=7)
                dpg.add_spacer(height=4)

                with dpg.child_window(tag="results_output_window", width=-1, height=-1, border=True):
                    pass