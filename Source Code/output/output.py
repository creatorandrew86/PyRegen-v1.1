import dearpygui.dearpygui as dpg



COLUMNS = [
    ("Station",                       None,                                                 "{:d}",    None,            0.28),
    ("x(m)",                          ("nozzle_parameters",  "station_x"),                  "{:.2f}",  None,            0.25),
    ("Channel Width(mm)",             ("channel_parameters", "station_cw"),                 "{:.3f}",  lambda v: v*1e3, 0.90),
    ("Channel Height(mm)",            ("channel_parameters", "station_ch"),                 "{:.3f}",  lambda v: v*1e3, 0.95),
    ("Landwidth(mm)",                 ("channel_parameters", "station_landwidth"),          "{:.3f}",  lambda v: v*1e3, 0.70),
    ("Coolant Temp(K)",               ("coolant_parameters", "station_coolant_T"),          "{:.2f}",  None,            0.90),
    ("Coolant Pressure(bar)",         ("coolant_parameters", "station_coolant_p"),          "{:.2f}",  lambda v: v/1e5, 1.00),
    ("Hot Wall Temp(K)",              ("results",            "T_hot_wall"),                 "{:.2f}",  None,            0.88),
    ("Coolant HTC(×10⁴ W/m²·K)",       ("results",            "h_coolant"),                 "{:.3f}",  lambda v: v/1e4, 1.40),
    ("Gas HTC(×10⁴ W/m²·K)",           ("results",            "h_gas"),                     "{:.3f}",  lambda v: v/1e4, 1.30),
    ("Heat Flux(MW/m²)",              ("results",            "Q_flux"),                     "{:.3f}",  lambda v: v/1e6, 0.85),
]

TABLE_TAG = "results_table"


def header():
    """
    Clears the results child window and rebuilds the table with headers.
    Call this once before starting a new solver run.
    """
    dpg.delete_item("results_output_window", children_only=True)

    with dpg.table(
        tag=TABLE_TAG,
        parent="results_output_window",
        header_row=True,
        borders_innerV=True,
        borders_outerV=True,
        borders_innerH=True,
        borders_outerH=True,
        scrollX=False,
        scrollY=True,
        freeze_rows=1,
        policy=dpg.mvTable_SizingStretchProp,
        resizable=True,
    ):
        for label, _, _, _, weight in COLUMNS:
            dpg.add_table_column(label=label, init_width_or_weight=float(weight))


def print_main_output(state: dict, station_index: int):
    """
    Appends one row to the results table for the given station_index.
    initialize_main_output() must have been called before the first call
    to this function in a solver run.
    """
    with dpg.table_row(parent=TABLE_TAG):
        for _, key_path, fmt, convert, _ in COLUMNS:

            if key_path is None:
                value_str = fmt.format(station_index)
            else:
                section, key = key_path
                raw = state[section][key]
                try:
                    val = raw[station_index]
                    if convert is not None:
                        val = convert(val)
                    value_str = fmt.format(val)
                except (TypeError, IndexError):
                    value_str = "N/A"

            dpg.add_text(value_str)

    dpg.set_y_scroll("results_output_window", dpg.get_y_scroll_max("results_output_window"))