from ui.callbacks import get_inputs_on_generate, get_inputs_on_solve

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
        case "ft":  return value / 3.28

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


# Input processor on generate
def inputs_on_generate(state: dict) -> list[str]:
    errors = []
    input = get_inputs_on_generate()

    engine = state["engine_parameters"]
    nozzle = state["nozzle_parameters"]

    # Oxidizer
    if not input["oxidizer"]:
        errors.append("Oxidizer must be selected.")
    else:
        engine["oxidizer"] = input["oxidizer"]

    # Fuel
    if not input["fuel"]:
        errors.append("Fuel must be selected.")
    else:
        engine["fuel"] = input["fuel"]

    # Mixture Ratio
    if input["MR"] == 0:
        errors.append("Mixture ratio must be bigger than 0.")
    else:
        engine["MR"] = input["MR"]

    # Chamber Pressure
    if input["Pc"] == 0:
        errors.append("Chamber pressure must be bigger than 0.")
    else:
        engine["Pc"] = pressure_conversion(input["Pc"], input["unit_Pc"])

    # Throat Sizing Method
    if not input["throat_sizing_method"]:
        errors.append("You must select one of the options for throat sizing.")
    else:
        engine["throat_sizing_method"] = input["throat_sizing_method"]

        if input["throat_sizing_method"] == "mass_flow":
            if input["mass_flow_rate"] == 0:
                errors.append("Mass flow rate must be greater than 0.")
            else:
                engine["mass_flow_rate"] = mass_flow_conversion(input["mass_flow_rate"], input["unit_mass_flow_rate"])

        elif input["throat_sizing_method"] == "given_radius":
            if input["Rt"] == 0:
                errors.append("Throat radius must be greater than 0.")
            else:
                engine["Rt"] = length_conversion(input["Rt"], input["unit_Rt"])

    # Expansion & Contraction
    nozzle["eps"] = input["eps"]
    nozzle["CR"] = input["CR"]

    # Characteristic Length
    if input["L_star"] == 0:
        errors.append("Characteristic length must be greater than 0.")
    else:
        nozzle["L_star"] = length_conversion(
            input["L_star"],
            input["unit_L_star"]
        )

    # Nozzle Resolution
    if input["nozzle_resolution"] <= 10:
        errors.append("Nozzle resolution must be greater than 10 points.")
    elif input["nozzle_resolution"] > 50000:
        errors.append("Nozzle resolution must be smaller than 50000 points.")
    else:
        nozzle["nozzle_resolution"] = input["nozzle_resolution"]

    # Nozzle Type
    if not input["nozzle_type"]:
        errors.append("You must select one of the options for nozzle type.")
    else:
        nozzle["nozzle_type"] = input["nozzle_type"]

        if input["nozzle_type"] == "conical":
            if input["nozzle_angle"] <= 0:
                errors.append("Nozzle angle must be greater than 0°.")
            elif input["nozzle_angle"] > 90:
                errors.append("Nozzle angle must be smaller than 90°.")
            else:
                nozzle["nozzle_angle"] = input["nozzle_angle"]

        elif input["nozzle_type"] == "bell":
            if input["nozzle_length_percentage"] <= 50:
                errors.append("Nozzle length percentage must be greater than 50%.")
            elif input["nozzle_length_percentage"] > 100:
                errors.append("Nozzle length percentage must be smaller than 100%.")
            else:
                nozzle["nozzle_length_percentage"] = input["nozzle_length_percentage"]

    return errors


# Input processor on solve
def inputs_on_solve(state: dict) -> list[str]:
    errors = []
    input = get_inputs_on_solve()
    
    control_points : list[dict] = input["control_points"]

    engine  = state["engine_parameters"]
    coolant = state["coolant_parameters"]
    channel = state["channel_parameters"]
    solver  = state["solver_options"]

    # ---------------- COOLANT ----------------

    if not input["coolant"]:
        errors.append("Coolant must be selected.")
    else:
        coolant["coolant"] = input["coolant"]

    if input["coolant_mass_flow_rate"] == 0:
        errors.append("Coolant mass flow rate must be greater than 0.")
    else:
        coolant["coolant_mass_flow_rate"] = mass_flow_conversion(
            input["coolant_mass_flow_rate"],
            input["unit_coolant_mass_flow_rate"]
        )

    if temperature_conversion(
        input["coolant_inlet_temperature"],
        input["unit_coolant_inlet_temperature"]
    ) <= 0:
        errors.append("Coolant inlet temperature must be greater than 0 Kelvin.")
    else:
        coolant["coolant_inlet_temperature"] = temperature_conversion(
            input["coolant_inlet_temperature"],
            input["unit_coolant_inlet_temperature"]
        )

    if input["coolant_inlet_pressure"] == 0:
        errors.append("Coolant inlet pressure must be greater than 0.")
    else:
        coolant["coolant_inlet_pressure"] = pressure_conversion(
            input["coolant_inlet_pressure"],
            input["unit_coolant_inlet_pressure"]
        )

    # ---------------- CHANNEL ----------------

    if not input["wall_material"]:
        errors.append("Wall material must be selected.")
    else:
        channel["wall_material"] = input["wall_material"]

    if input["wall_thickness"] == 0:
        errors.append("Wall thickness must be greater than 0.")
    else:
        channel["wall_thickness"] = length_conversion(
            input["wall_thickness"],
            input["unit_wall_thickness"]
        )

    if input["N_cooling_channels"] < 3:
        errors.append("Number of cooling channels must be greater than 2")
    else:
        channel["N_cooling_channels"] = input["N_cooling_channels"]

    if not input["interpolation_type"]:
        errors.append("Interpolation type must be selected.")
    else:
        channel["interpolation_type"] = input["interpolation_type"]

    if input["jacket_resolution"] <= 10:
        errors.append("Jacket resolution must be greater than 10 points.")
    elif input["jacket_resolution"] > 9999:
        errors.append("Jacket resolution must be smaller than 10000 points.")
    else:
        channel["jacket_resolution"] = input["jacket_resolution"]

    # ---------------- CONTROL POINTS ----------------

    positions = []
    cw_list = []
    ch_list = []

    for i, point in enumerate(control_points):
        if point["fixed"]:
            label = point["label"]
        else:
            label = f"Control Point {i}"

        if point["cw"] == 0:
            errors.append(f"{label}: channel width must be greater than 0.")
        else:
            cw_list.append(length_conversion(point["cw"], point["unit_cw"]))

        if point["ch"] == 0:
            errors.append(f"{label}: channel height must be greater than 0.")
        else:
            ch_list.append(length_conversion(point["ch"], point["unit_ch"]))

        positions.append(length_conversion(point["position"], point["unit_position"]))

    for i in range(len(positions)):
        if control_points[i]["fixed"]:
            label = control_points[i]["label"]
        else:
            label = f"Control Point {i}"

        if positions[i] > float(max(state["nozzle_parameters"]["x"])):
            errors.append(f"Position of {label} is outside the nozzle.")

    if not all(positions[i] <= positions[i+1] for i in range(len(positions) - 1)) and \
       not all(positions[i] >= positions[i+1] for i in range(len(positions) - 1)):
        errors.append("Control point positions must be monotonically ordered (inlet→outlet OR outlet→inlet).")

    channel["control_points_position"] = positions
    channel["control_points_cw"] = cw_list
    channel["control_points_ch"] = ch_list

    # ---------------- SOLVER OPTIONS ----------------

    if not input["pressure_drop_model"]:
        errors.append("Pressure drop model must be selected.")
    else:
        solver["pressure_drop_model"] = input["pressure_drop_model"]


    if not input["cold_side_model"]:
        errors.append("Cold side model must be selected.")
    else:
        solver["cold_side_model"] = input["cold_side_model"]


    if not input["hot_side_model"]:
        errors.append("Hot side model must be selected.")
    else:
        solver["hot_side_model"] = input["hot_side_model"]


    if not input["wall_model"]:
        errors.append("Wall model must be selected.")
    else:
        solver["wall_model"] = input["wall_model"]


    if solver.get("pressure_drop_model") in ("Colebrook-Petukhov", "Colebrook"):
        if input["channel_roughness"] == 0:
            errors.append("Channel roughness (ε) must be greater than 0 μm for Colebrook-based models.")
        else:
            channel["channel_roughness"] = input["channel_roughness"] * 1e-6


    if solver.get("hot_side_model") == "Bartz Corrected":
        if input["N_injectors"] == 0:
            errors.append("The number of injectors must be greater than 0 for Bartz Corrected.")
        else:
            engine["N_injectors"] = input["N_injectors"]

        if input["injector_velocity_ratio"] == 0:
            errors.append("Injector velocity ratio must be greater than 0 for Bartz Corrected.")
        else:
            engine["injector_velocity_ratio"] = input["injector_velocity_ratio"]

    return errors