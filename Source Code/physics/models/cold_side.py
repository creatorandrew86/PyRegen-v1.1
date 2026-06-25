from CoolProp.CoolProp import PropsSI
import numpy as np


# ── Roughness correction ─────────────────────────────────────────────────────
def _roughness_correction(coolant_Re: float, coolant_Pr: float) -> float:
    f        = pow(0.79 * np.log(coolant_Re) - 1.64, -2)
    f_smooth = 0.0032 + 0.221 * pow(coolant_Re, -0.237)
    zeta = f / f_smooth
    
    roughness_factor = (
        zeta * (1 + (1.5 * pow(coolant_Pr, -1/6) * pow(coolant_Re, -1/8)) * (coolant_Pr - 1))
             / (1 + (1.5 * pow(coolant_Pr, -1/6) * pow(coolant_Re, -1/8)) * (zeta * coolant_Pr - 1))
    )

    return roughness_factor


# ── Wall viscosity correction ─────────────────────────────────────────────────
def _wall_viscosity_correction(coolant: str, T_bulk: float, T_cold_wall: float, p: float) -> float:
    bulk_viscosity = PropsSI("V", "T", T_bulk,      "P", p, coolant)
    wall_viscosity = PropsSI("V", "T", T_cold_wall, "P", p, coolant)
    wall_viscosity_factor = pow(bulk_viscosity / wall_viscosity, 0.14)

    return wall_viscosity_factor


# ── Entrance correction ──────────────────────────────────────────────────────
def _entrance_correction(station_x: list, station_index: int, Dh: float, T: float, T_cold_wall: float) -> float:
    s = abs(station_x[station_index] - station_x[0]) 
    entrance_factor = 1.0 + pow(s / Dh, -0.7) * pow(T_cold_wall / T, 0.1) if station_index != 0 else 1.0

    return entrance_factor


# ── Nusselt Number Equations ─────────────────────────────────────────────────
def _gnielinski_nu(Re: float, Pr: float) -> float:
    f  = pow(0.79 * np.log(Re) - 1.64, -2)
    Nu = ((f / 8) * (Re - 1000) * Pr) / (1 + 12.7 * np.sqrt((f / 8) * (pow(Pr, 2/3) - 1)))
    return Nu

def _sieder_tate_nu(Re: float, Pr: float) -> float:
    Nu = 0.027 * pow(Re, 0.8) * pow(Pr, 1/3)
    return Nu

def _dittus_boelter_nu(Re: float, Pr: float, heating: bool = True) -> float:
    n  = 0.4 if heating else 0.3
    Nu = 0.023 * pow(Re, 0.8) * pow(Pr, n)
    return Nu



# ── Gnielinski ───────────────────────────────────────────────────────────────
def cold_side_gnielinski(state: dict, station_index: int, T_cold_wall: float) -> tuple[float, list[str]]:
    """
    Gnielinski correlation with roughness correction.
    Valid: 3000 < Re < 1e6.
    """
    errors = []

    Re = state["coolant_parameters"]["station_coolant_Re"][station_index]
    Pr = state["coolant_parameters"]["station_coolant_Pr"][station_index]
    k  = state["coolant_parameters"]["station_coolant_k"][station_index]
    Dh = state["channel_parameters"]["station_Dh"][station_index]

    try:
        Nu = _gnielinski_nu(Re, Pr)
        h_coolant = Nu * k / Dh
    except Exception as e:
        errors.append(f"Gnielinski failed at station {station_index}: {e}")
        return 0.0, errors

    try:
        h_coolant *= _roughness_correction(Re, Pr)
    except Exception as e:
        errors.append(f"Roughness correction failed at station {station_index}: {e}")

    return h_coolant, errors


# ── Sieder-Tate ───────────────────────────────────────────────────────────────
def cold_side_sieder_tate(state: dict, station_index: int, T_cold_wall: float) -> tuple[float, list[str]]:
    """
    Sieder-Tate correlation with roughness correction.
    Valid: Re > 1e4, large wall-to-bulk viscosity ratio.
    """
    errors  = []

    station_x = state["nozzle_parameters"]["station_x"]

    coolant = state["coolant_parameters"]["coolant"]
    Re      = state["coolant_parameters"]["station_coolant_Re"][station_index]
    Pr      = state["coolant_parameters"]["station_coolant_Pr"][station_index]
    k       = state["coolant_parameters"]["station_coolant_k"][station_index]
    Dh      = state["channel_parameters"]["station_Dh"][station_index]
    T       = state["coolant_parameters"]["station_coolant_T"][station_index]
    p       = state["coolant_parameters"]["station_coolant_p"][station_index]

 

    try:
        Nu = _sieder_tate_nu(Re, Pr)
        h_coolant = Nu * k / Dh
    except Exception as e:
        errors.append(f"Sieder-Tate failed at station {station_index}: {e}")
        return 0.0, errors
    

    try:
        h_coolant *= _wall_viscosity_correction(coolant, T, T_cold_wall, p)
    except Exception as e:
        errors.append(f"Wall viscosity correction failed at station {station_index}: {e}")


    try:
        h_coolant *= _entrance_correction(station_x, station_index, Dh, T, T_cold_wall)
    except Exception as e:
        errors.append(f"Entrance correction failed at station {station_index}: {e}")


    try:
        h_coolant *= _roughness_correction(Re, Pr)
    except Exception as e:
        errors.append(f"Roughness correction failed at station {station_index}: {e}")

    return h_coolant, errors


# ── Dittus-Boelter ───────────────────────────────────────────────────────────
def cold_side_dittus_boelter(state: dict, station_index: int, T_cold_wall: float) -> tuple[float, list[str]]:
    """
    Dittus-Boelter correlation with roughness correction.
    Valid: Re > 1e4, 0.6 < Pr < 160, smooth tubes, low wall-to-bulk temperature ratio.
    Returns (h_coolant [W/m²K], errors).
    """
    errors = []

    station_x = state["nozzle_parameters"]["station_x"]

    coolant = state["coolant_parameters"]["coolant"]
    Re      = state["coolant_parameters"]["station_coolant_Re"][station_index]
    Pr      = state["coolant_parameters"]["station_coolant_Pr"][station_index]
    k       = state["coolant_parameters"]["station_coolant_k"][station_index]
    Dh      = state["channel_parameters"]["station_Dh"][station_index]
    T       = state["coolant_parameters"]["station_coolant_T"][station_index]
    p       = state["coolant_parameters"]["station_coolant_p"][station_index]

    try:
        Nu = _dittus_boelter_nu(Re, Pr, heating=True)
        h_coolant = Nu * k / Dh
    except Exception as e:
        errors.append(f"Dittus-Boelter failed at station {station_index}: {e}")
        return 0.0, errors
    

    try:
        h_coolant *= _wall_viscosity_correction(coolant, T, T_cold_wall, p)
    except Exception as e:
        errors.append(f"Wall viscosity correction failed at station {station_index}: {e}")


    try:
        h_coolant *= _entrance_correction(station_x, station_index, Dh, T, T_cold_wall)
    except Exception as e:
        errors.append(f"Entrance correction failed at station {station_index}: {e}")


    try:
        h_coolant *= _roughness_correction(Re, Pr)
    except Exception as e:
        errors.append(f"Roughness correction failed at station {station_index}: {e}")

    return h_coolant, errors