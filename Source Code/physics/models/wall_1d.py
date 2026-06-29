from scipy.interpolate import interp1d
from scipy.optimize import fsolve
import numpy as np

from assets.data import THERMAL_CONDUCTIVITY_DATA


# ── Wall thermal conductivity ─────────────────────────────────────────────────
def _wall_thermal_conductivity(wall_material: str, T_cold_wall: float, station_index: int) -> tuple[float, list[str]]:
    errors = []

    try:
        data = THERMAL_CONDUCTIVITY_DATA[wall_material]
        wall_thermal_conductivity = float(interp1d(data["X"], data["Y"], kind="linear", fill_value="extrapolate")(T_cold_wall))
    except Exception as e:
        errors.append(f"Wall thermal conductivity failed at T={T_cold_wall:.2f} K, station {station_index}: {e}")
        return 0.0, errors
    
    return wall_thermal_conductivity, errors


# ── Fin model ───────────────────────────────────────────────────────────────────
def _fin_model(Q_flux_cold, h_coolant, wall_k, ch, cw, landwidth, N_channels: int, station_R) -> float:
    corrected_fin_height = ch + landwidth / 2.0
    m_fin                = np.sqrt(2.0 * h_coolant / (wall_k * landwidth))
    fin_efficiency       = np.tanh(m_fin * corrected_fin_height) / (m_fin * corrected_fin_height)

    A_cold = (2.0 * fin_efficiency * ch + cw) * N_channels
    A_hot  = 2.0 * np.pi * station_R

    return Q_flux_cold * (A_cold / A_hot)


# ── 1D Fin model ───────────────────────────────────────────────────────────────
def wall_1d_fin(state: dict, station_index: int, cold_side_model: callable, hot_side_model: callable) -> tuple[float, float, float, list[str]]:
    errors = []

    T_aw           = state["engine_parameters"]["station_T_aw"][station_index]
    station_R      = state["nozzle_parameters"]["station_R"][station_index]
    coolant_T      = state["coolant_parameters"]["station_coolant_T"][-1]

    wall_material  = state["channel_parameters"]["wall_material"]
    wall_thickness = state["channel_parameters"]["wall_thickness"]
    ch             = state["channel_parameters"]["station_ch"][station_index]
    cw             = state["channel_parameters"]["station_cw"][station_index]
    landwidth      = state["channel_parameters"]["station_landwidth"][station_index]
    N_channels     = state["channel_parameters"]["N_cooling_channels"]


    def residual(T_cold_wall: float) -> float:
        T_cold_wall = float(T_cold_wall)

        wall_k, thermal_conductivity_fetch_errors = _wall_thermal_conductivity(wall_material, T_cold_wall, station_index)
        if thermal_conductivity_fetch_errors:
            return 0.0

        h_coolant, cold_side_model_errors = cold_side_model(state, station_index, T_cold_wall)
        if cold_side_model_errors:
            return 0.0

        Q_flux_cold = h_coolant * (T_cold_wall - coolant_T)
        Q_flux_cold = _fin_model(Q_flux_cold, h_coolant, wall_k, ch, cw, landwidth, N_channels, station_R)

        T_hot_wall  = T_cold_wall + Q_flux_cold * wall_thickness / wall_k

        h_gas, hot_side_model_errors = hot_side_model(state, station_index, T_hot_wall)
        if hot_side_model_errors:
            return 0.0

        Q_flux_hot = h_gas * (T_aw - T_hot_wall)

        return Q_flux_hot - Q_flux_cold


    T_cold_wall_initial = coolant_T
    T_cold_wall_solution, _, ier, msg = fsolve(residual, T_cold_wall_initial, full_output=True)
    T_cold_wall_solution = float(T_cold_wall_solution[0])

    if ier != 1:
        errors.append(f"Station {station_index}: 1D model did not converge — {msg}")
        return 0.0, 0.0, 0.0, errors



    # ── Final evaluation at converged T_cold_wall ─────────────────────────
    wall_k, thermal_conductivity_fetch_errors = _wall_thermal_conductivity(wall_material, T_cold_wall_solution, station_index)
    errors.extend(thermal_conductivity_fetch_errors)
    if thermal_conductivity_fetch_errors:
        return 0.0, 0.0, 0.0, errors


    h_coolant, cold_side_model_errors = cold_side_model(state, station_index, T_cold_wall_solution)
    errors.extend(cold_side_model_errors)
    if cold_side_model_errors:
        return 0.0, 0.0, 0.0, errors

    
    Q_flux_cold = h_coolant * (T_cold_wall_solution - coolant_T)
    Q_flux_cold = _fin_model(Q_flux_cold, h_coolant, wall_k, ch, cw, landwidth, N_channels, station_R)

    T_hot_wall  = T_cold_wall_solution + Q_flux_cold * wall_thickness / wall_k


    h_gas, hot_side_model_errors = hot_side_model(state, station_index, T_hot_wall)
    errors.extend(hot_side_model_errors)
    if hot_side_model_errors:
        return 0.0, 0.0, 0.0, errors


    Q_flux_hot = h_gas * (T_aw - T_hot_wall)
    Q_flux = (Q_flux_hot + Q_flux_cold) / 2.0


    return Q_flux, T_cold_wall_solution, T_hot_wall, errors
