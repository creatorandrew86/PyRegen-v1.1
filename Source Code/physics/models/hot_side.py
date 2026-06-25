def _sigma(T_hot_wall: float, Tc: float, gamma: float, mach: float) -> float:
    mach_term = 1.0 + (gamma - 1.0) / 2.0 * mach ** 2
    return (pow(0.5 * (T_hot_wall / Tc) * mach_term + 0.5, -0.68) * pow(mach_term, -0.12))

def _radiative_correction(species_mass_fractions: tuple[dict, dict], L_star: float, Pc: float, T_aw: float, T_hot_wall: float) -> float:
    partial_pressure_H2O = species_mass_fractions[1]['H2O'][-1] * Pc / 101325 if 'H2O' in species_mass_fractions[1] else 0
    partial_pressure_CO2 = species_mass_fractions[1]['*CO2'][-1] * Pc / 101325 if '*CO2' in species_mass_fractions[1] else 0

    Q_flux_H2O = 4.07 * pow(partial_pressure_H2O, 0.8) * pow(0.006 * L_star, 0.6) * (pow(T_aw/100, 3) - pow(T_hot_wall/100, 3))
    Q_flux_CO2 = 4.07 * pow(partial_pressure_CO2 * 0.006 * L_star, 1/3) * (pow(T_aw/100, 3.5) - pow(T_hot_wall/100, 3.5))

    return (Q_flux_H2O + Q_flux_CO2) / (T_aw - T_hot_wall)


# ── Bartz ─────────────────────────────────────────────────────────────────────
def hot_side_bartz(state: dict, station_index: int, T_hot_wall: float) -> tuple[float, list[str]]:
    """
    Bartz correlation for hot-gas-side heat transfer.
    """
    errors = []

    Tc                = state["engine_parameters"]["Tc"]
    Pc                = state["engine_parameters"]["Pc"]
    C_star            = state["engine_parameters"]["C_star"]
    Rt                = state["engine_parameters"]["Rt"]
    T_aw              = state["engine_parameters"]["station_T_aw"][station_index]
    gamma             = state["engine_parameters"]["station_gamma"][station_index]
    mach              = state["engine_parameters"]["station_mach"][station_index]
    chamber_viscosity = state["engine_parameters"]["chamber_viscosity"]
    chamber_Cp        = state["engine_parameters"]["chamber_Cp"]
    chamber_Pr        = state["engine_parameters"]["chamber_Pr"]

    species_mass_fractions = state["engine_parameters"]["species_mass_fractions"]
    L_star                 = state["nozzle_parameters"]["L_star"]
    eps                    = state["nozzle_parameters"]["station_eps"][station_index]

    try:
        h_gas = (
            (0.026 / pow(Rt * 2.0, 0.2))
            * (pow(chamber_viscosity, 0.2) * chamber_Cp / pow(chamber_Pr, 0.6))
            * pow(Pc / C_star, 0.8)
            * pow(1.0 / eps, 0.9)
            * 1.029
        )
    except ZeroDivisionError as e:
        errors.append(f"Bartz division by zero at station {station_index}: {e}")
        return 0.0, 0.0, errors
    

    try:
        h_gas *= _sigma(T_hot_wall, Tc, gamma, mach)
    except Exception as e:
        errors.append(f"Wall boundary layer correction failed at station {station_index} with {e}")
    

    try:
        h_gas += _radiative_correction(species_mass_fractions, L_star, Pc, T_aw, T_hot_wall)
    except Exception as e:
        errors.append(f"Radiative heating correction failed at station {station_index} with {e}")

    return h_gas, errors