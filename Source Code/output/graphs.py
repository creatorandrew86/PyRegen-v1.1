import dearpygui.dearpygui as dpg
import interface.interface as ui


GRAPH_VALUE_MAP = {
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

graph_x_items = list(GRAPH_VALUE_MAP.keys())
graph_y_items = [k for k in GRAPH_VALUE_MAP if k != "Axial position (x) (m)"]


def main_graph(state: dict, values: dict):
    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        ui.show_errors(["PyRegen must run before attempting to print any output"])
        return

    x_axis_value = values["x_value"]
    y_axis_value = values["y_value"]

    if x_axis_value is None or y_axis_value is None:
        ui.show_errors(["You must select both values for the graph"])
        return

    if x_axis_value == y_axis_value:
        ui.show_errors(["X and Y axis must be different"])
        return

    if y_axis_value == "Axial position (x) (m)":
        ui.show_errors(["'Axial position (x)' can only be used as the X axis"])
        return

    x_group, x_key, x_conv = GRAPH_VALUE_MAP[x_axis_value]
    y_group, y_key, y_conv = GRAPH_VALUE_MAP[y_axis_value]

    x_raw = state[x_group][x_key]
    y_raw = state[y_group][y_key]

    if x_raw is None or y_raw is None:
        ui.show_errors(["Selected data has not been computed yet"])
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



def nozzle_graph(state: dict):
    # Check if the nozzle generator ran
    if state["nozzle_parameters"]["x"] is None:
        ui.show_errors(["The nozzle generator must run before attempting to show the nozzle graph"])
        return
    
    # Nozzle line color
    with dpg.theme() as nozzle_line_theme:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, (100, 180, 255, 255), category=dpg.mvThemeCat_Plots)

    x_data = state["nozzle_parameters"]["x"]
    r_data = state["nozzle_parameters"]["R_x"]

    if x_data is None or r_data is None:
        ui.show_errors(["Nozzle geometry has not been computed yet"])
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