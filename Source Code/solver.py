from rocketcea.cea_obj_w_units import CEA_Obj as CEA_Obj_SI_units
from rocketcea.cea_obj import CEA_Obj as CEA_Obj_default_units
from scipy.interpolate import interp1d
from CoolProp.CoolProp import PropsSI
from scipy.optimize import fsolve
import numpy as np

import models


def initialize_state(state: dict, station_index: int) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    Pc      = state["engine_parameters"]["Pc"]
    Pc_psia = Pc / 6894.7
    MR      = state["engine_parameters"]["MR"]
    Tc      = state["engine_parameters"]["Tc"]

    c_SI_units      : CEA_Obj_SI_units      = state["engine_parameters"]["CEA_Obj_SI_units"]
    c_default_units : CEA_Obj_default_units = state["engine_parameters"]["CEA_Obj_default_units"]

    station_x   = state["nozzle_parameters"]["station_x"][station_index]
    nozzle_x    = np.array(state["nozzle_parameters"]["x"])
    nozzle_R    = np.array(state["nozzle_parameters"]["R_x"])
    nozzle_eps  = np.array(state["nozzle_parameters"]["eps_x"])
    nozzle_zone = np.array(state["nozzle_parameters"]["zone_x"])

    N_channels  = state["channel_parameters"]["N_cooling_channels"]
    cw          = state["channel_parameters"]["station_cw"][station_index]
    ch          = state["channel_parameters"]["station_ch"][station_index]

    coolant     = state["coolant_parameters"]["coolant"]
    coolant_mfr = state["coolant_parameters"]["coolant_mass_flow_rate"]
    coolant_T   = state["coolant_parameters"]["station_coolant_T"][-1]
    coolant_p   = state["coolant_parameters"]["station_coolant_p"][-1]

    eps       = float(np.interp(station_x, nozzle_x, nozzle_eps))
    idx_zone  = int(np.argmin(np.abs(nozzle_x - station_x)))
    zone      = int(nozzle_zone[idx_zone])
    station_R = float(np.interp(station_x, nozzle_x, nozzle_R))

    # ── CEA gas properties ───────────────────────────────────────────────
    try:
        if zone == 1:
            full_output = c_default_units.get_full_cea_output(Pc=Pc_psia, MR=MR, eps=eps, subar=eps, output='siunits')
            lines = full_output.split("\n")

            mach, Pr_gas = 0.2, 0.7
            for line in lines:
                if 'MACH_NUMBER' in line:
                    mach = float(line.split()[3])
                if 'PRANDTL NUMBER' in line:
                    Pr_gas = float(line.split()[-3])

            gamma = float(c_SI_units.get_Chamber_MolWt_gamma(Pc=Pc, MR=MR)[1])
            T_gas = Tc

        elif zone == 2:
            full_output = c_default_units.get_full_cea_output(Pc=Pc_psia, MR=MR, eps=eps, subar=eps, output='siunits')
            lines = full_output.split("\n")

            mach, T_gas, gamma, Pr_gas = 0.5, Tc * 0.95, 1.2, 0.7
            for line in lines:
                if 'MACH NUMBER' in line:
                    mach = float(line.split()[-2])
                if 'T, K' in line:
                    T_gas = float(line.split()[-2])
                if 'GAMMAs' in line:
                    gamma = float(line.split()[-2])
                if 'PRANDTL NUMBER' in line:
                    Pr_gas = float(line.split()[-1])

        elif zone == 3:
            gamma  = float(c_SI_units.get_Chamber_MolWt_gamma(Pc=Pc, MR=MR)[1])
            mach   = 1.0
            T_gas  = float(c_SI_units.get_Temperatures(Pc=Pc, MR=MR, eps=eps)[1])
            Pr_gas = float(c_SI_units.get_Throat_Transport(Pc=Pc, MR=MR, eps=eps)[3])

        elif zone == 4:
            gamma  = float(c_SI_units.get_exit_MolWt_gamma(Pc=Pc, MR=MR, eps=eps)[1])
            mach   = float(c_SI_units.get_MachNumber(Pc=Pc, MR=MR, eps=eps))
            T_gas  = float(c_SI_units.get_Temperatures(Pc=Pc, MR=MR, eps=eps)[2])
            Pr_gas = float(c_SI_units.get_Exit_Transport(Pc=Pc, MR=MR, eps=eps)[3])

        else:
            errors.append(f"Unknown nozzle zone {zone} at x={station_x:.4f} m.")
            return errors

    except Exception as e:
        errors.append(f"CEA lookup failed at x={station_x:.2f} m, eps={eps:.2f} — {e}")
        return errors


    # ── Adiabatic Wall Temp ──────────────────────────────────────────────
    T_aw = Tc * (1.0 + pow(Pr_gas, 1/3) * (gamma - 1.0) / 2.0 * pow(mach, 2)) / (1.0 + (gamma - 1.0) / 2.0 * pow(mach, 2))


    # ── Channel geometry ─────────────────────────────────────────────────
    A_channel = cw * ch
    Dh        = 2.0 * cw * ch / (cw + ch)
    landwidth = (2.0 * np.pi * station_R / N_channels) - cw


    # ── Coolant bulk properties ──────────────────────────────────────────
    try:
        coolant_rho       = PropsSI("D", "T", coolant_T, "P", coolant_p, coolant)
        coolant_viscosity = PropsSI("V", "T", coolant_T, "P", coolant_p, coolant)
        coolant_k         = PropsSI("L", "T", coolant_T, "P", coolant_p, coolant)
        coolant_Cp        = PropsSI("C", "T", coolant_T, "P", coolant_p, coolant)
    except Exception as e:
        errors.append(f"CoolProp bulk properties failed at T={coolant_T:.1f} K, station {station_index} with: {e}")
        return errors

    coolant_velocity = coolant_mfr / (coolant_rho * A_channel * N_channels)
    coolant_Re       = coolant_rho * coolant_velocity * Dh / coolant_viscosity
    coolant_Pr       = coolant_viscosity * coolant_Cp / coolant_k


    # ── Store in state ───────────────────────────────────────────────────
    state["engine_parameters"]["station_T_gas"][station_index]  = T_gas
    state["engine_parameters"]["station_gamma"][station_index]  = gamma
    state["engine_parameters"]["station_mach"][station_index]   = mach
    state["engine_parameters"]["station_T_aw"][station_index]   = T_aw

    state["nozzle_parameters"]["station_eps"][station_index]    = eps
    state["nozzle_parameters"]["station_R"][station_index]      = station_R

    state["coolant_parameters"]["station_coolant_Re"][station_index]       = coolant_Re
    state["coolant_parameters"]["station_coolant_velocity"][station_index] = coolant_velocity
    state["coolant_parameters"]["station_coolant_k"][station_index]        = coolant_k
    state["coolant_parameters"]["station_coolant_Pr"][station_index]       = coolant_Pr
    state["coolant_parameters"]["station_coolant_rho"][station_index]      = coolant_rho

    state["channel_parameters"]["station_landwidth"][station_index] = landwidth
    state["channel_parameters"]["station_Dh"][station_index]        = Dh
    state["channel_parameters"]["station_A_channel"][station_index] = A_channel



    return errors




def update_state(station_index: int, state: dict) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    station_R = state["nozzle_parameters"]["station_R"][station_index]

    coolant = state["coolant_parameters"]["coolant"]
    coolant_mass_flow_rate = state["coolant_parameters"]["coolant_mass_flow_rate"]
    coolant_H = state["coolant_parameters"]["station_coolant_H"][-1]
    coolant_p = state["coolant_parameters"]["station_coolant_p"][-1]
    coolant_T = state["coolant_parameters"]["station_coolant_T"][-1]

    coolant_rho = state["coolant_parameters"]["station_coolant_rho"][station_index]
    coolant_Re = state["coolant_parameters"]["station_coolant_Re"][station_index]
    coolant_velocity = state["coolant_parameters"]["station_coolant_velocity"][station_index]

    Dh = state["channel_parameters"]["station_Dh"][station_index]


    # ── Geometry ──────────────────────────────────────────────────────────
    dx = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])
    A_heat_transfer = 2.0 * np.pi * station_R * dx


    # ── Enthalpy rise ────────────────────────────────────────────────────
    Q_transfer = state["results"]["Q_flux"][station_index] * A_heat_transfer
    dH = Q_transfer / coolant_mass_flow_rate
    coolant_H += dH

    
    try:
        coolant_T = PropsSI("T", "H", coolant_H, "P", coolant_p, coolant)
    except Exception as e:
        errors.append(f"CoolProp temperature lookup failed at station {station_index}, H={coolant_H:.2f} J/kg with: {e}")
        return errors



    # ── Pressure drop ────────────────────────────────────────────────────
    if coolant_Re < 2300:
        f = 64.0 / coolant_Re
    else:
        f = pow(0.79 * np.log(coolant_Re) - 1.64, -2)

    dp = f * (dx / Dh) * 0.5 * coolant_rho * pow(coolant_velocity, 2)
    coolant_p -= dp


    # ── Append to state ──────────────────────────────────────────────────
    state["coolant_parameters"]["station_coolant_T"].append(coolant_T)
    state["coolant_parameters"]["station_coolant_H"].append(coolant_H)
    state["coolant_parameters"]["station_coolant_p"].append(coolant_p)

    return errors




def run_solver(state: dict) -> list[str]:
    solver_errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    coolant = state["coolant_parameters"]["coolant"]
    coolant_T = state["coolant_parameters"]["coolant_inlet_temperature"]
    coolant_p = state["coolant_parameters"]["coolant_inlet_pressure"]

    control_points_position = state["channel_parameters"]["control_points_position"]
    control_points_cw = state["channel_parameters"]["control_points_cw"]
    control_points_ch = state["channel_parameters"]["control_points_ch"]
    jacket_resolution = state["channel_parameters"]["jacket_resolution"]
    interpolation_type = state["channel_parameters"]["interpolation_type"]

    if interpolation_type == "Linear": interpolation_type = "linear"
    if interpolation_type == "Piecewise Constant": interpolation_type = "zero"


    # ── Build station arrays and store in state ──────────────────────────
    station_x = np.linspace(control_points_position[0], control_points_position[-1], jacket_resolution)


    # ── Flip control points if coolant flows outlet → inlet ──────────────
    if control_points_position[0] > control_points_position[-1]:
        control_points_position = control_points_position[::-1]
        control_points_cw = control_points_cw[::-1]
        control_points_ch = control_points_ch[::-1]

    
    cw_interp = interp1d(control_points_position, control_points_cw, kind=interpolation_type)
    ch_interp = interp1d(control_points_position, control_points_ch, kind=interpolation_type)

    station_cw = cw_interp(station_x)
    station_ch = ch_interp(station_x)

    # Important naming scheme : station_value refers to the list of the values at each station
    state["nozzle_parameters"]["station_x"] = station_x.tolist()
    state["channel_parameters"]["station_cw"] = station_cw.tolist()
    state["channel_parameters"]["station_ch"] = station_ch.tolist()


    # ── Inlet coolant enthalpy ────────────────────────────────────────────
    try:
        coolant_H = PropsSI("H", "T", coolant_T, "P", coolant_p, coolant)
    except Exception as e:
        solver_errors.append(f"CoolProp inlet coolant enthalpy lookup failed at coolant inlet temperature {coolant_T:.2f} with: {e}")
        return solver_errors
    

    state["coolant_parameters"]["station_coolant_T"] = [coolant_T]
    state["coolant_parameters"]["station_coolant_p"] = [coolant_p]
    state["coolant_parameters"]["station_coolant_H"] = [coolant_H]


    state["engine_parameters"]["station_T_gas"]   = [None] * jacket_resolution
    state["engine_parameters"]["station_T_aw"]    = [None] * jacket_resolution
    state["engine_parameters"]["station_gamma"]   = [None] * jacket_resolution
    state["engine_parameters"]["station_mach"]    = [None] * jacket_resolution

    state["nozzle_parameters"]["station_R"]       = [None] * jacket_resolution
    state["nozzle_parameters"]["station_eps"]     = [None] * jacket_resolution

    state["coolant_parameters"]["station_coolant_k"]        = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_velocity"] = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_Re"]       = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_Pr"]       = [None] * jacket_resolution
    state["coolant_parameters"]["station_coolant_rho"]      = [None] * jacket_resolution

    state["channel_parameters"]["station_landwidth"] = [None] * jacket_resolution
    state["channel_parameters"]["station_Dh"]        = [None] * jacket_resolution
    state["channel_parameters"]["station_A_channel"] = [None] * jacket_resolution

    state["results"]["Q_flux"]      = [None] * jacket_resolution
    state["results"]["T_cold_wall"] = [None] * jacket_resolution
    state["results"]["T_hot_wall"]  = [None] * jacket_resolution
    state["results"]["h_coolant"]   = [None] * jacket_resolution
    state["results"]["h_gas"]       = [None] * jacket_resolution


    def flux_residual(T_cold_wall: float, station_index: int, state: dict) -> float:
        _, _, _, Q_residual, errors = models.model_1d(state, station_index, float(T_cold_wall))
        solver_errors.extend(errors)
        return Q_residual


    # ── Station loop ─────────────────────────────────────────────────────
    for station_index in range(jacket_resolution):
        x = state["nozzle_parameters"]["station_x"][station_index]

        coolant_T = state["coolant_parameters"]["station_coolant_T"][-1]
        coolant_p = state["coolant_parameters"]["station_coolant_p"][-1]
        coolant_H = state["coolant_parameters"]["station_coolant_H"][-1]

        # ── 1D Solver - fsolve ───────────────────────────────────────────
        T_cold_wall_initial = coolant_T


        initialization_errors = initialize_state(state, station_index)
        solver_errors.extend(initialization_errors)

        if initialization_errors:
            return solver_errors

        try:
            T_cold_wall_solution, info, ier, msg = fsolve(
                flux_residual,
                T_cold_wall_initial,
                args = (station_index, state),
                full_output = True,
            )
            T_cold_wall_solution = float(T_cold_wall_solution[0])
        except Exception as e:
            solver_errors.append(f"Station {station_index} (x={station_x[station_index]:.4f} m): 1D heat transfer model failed — {e}")
            continue

        if ier != 1:
            solver_errors.append(f"Station {station_index} (x={station_x[station_index]:.4f} m): 1D heat transfer model did not converge — {msg}")
            continue


        Q_flux_cold, Q_flux_hot, T_hot_wall, _, model_errors = models.model_1d(state, station_index, T_cold_wall_solution)
        solver_errors.extend(model_errors)

        if model_errors:
            return solver_errors
        

        T_aw = state["engine_parameters"]["station_T_aw"][station_index]
        
        Q_flux    = (Q_flux_hot + Q_flux_cold) / 2
        h_coolant = Q_flux_cold / (T_cold_wall_solution - coolant_T)
        h_gas     = Q_flux_hot / (T_aw - T_hot_wall)

        state["results"]["Q_flux"][station_index]      = Q_flux
        state["results"]["T_cold_wall"][station_index] = T_cold_wall_solution
        state["results"]["T_hot_wall"][station_index]  = T_hot_wall
        state["results"]["h_coolant"][station_index]   = h_coolant
        state["results"]["h_gas"][station_index]       = h_gas
        

        update_state_errors = update_state(station_index, state)
        solver_errors.extend(update_state_errors)

        if update_state_errors:
            return solver_errors
        

        print(
            f"Station: {station_index:>4d} | "
            f"x:{x*100:>6.2f} cm | "
            f"Coolant Temp:{coolant_T:>7.2f} K   Coolant Pressure:{coolant_p/1e5:>7.2f} bar | "
            f"Hot Wall Temp:{T_hot_wall:>7.2f} K   Heat Flux:{Q_flux/1e6:>7.3f} MW/m²"
        )


    return solver_errors