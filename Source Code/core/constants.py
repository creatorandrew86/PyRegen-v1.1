from pathlib import Path

# Interface combos
OXIDIZER_ITEMS = ["LOX", "GOX", "N2O4", "N2O", "IRFNA", "H2O2", "Peroxide90", "Peroxide98", "MON3", "MON15", "MON25"]
FUEL_ITEMS = ["RP1", "LH2", "CH4", "MMH", "N2H4", "UDMH", "A50", "Ethanol", "Methanol", "GH2", "GCH4", "JetA", "JP10"]
COOLANT_ITEMS = ["Hydrogen", "Methane", "Ethane", "Ethanol", "Methanol", "Water", "Ammonia", "Nitrogen", "Helium", "Oxygen", "n-Dodecane", "n-Decane", "n-Octane"]

WALL_MATERIAL_ITEMS = ["Copper", "GRCop 42", "GRCop 84"]
INTERPOLATION_TYPE_ITEMS = ["Linear", "Piecewise Constant"]

GRAPH_X_ITEMS = ["Axial position (x) (cm)", "Cold wall temperature (K)", "Hot wall temperature (K)", "Heat flux (MW/m²)", "Coolant temperature (K)", "Coolant pressure (bar)", "Coolant velocity (m/s)", "Coolant Re"]
GRAPH_Y_ITEMS = ["Cold wall temperature (K)", "Hot wall temperature (K)", "Gas HTC (×10⁴ W/m²K)", "Coolant HTC (×10⁴ W/m²K)", "Heat flux (MW/m²)", "Coolant temperature (K)", "Coolant pressure (bar)", "Coolant velocity (m/s)", "Coolant Re", "Channel width (mm)", "Channel height (mm)", "Landwidth (mm)"]

PRESSURE_DROP_MODEL_ITEMS = ["Colebrook-Petukhov", "Filonenko-Petukhov", "Colebrook"]
COLD_SIDE_MODEL_ITEMS = ["Sieder-Tate", "Bishop et al.", "Jackson", "Dittus-Boelter", "Gnielinski"]
HOT_SIDE_MODEL_ITEMS = ["Bartz", "Bartz Corrected"]
WALL_MODEL_ITEMS = ["1D"]

# Font
FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "Inter-VariableFont_opsz,wght.ttf"

# key -> dpg tag
ON_GENERATE_INPUT_TAGS = {
    "oxidizer"                 : "input_oxidizer",
    "fuel"                     : "input_fuel",
    "Pc"                       : "input_Pc",
    "unit_Pc"                  : "unit_Pc",
    "MR"                       : "input_MR",
    "mass_flow_rate"           : "input_mass_flow_rate",
    "unit_mass_flow_rate"      : "unit_mass_flow_rate",
    "Rt"                       : "input_Rt",
    "unit_Rt"                  : "unit_Rt",
    "eps"                      : "input_eps",
    "CR"                       : "input_CR",
    "L_star"                   : "input_L_star",
    "unit_L_star"              : "unit_L_star",
    "nozzle_length_percentage" : "input_nozzle_length_percentage",
    "nozzle_angle"             : "input_nozzle_angle",
    "nozzle_resolution"        : "input_nozzle_resolution",
}

ON_SOLVE_INPUT_TAGS = {
    "coolant"                          : "input_coolant",
    "coolant_mass_flow_rate"           : "input_coolant_mass_flow",
    "unit_coolant_mass_flow_rate"      : "unit_mass_flow_rate",
    "coolant_inlet_temperature"        : "input_coolant_inlet_temperature",
    "unit_coolant_inlet_temperature"   : "unit_coolant_inlet_temperature",
    "coolant_inlet_pressure"           : "input_coolant_inlet_pressure",
    "unit_coolant_inlet_pressure"      : "unit_coolant_inlet_pressure",
    "wall_material"                    : "input_wall_material",
    "wall_thickness"                   : "input_wall_thickness",
    "unit_wall_thickness"              : "unit_wall_thickness",
    "N_cooling_channels"               : "input_N_cooling_channels",
    "jacket_resolution"                : "input_jacket_resolution",
    "channel_roughness"                : "input_channel_roughness",
    "interpolation_type"               : "interpolation_type",
    "pressure_drop_model"              : "input_pressure_drop_model",
    "cold_side_model"                  : "input_cold_side_model",
    "hot_side_model"                   : "input_hot_side_model",
    "wall_model"                       : "input_wall_model",
    "N_injectors"                      : "input_N_injectors",
    "injector_velocity_ratio"          : "input_injector_velocity_ratio",
}