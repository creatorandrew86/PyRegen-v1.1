from rocketcea.cea_obj_w_units import CEA_Obj as CEA_Obj_SI_units
from rocketcea.cea_obj import CEA_Obj as CEA_Obj_default_units
import numpy as np


def run_cea(state: dict) -> list[str]:
    errors = []

    oxidizer = state["engine_parameters"]["oxidizer"]
    fuel     = state["engine_parameters"]["fuel"]
    Pc       = state["engine_parameters"]["Pc"]
    Pc_psia  = Pc / 6894.7
    MR       = state["engine_parameters"]["MR"]
    Rt       = state["engine_parameters"]["Rt"]
    mass_flow = state["engine_parameters"]["mass_flow_rate"]

    CR     = state["nozzle_parameters"]["CR"]
    eps    = state["nozzle_parameters"]["eps"]

    try: 
        c_SI_units = CEA_Obj_SI_units(oxName=oxidizer, fuelName=fuel, fac_CR=CR, pressure_units="Pa", temperature_units="K", cstar_units="m/s", 
                                      sonic_velocity_units="m/s", density_units="kg/m^3", specific_heat_units="J/kg-K")
        
        c_default_units = CEA_Obj_default_units(oxName=oxidizer, fuelName=fuel, fac_CR=CR)
        
        # Store the CEA object in the state dict
        state["engine_parameters"]["CEA_Obj_SI_units"]      = c_SI_units
        state["engine_parameters"]["CEA_Obj_default_units"] = c_default_units

        # Update the state dict with the CEA values
        state["engine_parameters"]["Tc"]                     = c_SI_units.get_Tcomb(Pc=Pc, MR=MR)
        state["engine_parameters"]["C_star"]                 = c_SI_units.get_Cstar(Pc=Pc, MR=MR)
        state["engine_parameters"]["Isp"]                    = c_default_units.get_SonicVelocities(Pc=Pc_psia, MR=MR, eps=eps)[2] / 3.28 * \
                                                               c_default_units.get_MachNumber(Pc=Pc_psia, MR=MR, eps=eps) / 9.81
        state["engine_parameters"]["Ivac"]                   = c_default_units.get_IvacCstrTc(Pc=Pc_psia, MR=MR, eps=eps)[0]
        state["engine_parameters"]["species_mass_fractions"] = c_SI_units.get_SpeciesMassFractions(Pc=Pc, MR=MR, eps=eps, min_fraction=0.00001)


        chamber_transport = c_SI_units.get_Chamber_Transport(Pc=Pc, MR=MR, eps=eps, frozen=1)
        state["engine_parameters"]["chamber_Cp"] = chamber_transport[0]
        state["engine_parameters"]["chamber_viscosity"] = chamber_transport[1] * 1e-4 
        state["engine_parameters"]["chamber_Pr"] = chamber_transport[3]   


        # Calculate throat radius / mass flow rate
        throat_c = c_SI_units.get_SonicVelocities(Pc=Pc, MR=MR, eps=eps)[1]
        throat_rho = c_SI_units.get_Densities(Pc=Pc, MR=MR, eps=eps)[1]

        if state["engine_parameters"]["throat_sizing_method"] == "given_radius":
            state["nozzle_parameters"]["At"] = np.pi * pow(Rt, 2)
            state["engine_parameters"]["mass_flow_rate"] = throat_c * throat_rho * state["nozzle_parameters"]["At"]

        elif state["engine_parameters"]["throat_sizing_method"] == "mass_flow":
            state["nozzle_parameters"]["At"] = mass_flow / (throat_c * throat_rho)
            state["engine_parameters"]["Rt"] = np.sqrt(state["nozzle_parameters"]["At"] / np.pi)

    except Exception as e:
        errors.append(f"CEA Error: {e}")

    return errors


def get_station_values(state: dict, station_index: int, zone: int) -> tuple[float, float, float, float, list[str]]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    Pc      = state["engine_parameters"]["Pc"]
    Pc_psia = Pc / 6894.7
    MR      = state["engine_parameters"]["MR"]
    Tc      = state["engine_parameters"]["Tc"]
    eps     = state["nozzle_parameters"]["station_eps"][station_index]

    c_SI_units      : CEA_Obj_SI_units      = state["engine_parameters"]["CEA_Obj_SI_units"]
    c_default_units : CEA_Obj_default_units = state["engine_parameters"]["CEA_Obj_default_units"]

    # ── CEA gas properties ───────────────────────────────────────────────
    try:
        if zone in (0, 1) :
            full_output = c_default_units.get_full_cea_output(Pc=Pc_psia, MR=MR, eps=eps, subar=eps, output='siunits')
            lines = full_output.split("\n")

            mach, Pr_gas = 0.2, 0.7
            for line in lines:
                if 'MACH NUMBER' in line:
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
            gamma  = float(c_SI_units.get_Throat_MolWt_gamma(Pc=Pc, MR=MR)[1])
            mach   = 1.0
            T_gas  = float(c_SI_units.get_Temperatures(Pc=Pc, MR=MR, eps=eps)[1])
            Pr_gas = float(c_SI_units.get_Throat_Transport(Pc=Pc, MR=MR, eps=eps)[3])

        elif zone == 4:
            gamma  = float(c_SI_units.get_exit_MolWt_gamma(Pc=Pc, MR=MR, eps=eps)[1])
            mach   = float(c_SI_units.get_MachNumber(Pc=Pc, MR=MR, eps=eps))
            T_gas  = float(c_SI_units.get_Temperatures(Pc=Pc, MR=MR, eps=eps)[2])
            Pr_gas = float(c_SI_units.get_Exit_Transport(Pc=Pc, MR=MR, eps=eps)[3])

        else:
            errors.append(f"Unknown nozzle zone {zone}")
            return 0.0, 0.0, 0.0, 0.0, 0.0, errors

    except Exception as e:
        errors.append(f"CEA lookup failed at eps={eps:.2f} — {e}")
        return 0.0, 0.0, 0.0, 0.0, 0.0, errors


    # ── Adiabatic Wall Temp ──────────────────────────────────────────────
    T_aw = Tc * (1.0 + pow(Pr_gas, 1/3) * (gamma - 1.0) / 2.0 * pow(mach, 2)) / (1.0 + (gamma - 1.0) / 2.0 * pow(mach, 2))

    return T_gas, T_aw, gamma, mach, errors