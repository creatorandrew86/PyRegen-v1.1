from rocketcea.cea_obj_w_units import CEA_Obj as CEA_Obj_SI_units
from rocketcea.cea_obj import CEA_Obj as CEA_Obj_default_units
import numpy as np


def run_cea_SI_units(state: dict) -> list[str]:
    errors = []

    engine_params = state["engine_parameters"]
    nozzle_params = state["nozzle_parameters"]

    try: 
        c = CEA_Obj_SI_units(oxName=engine_params["oxidizer"], fuelName=engine_params["fuel"], fac_CR=nozzle_params["CR"], pressure_units="Pa",
                    temperature_units="K", cstar_units="m/s", sonic_velocity_units="m/s", density_units="kg/m^3", specific_heat_units="J/kg-K")
        
        # Store the CEA object in the state dict
        engine_params["CEA_Obj_SI_units"] = c

        # Update the state dict with the CEA values
        engine_params["Tc"] = c.get_Tcomb(Pc = engine_params["Pc"], MR = engine_params["MR"])
        engine_params["C_star"] = c.get_Cstar(Pc = engine_params["Pc"], MR = engine_params["MR"])

        chamber_transport = c.get_Chamber_Transport(Pc=engine_params["Pc"], MR=engine_params["MR"], eps=nozzle_params["eps"], frozen=1)
        engine_params["chamber_Cp"] = chamber_transport[0]
        engine_params["chamber_viscosity"] = chamber_transport[1] * 1e-4 
        engine_params["chamber_Pr"] = chamber_transport[3]   



        # Calculate throat radius / mass flow rate
        throat_c = c.get_SonicVelocities(Pc=engine_params["Pc"], MR=engine_params["MR"], eps=nozzle_params["eps"])[1]
        throat_rho = c.get_Densities(Pc=engine_params["Pc"], MR=engine_params["MR"], eps=nozzle_params["eps"])[1]

        if engine_params["throat_sizing_method"] == "given_radius":
            nozzle_params["At"] = np.pi * pow(engine_params["Rt"], 2)
            engine_params["mass_flow_rate"] = throat_c * throat_rho * nozzle_params["At"]

        elif engine_params["throat_sizing_method"] == "mass_flow":
            nozzle_params["At"] = engine_params["mass_flow_rate"] / (throat_c * throat_rho)
            engine_params["Rt"] = np.sqrt(nozzle_params["At"] / np.pi)

    except Exception as e:
        errors.append(f"CEA Error: {e}")

    return errors


def run_cea_default_units(state: dict) -> list[str]:
    errors = []

    engine_params = state["engine_parameters"]
    nozzle_params = state["nozzle_parameters"]

    try:
        c = CEA_Obj_default_units(oxName=engine_params["oxidizer"], fuelName=engine_params["fuel"], fac_CR=nozzle_params["CR"])
        engine_params["CEA_Obj_default_units"] = c

        engine_params["Isp"]  = c.get_SonicVelocities(Pc=engine_params["Pc"]/6894.7, MR=engine_params["MR"], eps=nozzle_params["eps"])[2] / 3.28 * \
                                c.get_MachNumber(Pc=engine_params["Pc"]/6894.7, MR=engine_params["MR"], eps=nozzle_params["eps"]) / 9.81
        engine_params["Ivac"] = c.get_IvacCstrTc(Pc=engine_params["Pc"]/6894.7, MR=engine_params["MR"], eps=nozzle_params["eps"])[0]
    except Exception as e:
        errors.append(f"CEA Error: {e}")

    return errors