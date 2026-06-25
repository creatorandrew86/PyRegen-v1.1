def pressure_conversion(value: float, unit: str) -> float:
    match unit:
        case "Pa" :  return value
        case "kPa" : return value * 1e2
        case "MPa" : return value * 1e6
        case "bar" : return value * 1e5
        case "atm" : return value * 101325
        case "psi" : return value * 6894.76

def length_conversion(value: float, unit: str) -> float:
    match unit:
        case "m":   return value
        case "cm":  return value / 100
        case "mm":  return value / 1000
        case "in":  return value * 0.0254

def temperature_conversion(value, unit):
    match unit:
        case "K": return value
        case "C": return value + 273.15
        case "F": return (value - 32) * 5/9 + 273.15

def mass_flow_conversion(value, unit):
    match unit:
        case "kg/s":   return value
        case "g/s":    return value / 1000
        case "kg/min": return value / 60
        case "lb/s":   return value * 0.453592


# Input validation functions
def process_engine_inputs(raw_engine_params: dict) -> tuple[dict, list[str]]:
    errors = []
    clean = {}

    # Oxidizer
    if not raw_engine_params["oxidizer"]:
        errors.append("Oxidizer must be selected.")
    else:
        clean["oxidizer"] = raw_engine_params["oxidizer"]

    # Fuel
    if not raw_engine_params["fuel"]:
        errors.append("Fuel must be selected.")
    else:
        clean["fuel"] = raw_engine_params["fuel"]

    # Mixture Ratio
    if raw_engine_params["MR"] == 0:
        errors.append("Mixture ratio must be bigger than 0.")
    else:
        clean["MR"] = raw_engine_params["MR"]

    # Chamber Pressure
    if raw_engine_params["Pc"] == 0:
        errors.append("Chamber pressure must be bigger than 0.")
    else:
        clean["Pc"] = pressure_conversion(raw_engine_params["Pc"], raw_engine_params["unit_Pc"])


    # Throat Sizing Method
    clean["throat_sizing_method"] = raw_engine_params["throat_sizing_method"]

    if raw_engine_params["throat_sizing_method"] == "mass_flow":
        if raw_engine_params["mass_flow_rate"] == 0:
            errors.append("Mass flow rate must be greater than 0.")
        else:
            clean["mass_flow_rate"] = mass_flow_conversion(raw_engine_params["mass_flow_rate"], raw_engine_params["unit_mass_flow_rate"])

    elif raw_engine_params["throat_sizing_method"] == "given_radius":
        if raw_engine_params["Rt"] == 0:
            errors.append("Throat radius must be greater than 0.")
        else:
            clean["Rt"] = length_conversion(raw_engine_params["Rt"], raw_engine_params["unit_Rt"])

    else:
        errors.append("You must select one of the options for throat sizing.")

    return clean, errors


def process_nozzle_inputs(raw_nozzle_params: dict) -> tuple[dict, list[str]]:
    errors = []
    clean = {}

    # Expansion Ratio & Contraction Ratio
    clean["eps"] = raw_nozzle_params["eps"]
    clean["CR"] = raw_nozzle_params["CR"]

    # Characteristic Length
    if raw_nozzle_params["L_star"] == 0:
        errors.append("Characteristic length must be greater than 0.")
    else:
        clean["L_star"] = length_conversion(raw_nozzle_params["L_star"], raw_nozzle_params["unit_L_star"])

    # Nozzle Resolution
    if raw_nozzle_params["nozzle_resolution"] <= 10:
        errors.append("Nozzle resolution must be greater than 10 points.")
    elif raw_nozzle_params["nozzle_resolution"] > 50000:
        errors.append("Nozzle resolution must be smaller than 50000 points.")
    else:
        clean["nozzle_resolution"] = raw_nozzle_params["nozzle_resolution"]

    # Nozzle Type
    clean["nozzle_type"] = raw_nozzle_params["nozzle_type"]

    if raw_nozzle_params["nozzle_type"] == "conical":
        if raw_nozzle_params["nozzle_angle"] == 0:
            errors.append("Nozzle angle must be greater than 0°.")
        elif raw_nozzle_params["nozzle_angle"] > 90:
            errors.append("Nozzle angle must be smaller than 90°.")
        else:
            clean["nozzle_angle"] = raw_nozzle_params["nozzle_angle"]

    elif raw_nozzle_params["nozzle_type"] == "bell":
        if raw_nozzle_params["nozzle_length_percentage"] <= 50:
            errors.append("Nozzle length percentage must be greater than 50%.")
        elif raw_nozzle_params["nozzle_length_percentage"] > 100:
            errors.append("Nozzle length percentage must be smaller than 100%.")
        else:
            clean["nozzle_length_percentage"] = raw_nozzle_params["nozzle_length_percentage"]

    else:
        errors.append("You must select one of the options for nozzle type.")

    return clean, errors


def process_coolant_inputs(raw_coolant_params: dict) -> tuple[dict, list[str]]:
    errors = []
    clean = {}

    # Coolant
    if not raw_coolant_params["coolant"]:
        errors.append("Coolant must be selected.")
    else:
        clean["coolant"] = raw_coolant_params["coolant"]

    # Coolant Mass Flow Rate
    if raw_coolant_params["coolant_mass_flow_rate"] == 0:
        errors.append("Coolant mass flow rate must be greater than 0.")
    else:
        clean["coolant_mass_flow_rate"] = mass_flow_conversion(raw_coolant_params["coolant_mass_flow_rate"], raw_coolant_params["unit_coolant_mass_flow_rate"])

    # Coolant Inlet Temperature
    clean["coolant_inlet_temperature"] = temperature_conversion(raw_coolant_params["coolant_inlet_temperature"], raw_coolant_params["unit_coolant_inlet_temperature"])
    if clean["coolant_inlet_temperature"] <= 0:
        errors.append("Coolant inlet temperature must be greater than 0 Kelvin.")

    # Coolant Inlet Pressure
    if raw_coolant_params["coolant_inlet_pressure"] == 0:
        errors.append("Coolant inlet pressure must be greater than 0.")
    else:
        clean["coolant_inlet_pressure"] = pressure_conversion(raw_coolant_params["coolant_inlet_pressure"], raw_coolant_params["unit_coolant_inlet_pressure"])

    return clean, errors


def process_channel_inputs(raw_channel_params: dict, control_points: list[dict], state: dict) -> tuple[dict, list[str]]:
    errors = []
    clean = {}

    positionsList, cwList, chlist = [], [], []

    # Wall Material
    if not raw_channel_params["wall_material"]:
        errors.append("Wall material must be selected.")
    else:
        clean["wall_material"] = raw_channel_params["wall_material"]


    # Wall Thickness
    if raw_channel_params["wall_thickness"] == 0:
        errors.append("Wall thickness must be greater than 0.")
    else:
        clean["wall_thickness"] = length_conversion(raw_channel_params["wall_thickness"], raw_channel_params["unit_wall_thickness"])


    # Number of Channels
    if raw_channel_params["N_cooling_channels"] < 3:
        errors.append("Number of cooling channels must be greater than 2")
    else:
        clean["N_cooling_channels"] = raw_channel_params["N_cooling_channels"]


    # Interpolation Type
    if not raw_channel_params["interpolation_type"]:
        errors.append("Interpolation type must be selected.")
    else:
        clean["interpolation_type"] = raw_channel_params["interpolation_type"]


    # Jacket Resolution
    if raw_channel_params["jacket_resolution"] <= 10:
        errors.append("Jacket resolution must be greater than 10 points.")
    elif raw_channel_params["jacket_resolution"] > 9999:
        errors.append("Jacket resolution must be smaller than 10000 points.")
    else:
        clean["jacket_resolution"] = raw_channel_params["jacket_resolution"]


    # Control Points
    for i, point in enumerate(control_points):
        label = point["label"] if point["fixed"] else f"Control Point {i}"

        # Channel Width
        if point["cw"] == 0:
            errors.append(f"{label}: channel width must be greater than 0.")
        else:
            cwList.append(length_conversion(point["cw"], point["unit_cw"]))

        # Channel Height
        if point["ch"] == 0:
            errors.append(f"{label}: channel height must be greater than 0.")
        else:
            chlist.append(length_conversion(point["ch"], point["unit_ch"]))

        # Positions
        positionsList.append(length_conversion(point["position"], point["unit_position"]))


    # ----- Mathematical checking -----

    # Check that all the positions are points on the nozzle
    for i, point in enumerate(control_points):
        label = point["label"] if point["fixed"] else f"Control Point {i}"

        if positionsList[i] > float(max(state["nozzle_parameters"]["x"])):
            errors.append(f"Position of {label} is outside the nozzle.")


    # Check control point ordering
    ascending = all(positionsList[i] <= positionsList[i+1] for i in range(len(positionsList) - 1))
    descending = all(positionsList[i] >= positionsList[i+1] for i in range(len(positionsList) - 1))

    if not ascending and not descending:
        errors.append("Control point positions must be monotonically ordered (inlet→outlet OR outlet→inlet).")


    # Appending the control points data to the clean dict
    clean["control_points_position"] = positionsList
    clean["control_points_cw"] = cwList
    clean["control_points_ch"] = chlist


    return clean, errors


def process_solver_inputs(raw_solver_options: dict, raw_channel_params: dict) -> tuple[dict, list[str]]:
    errors = []
    clean = {}

    # Pressure drop model
    if not raw_solver_options["pressure_drop_model"]:
        errors.append("Pressure drop model must be selected.")
    else:
        clean["pressure_drop_model"] = raw_solver_options["pressure_drop_model"]


    # Cold side model
    if not raw_solver_options["cold_side_model"]:
        errors.append("Cold side model must be selected.")
    else:
        clean["cold_side_model"] = raw_solver_options["cold_side_model"]


    # Hot side model
    if not raw_solver_options["hot_side_model"]:
        errors.append("Hot side model must be selected.")
    else:
        clean["hot_side_model"] = raw_solver_options["hot_side_model"]


    # Wall model
    if not raw_solver_options["wall_model"]:
        errors.append("Wall model must be selected.")
    else:
        clean["wall_model"] = raw_solver_options["wall_model"]


    # Roughness — only required for Colebrook variants
    if clean.get("pressure_drop_model") in ("Colebrook-Petukhov", "Colebrook"):
        if raw_channel_params["channel_roughness"] == 0:
            errors.append("Channel roughness (ε) must be greater than 0 μm for Colebrook-based models.")
        else:
            clean["channel_roughness"] = raw_channel_params["channel_roughness"] * 1e-6

    return clean, errors




def process_inputs_on_generate(raw_engine_params, raw_nozzle_params) -> tuple[dict, list[str]]:
    clean_engine_params, engine_input_errors = process_engine_inputs(raw_engine_params)
    clean_nozzle_params, nozzle_input_errors = process_nozzle_inputs(raw_nozzle_params)

    input_errors = engine_input_errors + nozzle_input_errors
    clean_params = {
        "engine_parameters" : clean_engine_params,
        "nozzle_parameters" : clean_nozzle_params,
    }

    return clean_params, input_errors


def process_inputs_on_solve(raw_coolant_params: dict, raw_channel_params: dict, raw_solver_options:dict, control_points: list[str], state: dict) -> tuple[dict, list[str]]:
    clean_coolant_params, coolant_input_errors  = process_coolant_inputs(raw_coolant_params)
    clean_channel_params, channel_input_errors  = process_channel_inputs(raw_channel_params, control_points, state)
    clean_solver_options, solver_options_errors = process_solver_inputs(raw_solver_options, raw_channel_params)

    errors = channel_input_errors + coolant_input_errors + solver_options_errors

    clean_channel_params["channel_roughness"] = clean_solver_options.pop("channel_roughness", None)

    clean_params = {
        "coolant_parameters" : clean_coolant_params,
        "channel_parameters" : clean_channel_params,
        "solver_options" :     clean_solver_options
    }

    return clean_params, errors