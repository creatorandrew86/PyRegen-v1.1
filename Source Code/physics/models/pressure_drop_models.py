from CoolProp.CoolProp import PropsSI
import numpy as np


# ── Friction factor equaitons ─────────────────────────────────────────────────
def _f_colebrook(Re: float, Dh: float, roughness: float) -> float:
    relative_roughness = roughness / Dh
    rhs = -2.0 * np.log10(
        (relative_roughness / 3.7065) - (5.0452 / Re) * np.log10(2.8257 * pow(relative_roughness, 1.1098) + 5.8506 / (Re ** 0.8981))
    )
    f = 1.0 / pow(rhs, 2)
    return f

def _f_filonenko(Re: float) -> float:
    f = pow((1.82 * np.log10(Re) - 1.64), -2)
    return f



# ── Corrections ──────────────────────────────────────────────────────────────
def _petukhov_correction(f: float, T_cold_wall: float, T: float, p: float, velocity: float, Dh: float, coolant: str) -> float:
    wall_viscosity = PropsSI("V", "T", T_cold_wall, "P", p, coolant)
    wall_rho       = PropsSI("D", "T", T_cold_wall, "P", p, coolant)
    wall_Re = wall_rho * velocity * Dh / wall_viscosity

    exponent = -0.6 + 5.6 * pow(wall_Re, -0.38)
    return f * pow(T_cold_wall / T, exponent)



# ── Darcy-Weisbach model ──────────────────────────────────────────────────────
def _darcy_weisbach(f: float, rho: float, velocity: float, Dh: float, dx: float) -> float:
    return f * (dx / Dh) * 0.5 * rho * velocity ** 2


# ── Area change pressure drop ───────────────────────────────────────────────────
def _area_change_pressure_drop(rho: float, velocity: float, Dh_list: list, station_index: int) -> float:
    if station_index == 0:
        return 0.0

    Dh_i    = Dh_list[station_index]
    Dh_prev = Dh_list[station_index - 1]

    if abs(Dh_i - Dh_prev) < 1e-12:
        return 0.0

    dynamic_pressure = 0.5 * rho * pow(velocity, 2)

    if (Dh_i / Dh_prev) > 1.0:  # expansion
        area_ratio = pow(Dh_prev / Dh_i, 2)
        K = pow(1.0 - area_ratio, 2)
    else:           # contraction
        area_ratio = pow(Dh_i / Dh_prev, 2)
        K = 0.5 * (1.0 - area_ratio)

    return K * dynamic_pressure




# ── Colebrook-Petukhov ────────────────────────────────────────────────────────
def colebrook_petukhov(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    coolant   = state["coolant_parameters"]["coolant"]
    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re        = state["coolant_parameters"]["station_coolant_Re"][station_index]
    T         = state["coolant_parameters"]["station_coolant_T"][station_index]
    p         = state["coolant_parameters"]["station_coolant_p"][station_index]

    Dh_list     = state["channel_parameters"]["station_Dh"]
    roughness   = state["channel_parameters"]["channel_roughness"]
    T_cold_wall = state["results"]["T_cold_wall"][station_index]
    dx          = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])
    Dh          = Dh_list[station_index]


    # Colebrook friction factor
    try:
        f = _f_colebrook(Re, Dh, roughness)
    except Exception as e:
        errors.append(f"Colebrook friction factor calculation failed at station: {station_index} with {e}")
        return 0.0, errors


    try:
        f = _petukhov_correction(f, T_cold_wall, T, p, velocity, Dh, coolant)
    except Exception as e:
        errors.append(f"Petukhov correction failed at station: {station_index} with {e}")
        return 0.0, errors


    # Pressure drop calculation
    try:
        pressure_drop = _darcy_weisbach(f, rho, velocity, Dh, dx)
    except Exception as e:
        errors.append(f"Darcy Weisbach pressure drop calculation failed at: {station_index} with {e}")
        return 0.0, errors


    try:
        pressure_drop += _area_change_pressure_drop(rho, velocity, Dh_list, station_index)
    except Exception as e:
        errors.append(f"Area change pressure drop correction failed at: {station_index} with {e}")
        return 0.0, errors


    return pressure_drop, errors


# ── Filonenko-Petukhov ────────────────────────────────────────────────────────
def filonenko_petukhov(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    coolant   = state["coolant_parameters"]["coolant"]
    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re        = state["coolant_parameters"]["station_coolant_Re"][station_index]
    T         = state["coolant_parameters"]["station_coolant_T"][station_index]
    p         = state["coolant_parameters"]["station_coolant_p"][station_index]

    Dh_list     = state["channel_parameters"]["station_Dh"]
    T_cold_wall = state["results"]["T_cold_wall"][station_index]
    dx          = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])
    Dh          = Dh_list[station_index]

    # Filonenko friction factor
    try:
        f = _f_filonenko(Re)
    except Exception as e:
        errors.append(f"Colebrook friction factor calculation failed at station: {station_index} with {e}")
        return 0.0, errors


    try:
        f = _petukhov_correction(f, T_cold_wall, T, p, velocity, Dh, coolant)
    except Exception as e:
        errors.append(f"Petukhov correction failed at station: {station_index} with {e}")
        return 0.0, errors


    # Pressure drop calculation
    try:
        pressure_drop = _darcy_weisbach(f, rho, velocity, Dh, dx)
    except Exception as e:
        errors.append(f"Darcy Weisbach pressure drop calculation failed at: {station_index} with {e}")
        return 0.0, errors


    try:
        pressure_drop += _area_change_pressure_drop(rho, velocity, Dh_list, station_index)
    except Exception as e:
        errors.append(f"Area change pressure drop correction failed at: {station_index} with {e}")
        return 0.0, errors


    return pressure_drop, errors


# ── Colebrook ───────────────────────────────────────────────────────────────────
def colebrook(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re        = state["coolant_parameters"]["station_coolant_Re"][station_index]
    roughness = state["channel_parameters"]["channel_roughness"]

    Dh_list = state["channel_parameters"]["station_Dh"]
    dx      = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])
    Dh      = Dh_list[station_index]



    # Colebrook friction factor
    try:
        f = _f_colebrook(Re, Dh, roughness)
    except Exception as e:
        errors.append(f"Colebrook friction factor calculation failed at station: {station_index} with {e}")
        return 0.0, errors


    # Pressure drop calculation
    try:
        pressure_drop = _darcy_weisbach(f, rho, velocity, Dh, dx)
    except Exception as e:
        errors.append(f"Darcy Weisbach pressure drop calculation failed at: {station_index} with {e}")
        return 0.0, errors


    try:
        pressure_drop += _area_change_pressure_drop(rho, velocity, Dh_list, station_index)
    except Exception as e:
        errors.append(f"Area change pressure drop correction failed at: {station_index} with {e}")
        return 0.0, errors

    return pressure_drop, errors