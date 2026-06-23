from scipy.interpolate import interp1d
from CoolProp.CoolProp import PropsSI
import numpy as np

import data


def model_1d(state: dict, station_index: int, T_cold_wall: float) -> tuple[float, float, float, float, list[str]]:
    errors = []

    # ── Unpack  ──────────────────────────────────
    Pc                = state["engine_parameters"]["Pc"]
    Rt                = state["engine_parameters"]["Rt"]
    Tc                = state["engine_parameters"]["Tc"]
    C_star            = state["engine_parameters"]["C_star"]
    chamber_Cp        = state["engine_parameters"]["chamber_Cp"]
    chamber_Pr        = state["engine_parameters"]["chamber_Pr"]
    chamber_viscosity = state["engine_parameters"]["chamber_viscosity"]

    T_gas     = state["engine_parameters"]["station_T_gas"][station_index]
    T_aw      = state["engine_parameters"]["station_T_aw"][station_index]
    gamma     = state["engine_parameters"]["station_gamma"][station_index]
    mach      = state["engine_parameters"]["station_mach"][station_index]

    station_R = state["nozzle_parameters"]["station_R"][station_index]
    eps       = state["nozzle_parameters"]["station_eps"][station_index]


    N_channels     = state["channel_parameters"]["N_cooling_channels"]
    wall_material  = state["channel_parameters"]["wall_material"]
    wall_thickness = state["channel_parameters"]["wall_thickness"]

    cw        = state["channel_parameters"]["station_cw"][station_index]
    ch        = state["channel_parameters"]["station_ch"][station_index]
    landwidth = state["channel_parameters"]["station_landwidth"][station_index]
    Dh        = state["channel_parameters"]["station_Dh"][station_index]

    coolant     = state["coolant_parameters"]["coolant"]
    coolant_T   = state["coolant_parameters"]["station_coolant_T"][-1]
    coolant_p   = state["coolant_parameters"]["station_coolant_p"][-1]
    coolant_Re  = state["coolant_parameters"]["station_coolant_Re"][station_index]
    coolant_Pr  = state["coolant_parameters"]["station_coolant_Pr"][station_index]
    coolant_k   = state["coolant_parameters"]["station_coolant_k"][station_index]


    # ── Wall thermal conductivity ────────────────────────────────────────
    try:
        thermal_conductivity_data = data.THERMAL_CONDUCTIVITY_DATA[wall_material]
        wall_k = float(interp1d(
            thermal_conductivity_data["X"],
            thermal_conductivity_data["Y"],
            kind="linear", fill_value="extrapolate"
        )(T_cold_wall))
    except Exception as e:
        errors.append(f"Wall thermal conductivity failed at T={T_cold_wall:.2f} K, station {station_index} — {e}")
        return 0.0, 0.0, 0.0, 0.0, errors


    # ── Cold side (Nusselt + fin) ────────────────────────────────────────
    if coolant_Re <= 10000:
        try:
            f = pow(0.79 * np.log(coolant_Re) - 1.64, -2)
            Nu = ((f / 8) * (coolant_Re - 1000) * coolant_Pr) / (1 + 12.7 * np.sqrt((f / 8) * (pow(coolant_Pr, 2/3) - 1)))
            h_coolant = Nu * coolant_k / Dh
        except Exception as e:
            errors.append(f"Gnielinski failed at station {station_index} — {e}")
            return 0.0, 0.0, 0.0, 0.0, errors
        
    else:
        try:
            wall_coolant_viscosity = PropsSI("V", "T", T_cold_wall, "P", coolant_p, coolant)
            coolant_viscosity      = PropsSI("V", "T", coolant_T,   "P", coolant_p, coolant)
        except Exception as e:
            errors.append(f"CoolProp viscosity failed at station {station_index} — {e}")
            return 0.0, 0.0, 0.0, 0.0, errors
        
        try:
            Nu = 0.027 * pow(coolant_Re, 0.8) * pow(coolant_Pr, 1/3)
            h_coolant = (Nu * coolant_k / Dh) * pow(coolant_viscosity / wall_coolant_viscosity, 0.14)
        except Exception as e:
            errors.append(f"Sieder-Tate failed at station {station_index} — {e}")
            return 0.0, 0.0, 0.0, 0.0, errors


    # ── Roughness correction ─────────────────────────────────────────────
    try:
        f = pow(0.79 * np.log(coolant_Re) - 1.64, -2)
        f_smooth = 0.0032 + 0.221 * pow(coolant_Re, -0.237)
        zeta = f / f_smooth

        roughness_factor = (
            zeta * (1 + (1.5 * pow(coolant_Pr, -1/6) * pow(coolant_Re, -1/8)) * (coolant_Pr - 1))
                 / (1 + (1.5 * pow(coolant_Pr, -1/6) * pow(coolant_Re, -1/8)) * (zeta * coolant_Pr - 1))
        )

        h_coolant *= roughness_factor
    except Exception as e:
        errors.append(f"Roughness correction failed at station {station_index} — {e}")



    # ── Fin model ────────────────────────────────────────────────────────
    corrected_fin_height = ch + landwidth / 2
    m_fin = np.sqrt(2 * h_coolant / (wall_k * landwidth))
    fin_efficiency = np.tanh(m_fin * corrected_fin_height) / (m_fin * corrected_fin_height)

    A_cold = (2 * fin_efficiency * ch + cw) * N_channels
    A_hot  = 2.0 * np.pi * station_R

    Q_flux_cold = h_coolant * (T_cold_wall - coolant_T) * (A_cold / A_hot)



    # ── Wall Model ───────────────────────────────────────────────────────
    T_hot_wall = T_cold_wall + Q_flux_cold * wall_thickness / wall_k



    # ── Hot side (Bartz) ─────────────────────────────────────────────────
    mach_term = 1.0 + (gamma - 1.0) / 2.0 * pow(mach, 2)
    sigma = pow(0.5 * (T_hot_wall / Tc) * mach_term + 0.5, -0.68) * pow(mach_term, -0.12)

    try:
        h_gas = (
            (0.026 / pow(Rt * 2.0, 0.2))
            * (pow(chamber_viscosity, 0.2) * chamber_Cp / pow(chamber_Pr, 0.6))
            * pow(Pc / C_star, 0.8)
            * pow(1.0 / eps, 0.9)
            * 1.029 * sigma
        )
    except ZeroDivisionError as e:
        errors.append(f"Bartz division by zero at station {station_index} — {e}")
        return 0.0, 0.0, 0.0, 0.0, errors

    Q_flux_hot = h_gas * (T_aw - T_hot_wall)


    # ── Residual ─────────────────────────────────────────────────────────
    Q_residual = Q_flux_hot - Q_flux_cold

    return Q_flux_cold, Q_flux_hot, T_hot_wall, Q_residual, errors