from CoolProp.CoolProp import PropsSI

from physics.models.registry import PRESSURE_DROP, COLD_SIDE, HOT_SIDE, WALL
from core.geometry import generate_jacket_geometry
from core.output import print_main_output
from core.cea import get_station_values

def initialize_state(state: dict, station_index: int) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    N_channels  = state["channel_parameters"]["N_cooling_channels"]
    Dh          = state["channel_parameters"]["station_Dh"][station_index]
    A_channel   = state["channel_parameters"]["station_A_channel"][station_index]

    coolant     = state["coolant_parameters"]["coolant"]
    coolant_mfr = state["coolant_parameters"]["coolant_mass_flow_rate"]
    coolant_T   = state["coolant_parameters"]["station_coolant_T"][-1]
    coolant_p   = state["coolant_parameters"]["station_coolant_p"][-1]

    zone        = state["nozzle_parameters"]["station_zone"][station_index]

    # Fetch the station values from CEA
    T_gas, T_aw, gamma, mach, cea_errors = get_station_values(state, station_index, zone)
    errors.extend(cea_errors)


    # ── Coolant bulk properties ──────────────────────────────────────────
    try:
        coolant_rho       = PropsSI("D", "T", coolant_T, "P", coolant_p, coolant)
        coolant_viscosity = PropsSI("V", "T", coolant_T, "P", coolant_p, coolant)
        coolant_k         = PropsSI("L", "T", coolant_T, "P", coolant_p, coolant)
        coolant_Pr        = PropsSI("PRANDTL", "T", coolant_T, "P", coolant_p, coolant)
    except Exception as e:
        errors.append(f"CoolProp bulk properties failed at T={coolant_T:.1f} K, station {station_index} with: {e}")
        return errors

    coolant_velocity = coolant_mfr / (coolant_rho * A_channel * N_channels)
    coolant_Re       = coolant_rho * coolant_velocity * Dh / coolant_viscosity


    # ── Update state ──────────────────────────────────────────────────────
    state["engine_parameters"]["station_T_gas"][station_index]  = T_gas
    state["engine_parameters"]["station_gamma"][station_index]  = gamma
    state["engine_parameters"]["station_mach"][station_index]   = mach
    state["engine_parameters"]["station_T_aw"][station_index]   = T_aw

    state["coolant_parameters"]["station_coolant_Re"][station_index]       = coolant_Re
    state["coolant_parameters"]["station_coolant_velocity"][station_index] = coolant_velocity
    state["coolant_parameters"]["station_coolant_k"][station_index]        = coolant_k
    state["coolant_parameters"]["station_coolant_Pr"][station_index]       = coolant_Pr
    state["coolant_parameters"]["station_coolant_rho"][station_index]      = coolant_rho

    return errors



def update_state(state: dict, station_index: int, pressure_drop_model: callable) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────]
    coolant = state["coolant_parameters"]["coolant"]
    coolant_mass_flow_rate = state["coolant_parameters"]["coolant_mass_flow_rate"]

    coolant_H = state["coolant_parameters"]["station_coolant_H"][-1]
    coolant_p = state["coolant_parameters"]["station_coolant_p"][-1]
    coolant_T = state["coolant_parameters"]["station_coolant_T"][-1]

    A_heat_transfer = state["channel_parameters"]["station_A_heat_transfer"][station_index]


    # ── Enthalpy rise ────────────────────────────────────────────────────
    Q_transfer = state["results"]["Q_flux"][station_index] * A_heat_transfer
    coolant_H += (Q_transfer / coolant_mass_flow_rate)
    
    try:
        coolant_T = PropsSI("T", "H", coolant_H, "P", coolant_p, coolant)
    except Exception as e:
        errors.append(f"CoolProp temperature lookup failed at station {station_index}, H={coolant_H:.2f} J/kg with: {e}")
        return errors


    # ── Pressure drop ────────────────────────────────────────────────────
    dp, pressure_drop_model_errors = pressure_drop_model(state, station_index)
    errors.extend(pressure_drop_model_errors)

    coolant_p -= dp


    state["coolant_parameters"]["station_coolant_T"].append(coolant_T)
    state["coolant_parameters"]["station_coolant_H"].append(coolant_H)
    state["coolant_parameters"]["station_coolant_p"].append(coolant_p)

    return errors




def run_solver(state: dict) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    coolant           = state["coolant_parameters"]["coolant"]
    coolant_T         = state["coolant_parameters"]["coolant_inlet_temperature"]
    coolant_p         = state["coolant_parameters"]["coolant_inlet_pressure"]
    jacket_resolution = state["channel_parameters"]["jacket_resolution"]

    # Generate the jacket geometry
    jacket_geometry_errors = generate_jacket_geometry(state)
    errors.extend(jacket_geometry_errors)


    # ── Inlet coolant enthalpy ────────────────────────────────────────────
    try:
        coolant_H = PropsSI("H", "T", coolant_T, "P", coolant_p, coolant)
    except Exception as e:
        errors.append(f"CoolProp inlet coolant enthalpy lookup failed at coolant inlet temperature {coolant_T:.2f} with: {e}")
        return errors
    

    state["coolant_parameters"]["station_coolant_T"] = [coolant_T]
    state["coolant_parameters"]["station_coolant_p"] = [coolant_p]
    state["coolant_parameters"]["station_coolant_H"] = [coolant_H]

    state["engine_parameters"]["station_T_gas"]   = [None] * jacket_resolution
    state["engine_parameters"]["station_T_aw"]    = [None] * jacket_resolution
    state["engine_parameters"]["station_gamma"]   = [None] * jacket_resolution
    state["engine_parameters"]["station_mach"]    = [None] * jacket_resolution

    state["coolant_parameters"]["station_coolant_k"]        = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_velocity"] = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_Re"]       = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_Pr"]       = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_rho"]      = [None] * jacket_resolution

    state["results"]["Q_flux"]      = [None] * jacket_resolution
    state["results"]["T_cold_wall"] = [None] * jacket_resolution
    state["results"]["T_hot_wall"]  = [None] * jacket_resolution
    state["results"]["h_coolant"]   = [None] * jacket_resolution
    state["results"]["h_gas"]       = [None] * jacket_resolution

    
    # Solver models
    pressure_drop_model = PRESSURE_DROP[state["solver_options"]["pressure_drop_model"]]
    cold_side_model     = COLD_SIDE[state["solver_options"]["cold_side_model"]]
    hot_side_model      = HOT_SIDE[state["solver_options"]["hot_side_model"]]
    wall_model          = WALL[state["solver_options"]["wall_model"]]

    # ── Station loop ─────────────────────────────────────────────────────
    for station_index in range(jacket_resolution):
        initialize_state_errors = initialize_state(state, station_index)
        errors.extend(initialize_state_errors)

        if initialize_state_errors:
            return errors

        # ── Solver ───────────────────────────────────────────
        Q_flux, T_cold_wall, T_hot_wall, solver_errors = wall_model(state, station_index, cold_side_model, hot_side_model)
        errors.extend(solver_errors)

        if solver_errors:
            return errors
        

        coolant_T = state["coolant_parameters"]["station_coolant_T"][-1]
        T_aw = state["engine_parameters"]["station_T_aw"][station_index]
        
        h_coolant = Q_flux / (T_cold_wall - coolant_T)
        h_gas     = Q_flux / (T_aw - T_hot_wall)

        state["results"]["Q_flux"][station_index]      = Q_flux
        state["results"]["T_cold_wall"][station_index] = T_cold_wall
        state["results"]["T_hot_wall"][station_index]  = T_hot_wall
        state["results"]["h_coolant"][station_index]   = h_coolant
        state["results"]["h_gas"][station_index]       = h_gas
        

        update_state_errors = update_state(state, station_index, pressure_drop_model)
        errors.extend(update_state_errors)

        if update_state_errors:
            return errors

        # Print to main output
        print_main_output(state, station_index)

    return errors