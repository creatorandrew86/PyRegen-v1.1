from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import dearpygui.dearpygui as dpg

from rocketcea.cea_obj import CEA_Obj as CEA_Obj_default_units

import interface


def _ask_save_path(default_filename: str):
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    root.update()

    path = filedialog.asksaveasfilename(
        parent=root,
        defaultextension=".txt",
        initialfile=default_filename,
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Save Output As",
    )

    root.destroy()
    return Path(path) if path else None


def print_full_cea_output(state: dict):
    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        print("PyRegen must run before attempting to print any output")
        interface.show_errors(["PyRegen must run before attempting to print any output"])
        return

    # ── Unpack ───────────────────────────────────────────────────────────
    Pc              = state["engine_parameters"]["Pc"]
    Pc_psia         = Pc / 6894.7
    MR              = state["engine_parameters"]["MR"]
    eps             = state["nozzle_parameters"]["eps"]
    c_default_units : CEA_Obj_default_units = state["engine_parameters"]["CEA_Obj_default_units"]

    full_cea_output = c_default_units.get_full_cea_output(Pc=Pc_psia, MR=MR, eps=eps, output='siunits')

    # ── Save ─────────────────────────────────────────────────────────────
    path = _ask_save_path("CEA Output.txt")
    if path is None:
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(full_cea_output)

    print(f"CEA output written to {path}")


def print_full_output(state: dict):
    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        print("PyRegen must run before attempting to print any output")
        interface.show_errors(["PyRegen must run before attempting to print any output"])
        return

    # ── Unpack engine ────────────────────────────────────────────────────
    oxidizer        = state["engine_parameters"]["oxidizer"]
    fuel            = state["engine_parameters"]["fuel"]
    Pc              = state["engine_parameters"]["Pc"]
    MR              = state["engine_parameters"]["MR"]
    Tc              = state["engine_parameters"]["Tc"]
    Isp             = state["engine_parameters"]["Isp"]
    Ivac            = state["engine_parameters"]["Ivac"]
    C_star          = state["engine_parameters"]["C_star"]
    Rt              = state["engine_parameters"]["Rt"]
    At              = state["nozzle_parameters"]["At"]
    eps             = state["nozzle_parameters"]["eps"]
    CR              = state["nozzle_parameters"]["CR"]
    mass_flow_rate  = state["engine_parameters"]["mass_flow_rate"]
    chamber_Cp      = state["engine_parameters"]["chamber_Cp"]
    chamber_Pr      = state["engine_parameters"]["chamber_Pr"]

    coolant         = state["coolant_parameters"]["coolant"]
    coolant_mfr     = state["coolant_parameters"]["coolant_mass_flow_rate"]
    coolant_T_in    = state["coolant_parameters"]["coolant_inlet_temperature"]
    coolant_p_in    = state["coolant_parameters"]["coolant_inlet_pressure"]
    coolant_T_out   = state["coolant_parameters"]["station_coolant_T"][-1]
    coolant_p_out   = state["coolant_parameters"]["station_coolant_p"][-1]

    wall_material   = state["channel_parameters"]["wall_material"]
    wall_thickness  = state["channel_parameters"]["wall_thickness"]
    N_channels      = state["channel_parameters"]["N_cooling_channels"]

    station_x       = state["nozzle_parameters"]["station_x"]
    station_cw      = state["channel_parameters"]["station_cw"]
    station_ch      = state["channel_parameters"]["station_ch"]
    station_lw      = state["channel_parameters"]["station_landwidth"]

    station_Re      = state["coolant_parameters"]["station_coolant_Re"]
    station_vel     = state["coolant_parameters"]["station_coolant_velocity"]
    station_T_cool  = state["coolant_parameters"]["station_coolant_T"][:-1]
    station_p_cool  = state["coolant_parameters"]["station_coolant_p"][:-1]

    station_T_cold  = state["results"]["T_cold_wall"]
    station_T_hot   = state["results"]["T_hot_wall"]
    station_Q       = state["results"]["Q_flux"]
    station_hl      = state["results"]["h_coolant"]
    station_hg      = state["results"]["h_gas"]

    n = len(station_x)


    # ── Save ─────────────────────────────────────────────────────────────
    path = _ask_save_path(f"Full Output.txt")
    if path is None:
        return

    # ── Column widths ────────────────────────────────────────────────────
    C1_width = 22
    C2_width = 36
    C3_width = 44
    C4_width = 62
    total_width  = C1_width + C2_width + C3_width + C4_width + 5

    def row(c1, c2, c3, c4):
        return f"│{c1:<{C1_width}}│{c2:<{C2_width}}│{c3:<{C3_width}}│{c4:<{C4_width}}│"

    with open(path, "w", encoding="utf-8") as f:

        f.write("=" * total_width + "\n")
        f.write(f"  PyRegen — Full Solver Output\n")
        f.write(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * total_width + "\n\n")

        f.write("── Engine Definition " + "─" * (total_width - 21) + "\n\n")
        f.write(f"  {'Oxidizer:':<28} {oxidizer}\n")
        f.write(f"  {'Fuel:':<28} {fuel}\n")
        f.write(f"  {'Chamber Pressure:':<28} {Pc/1e5:.2f} bar\n")
        f.write(f"  {'Mixture Ratio (O/F):':<28} {MR:.2f}\n")
        f.write(f"  {'Combustion Temperature:':<28} {Tc:.2f} K\n")
        f.write(f"  {'Characteristic Velocity:':<28} {C_star:.2f} m/s\n")
        f.write(f"  {'Specific Impulse:':<28} {Isp:.2f} s\n")
        f.write(f"  {'Vacuum Specific Impulse:':<28} {Ivac:.2f} s\n")
        f.write(f"  {'Throat Radius:':<28} {Rt*100:.2f} cm\n")
        f.write(f"  {'Throat Area:':<28} {At*1e4:.3f} cm²\n")
        f.write(f"  {'Expansion Ratio:':<28} {eps:.2f}\n")
        f.write(f"  {'Contraction Ratio:':<28} {CR:.2f}\n")
        f.write(f"  {'Mass Flow Rate:':<28} {mass_flow_rate:.2f} kg/s\n")
        f.write(f"  {'Gas Specific Heat (frozen):':<28} {chamber_Cp:.2f} J/(kg·K)\n")
        f.write(f"  {'Pr Number (frozen):':<28} {chamber_Pr:.4f}\n")
        f.write("\n\n")

        f.write("── Jacket Definition " + "─" * (total_width - 21) + "\n\n")
        f.write(f"  {'Coolant:':<28} {coolant}\n")
        f.write(f"  {'Coolant Mass Flow Rate:':<28} {coolant_mfr:.2f} kg/s\n")
        f.write(f"  {'Inlet Temperature:':<28} {coolant_T_in:.2f} K\n")
        f.write(f"  {'Inlet Pressure:':<28} {coolant_p_in/1e5:.2f} bar\n")
        f.write(f"  {'Outlet Temperature:':<28} {coolant_T_out:.2f} K\n")
        f.write(f"  {'Outlet Pressure:':<28} {coolant_p_out/1e5:.2f} bar\n")
        f.write(f"  {'Pressure Drop:':<28} {(coolant_p_in - coolant_p_out)/1e5:.2f} bar\n")
        f.write(f"  {'Temperature Rise:':<28} {coolant_T_out - coolant_T_in:.2f} K\n")
        f.write(f"  {'Wall Material:':<28} {wall_material}\n")
        f.write(f"  {'Wall Thickness:':<28} {wall_thickness*1000:.2f} mm\n")
        f.write(f"  {'Number of Channels:':<28} {N_channels}\n")
        f.write("\n\n")

        f.write("── Station Data " + "\n")

        f.write("─" * (total_width - 21) + "\n")
        f.write(row(
            " Station / Position",
            " Channel Geometry",
            " Coolant Properties",
            " Thermal Properties",
        ) + "\n")

        f.write("─" * (total_width - 21) + "\n")
        f.write(row(
            "    #      x[cm]",
            "   cw[mm]    ch[mm]     lw[mm]",
            "       Re     v[m/s]     T[K]    p[bar]",
            "   T_cw[K]    T_hw[K]   Q[MW/m²]  hl[kW/m²]   hg[kW/m²]",
        ) + "\n")

        f.write("─" * (total_width - 21) + "\n")
        for i in range(n):
            c1 = f"  {i:>4d}   {station_x[i]*100:>7.2f}"
            c2 = (
                f"  {station_cw[i]*1000:>6.3f}"
                f"     {station_ch[i]*1000:>6.3f}"
                f"     {station_lw[i]*1000:>6.3f}"
            )
            c3 = (
                f"  {station_Re[i]:>9.0f}"
                f"  {station_vel[i]:>7.3f}"
                f"  {station_T_cool[i]:>8.2f}"
                f"  {station_p_cool[i]/1e5:>7.2f}"
            )
            c4 = (
                f"  {station_T_cold[i]:>8.2f}"
                f"  {station_T_hot[i]:>8.2f}"
                f"  {station_Q[i]/1e6:>8.2f}"
                f"  {station_hl[i]/1e3:>9.2f}"
                f"  {station_hg[i]/1e3:>9.2f}"
            )
            f.write(row(c1, c2, c3, c4) + "\n")

        f.write("─" * (total_width - 21) + "\n")

    print(f"Full PyRegen output written to {path}")



VALUE_MAP = {
    "Axial position (x) (cm)":                      ("nozzle_parameters",  "station_x",                   lambda v: v * 1e2),
    "Cold wall temperature (K)":                    ("results",            "T_cold_wall",                 lambda v: v),
    "Hot wall temperature (K)":                     ("results",            "T_hot_wall",                  lambda v: v),
    "Gas HTC (×10⁴ W/m²K)":                         ("results",            "h_gas",                       lambda v: v / 1e4),
    "Coolant HTC (×10⁴ W/m²K)":                     ("results",            "h_coolant",                   lambda v: v / 1e4),
    "Heat flux (MW/m²)":                            ("results",            "Q_flux",                      lambda v: v / 1e6),
    "Coolant temperature (K)":                      ("coolant_parameters", "station_coolant_T",           lambda v: v),
    "Coolant pressure (bar)":                       ("coolant_parameters", "station_coolant_p",           lambda v: v / 1e5),
    "Coolant velocity (m/s)":                       ("coolant_parameters", "station_coolant_velocity",    lambda v: v),
    "Coolant Re":                                   ("coolant_parameters", "station_coolant_Re",          lambda v: v),
    "Channel width (mm)":                           ("channel_parameters", "station_cw",                  lambda v: v * 1e3),
    "Channel height (mm)":                          ("channel_parameters", "station_ch",                  lambda v: v * 1e3),
    "Landwidth (mm)":                               ("channel_parameters", "station_landwidth",           lambda v: v * 1e3),
    }

graph_x_items = list(VALUE_MAP.keys())
graph_y_items = [k for k in VALUE_MAP if k != "Axial position (x) (m)"]


def print_graph_output(state: dict, values: dict):
    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        print("PyRegen must run before attempting to print any output")
        interface.show_errors(["PyRegen must run before attempting to print any output"])
        return

    x_axis_value = values["x_value"]
    y_axis_value = values["y_value"]

    if x_axis_value is None or y_axis_value is None:
        interface.show_errors(["You must select both values for the graph"])
        return

    if x_axis_value == y_axis_value:
        interface.show_errors(["X and Y axis must be different"])
        return

    if y_axis_value == "Axial position (x) (m)":
        interface.show_errors(["'Axial position (x)' can only be used as the X axis"])
        return

    x_group, x_key, x_conv = VALUE_MAP[x_axis_value]
    y_group, y_key, y_conv = VALUE_MAP[y_axis_value]

    x_raw = state[x_group][x_key]
    y_raw = state[y_group][y_key]

    if x_raw is None or y_raw is None:
        interface.show_errors(["Selected data has not been computed yet"])
        return

    x_data = list(reversed([x_conv(v) for v in x_raw]))
    y_data = list(reversed([y_conv(v) for v in y_raw]))

    window_tag = "graph_window"
    if dpg.does_item_exist(window_tag):
        dpg.delete_item(window_tag)

    with dpg.window(label="Graph Output", tag=window_tag, width=700, height=500):
        with dpg.plot(label=f"{y_axis_value} vs {x_axis_value}", height=-1, width=-1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label=x_axis_value, tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label=y_axis_value, tag="y_axis")
            dpg.add_line_series(x_data, y_data, label=f"{y_axis_value} vs {x_axis_value}", parent="y_axis")
            dpg.fit_axis_data("x_axis")
            dpg.fit_axis_data("y_axis")


def print_main_output(state: dict):
    vp_width  = dpg.get_viewport_width()
    vp_height = dpg.get_viewport_height()
    window_width  = 350
    window_height = 180

    pos_x = (vp_width  - window_width)  // 2
    pos_y = (vp_height - window_height) // 2

    window_tag = "main_output_window"
    if dpg.does_item_exist(window_tag):
        dpg.delete_item(window_tag)

    max_heat_flux    = max(state["results"]["Q_flux"]) / 1e6
    max_hot_wall_T   = max(state["results"]["T_hot_wall"])
    pressure_drop    = abs((state["coolant_parameters"]["station_coolant_p"][0] - state["coolant_parameters"]["station_coolant_p"][-1]) / 1e5)
    temp_rise        = state["coolant_parameters"]["station_coolant_T"][-1] - state["coolant_parameters"]["station_coolant_T"][0]

    with dpg.window(label="Output", tag=window_tag, width=350, height=180, modal=False, no_resize=True, pos=(pos_x, pos_y)):
        dpg.add_text("--- Results ---")
        dpg.add_separator()
        dpg.add_text(f"Max heat flux:           {max_heat_flux:.3f} MW/m²")
        dpg.add_text(f"Max hot wall temperature: {max_hot_wall_T:.2f} K")
        dpg.add_text(f"Coolant pressure drop:    {pressure_drop:.3f} bar")
        dpg.add_text(f"Coolant temperature rise: {temp_rise:.2f} K")


def print_nozzle_graph(state: dict):
    # Check if the nozzle generator ran
    if state["nozzle_parameters"]["x"] is None:
        print("The nozzle generator must run before attempting to show the nozzle graph")
        interface.show_errors(["The nozzle generator must run before attempting to show the nozzle graph"])
        return
    
    # Nozzle line color
    with dpg.theme() as nozzle_line_theme:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, (100, 180, 255, 255), category=dpg.mvThemeCat_Plots)

    x_data = state["nozzle_parameters"]["x"]
    r_data = state["nozzle_parameters"]["R_x"]

    if x_data is None or r_data is None:
        interface.show_errors(["Nozzle geometry has not been computed yet"])
        return

    window_tag = "nozzle_graph_window"
    if dpg.does_item_exist(window_tag):
        dpg.delete_item(window_tag)

    x     = [v * 100 for v in x_data]
    upper = [v * 100 for v in r_data]
    lower = [-v for v in upper]

    with dpg.window(label="Nozzle Profile", tag=window_tag, width=700, height=400, modal=False):
        with dpg.plot(label="Nozzle Contour", height=-1, width=-1):
            dpg.add_plot_axis(dpg.mvXAxis, label="Axial position (cm)", tag="nozzle_x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, label="Radius (cm)",          tag="nozzle_y_axis")

            dpg.add_line_series(x, upper, label="Nozzle wall", parent="nozzle_y_axis", tag="nozzle_upper")
            dpg.add_line_series(x, lower, label="",            parent="nozzle_y_axis", tag="nozzle_lower")

            dpg.bind_item_theme("nozzle_upper", nozzle_line_theme)
            dpg.bind_item_theme("nozzle_lower", nozzle_line_theme)

            dpg.fit_axis_data("nozzle_x_axis")
            dpg.fit_axis_data("nozzle_y_axis")