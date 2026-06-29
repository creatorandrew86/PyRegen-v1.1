from CoolProp.CoolProp import PropsSI
import numpy as np


# ── Friction factor equaitons ─────────────────────────────────────────────────
def _f_colebrook(Re: float, Dh: float, roughness: float) -> float:
    eps_over_Dh = roughness / Dh
    rhs = -2.0 * np.log10(
        eps_over_Dh / 3.7065
        - (5.0452 / Re) * np.log10(
            2.8257 * (eps_over_Dh ** 1.1098)
            + 5.8506 / (Re ** 0.8981)
        )
    )
    return 1.0 / (rhs ** 2)

def _f_filonenko(Re: float) -> float:
    return (1.82 * np.log10(Re) - 1.64) ** -2



# ── Corrections ──────────────────────────────────────────────────────────────
def _petukhov_correction(f: float, T_cold_wall: float, T_bulk: float, wall_Re: float) -> float:
    exponent = -0.6 + 5.6 * pow(wall_Re, -0.38)
    return f * pow(T_cold_wall / T_bulk, exponent)



# ── Area change pressure drop ───────────────────────────────────────────────────
def _area_change_pressure_drop(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    if station_index == 0:
        return 0.0, errors

    rho      = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Dh_i     = state["channel_parameters"]["station_Dh"][station_index]
    Dh_prev  = state["channel_parameters"]["station_Dh"][station_index - 1]

    if abs(Dh_i - Dh_prev) < 1e-12:
        return 0.0, errors

    dynamic_pressure = 0.5 * rho * pow(velocity, 2)

    if (Dh_i / Dh_prev) > 1.0:  # expansion
        area_ratio = pow(Dh_prev / Dh_i, 2)
        K = pow(1.0 - area_ratio, 2)
    else:           # contraction
        area_ratio = pow(Dh_i / Dh_prev, 2)
        K = 0.5 * (1.0 - area_ratio)

    return K * dynamic_pressure, errors


# ── Darcy-Weisbach model ──────────────────────────────────────────────────────
def _darcy_weisbach(f: float, rho: float, velocity: float, Dh: float, dx: float) -> float:
    return f * (dx / Dh) * 0.5 * rho * velocity ** 2



# ── Colebrook-Petukhov ────────────────────────────────────────────────────────
def pressure_drop_colebrook_petukhov(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    # Bulk coolant values
    coolant   = state["coolant_parameters"]["coolant"]
    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re        = state["coolant_parameters"]["station_coolant_Re"][station_index]
    T         = state["coolant_parameters"]["station_coolant_T"][station_index]
    p         = state["coolant_parameters"]["station_coolant_p"][station_index]

    # Geoemtry and T_cold_wall
    Dh          = state["channel_parameters"]["station_Dh"][station_index]
    roughness   = state["channel_parameters"]["channel_roughness"]
    T_cold_wall = state["results"]["T_cold_wall"][station_index]
    dx          = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])

    # Uncorrected Colebrook friction factor
    f = _f_colebrook(Re, Dh, roughness)

    try:
        wall_viscosity = PropsSI("V", "T", T_cold_wall, "P", p, coolant)
        wall_rho       = PropsSI("D", "T", T_cold_wall, "P", p, coolant)
    except Exception as e:
        errors.append(f"CoolProp wall properties lookup failed at {T_cold_wall:.2f}, at station: {station_index} with {e}")

    wall_Re = wall_rho * velocity * Dh / wall_viscosity

    # Correct friction factor
    f = _petukhov_correction(f, T_cold_wall, T, wall_Re)

    dP_friction            = _darcy_weisbach(f, rho, velocity, Dh, dx)
    dP_area, area_errors   = _area_change_pressure_drop(state, station_index)
    errors.extend(area_errors)

    return dP_friction + dP_area, errors


# ── Filonenko-Petukhov ────────────────────────────────────────────────────────
def pressure_drop_filonenko_petukhov(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    # Bulk coolant values
    coolant   = state["coolant_parameters"]["coolant"]
    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re        = state["coolant_parameters"]["station_coolant_Re"][station_index]
    T         = state["coolant_parameters"]["station_coolant_T"][station_index]
    p         = state["coolant_parameters"]["station_coolant_p"][station_index]

    # Geoemtry and T_cold_wall
    Dh          = state["channel_parameters"]["station_Dh"][station_index]
    T_cold_wall = state["results"]["T_cold_wall"][station_index]
    dx          = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])

    # uncorrected filonenko friction factor
    f = _f_filonenko(Re)

    try:
        wall_viscosity = PropsSI("V", "T", T_cold_wall, "P", p, coolant)
        wall_rho       = PropsSI("D", "T", T_cold_wall, "P", p, coolant)
    except Exception as e:
        errors.append(f"CoolProp wall properties lookup failed at {T_cold_wall:.2f}, at station: {station_index} with {e}")

    wall_Re = wall_rho * velocity * Dh / wall_viscosity

    # Correct friction factor
    f = _petukhov_correction(f, T_cold_wall, T, wall_Re)

    dP_friction          = _darcy_weisbach(f, rho, velocity, Dh, dx)
    dP_area, area_errors = _area_change_pressure_drop(state, station_index)
    errors.extend(area_errors)

    return dP_friction + dP_area, errors


# ── Colebrook ───────────────────────────────────────────────────────────────────
def pressure_drop_colebrook(state: dict, station_index: int) -> tuple[float, list[str]]:
    errors = []

    rho       = state["coolant_parameters"]["station_coolant_rho"][station_index]
    velocity  = state["coolant_parameters"]["station_coolant_velocity"][station_index]
    Re_bulk   = state["coolant_parameters"]["station_coolant_Re"][station_index]
    Dh        = state["channel_parameters"]["station_Dh"][station_index]
    roughness = state["channel_parameters"]["channel_roughness"]

    dx = abs(state["nozzle_parameters"]["station_x"][1] - state["nozzle_parameters"]["station_x"][0])

    f = _f_colebrook(Re_bulk, Dh, roughness)

    dP_friction          = _darcy_weisbach(f, rho, velocity, Dh, dx)
    dP_area, area_errors = _area_change_pressure_drop(state, station_index)
    errors.extend(area_errors)

    return dP_friction + dP_area, errors