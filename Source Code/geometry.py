from scipy.interpolate import interp1d
import numpy as np
import math

import data

def run_geometry(state: dict) -> list[str]:
    errors = []

    nozzle_params = state["nozzle_parameters"]

    Rt = state["engine_parameters"]["Rt"]
    eps = nozzle_params["eps"]
    CR = nozzle_params["CR"]
    L_star = nozzle_params["L_star"]
    nozzle_type = nozzle_params["nozzle_type"]
    nozzle_length_percentage = nozzle_params["nozzle_length_percentage"] if nozzle_type == "bell" else None
    nozzle_angle = nozzle_params["nozzle_angle"] if nozzle_type == "conical" else None
    N = int(nozzle_params["nozzle_resolution"])

    R1, R2, R3 = 0.7, 1.5, 0.382 
    theta_conv = 45

    N_chamber = int(0.1 * N) if nozzle_type == "bell" else int(0.2 * N)
    N_convergent = int(0.15 * N) if nozzle_type == "bell" else int(0.25 * N)
    N_throat = int(0.2 * N) if nozzle_type == "bell" else int(0.35 * N)
    N_divergent = N - N_chamber - N_convergent - N_throat

    xList, yList = [], []

    # Bell: fetch thetan/thetae from lookup table
    if nozzle_type == "bell":
        try:
            percentages = np.array([60, 70, 80, 90, 100])
            thetan_values, thetae_values = [], []

            for pct in percentages:
                n_data = data.NOZZLE_DATA[f"thetan_{pct}"]
                e_data = data.NOZZLE_DATA[f"thetae_{pct}"]
                thetan_values.append(interp1d(n_data["X"], n_data["Y"], kind="linear", fill_value="extrapolate")(eps))
                thetae_values.append(interp1d(e_data["X"], e_data["Y"], kind="linear", fill_value="extrapolate")(eps))

            thetan = float(interp1d(percentages, thetan_values, kind="linear", fill_value="extrapolate")(nozzle_length_percentage))
            thetae = float(interp1d(percentages, thetae_values, kind="linear", fill_value="extrapolate")(nozzle_length_percentage))

            nozzle_length = (nozzle_length_percentage / 100) * (math.sqrt(eps) - 1) * Rt / math.tan(math.radians(15))
        except Exception as e:
            errors.append(f"Bell angle lookup failed: {e}")
            return errors
    else:
        thetan = nozzle_angle
        nozzle_length = (math.sqrt(eps) - 1) * Rt / math.tan(math.radians(nozzle_angle))

    # x-coordinate of the upstream end of the r1 arc
    def x_convergent_start():
        return (
            -R2 * Rt * math.sin(math.radians(theta_conv))
            - R1 * Rt * math.sin(math.radians(theta_conv))
            - ((1 / math.tan(math.radians(theta_conv))) * Rt * (math.sqrt(CR) - 1)
               - R2 * Rt * (1 - math.cos(math.radians(theta_conv)))
               - R1 * Rt * (1 - math.cos(math.radians(theta_conv))))
        )

    # Injector Plate point
    xList.append(x_convergent_start() - L_star / CR)
    yList.append(Rt * math.sqrt(CR))

    # Section 1: chamber blend arc (R1)
    try:
        x_start = x_convergent_start()
        for i in range(N_chamber):
            theta = i * (theta_conv / N_chamber)
            xList.append(x_start + R1 * Rt * math.sin(math.radians(theta)))
            yList.append(Rt * math.sqrt(CR) - R1 * Rt * (1 - math.cos(math.radians(theta))))

    except Exception as e:
        errors.append(f"Section 1 (chamber blend) failed: {e}")
        return errors

    # Section 2: convergent-to-throat arc (R2)
    try:
        for i in range(N_convergent):
            theta = theta_conv - i * (theta_conv / N_convergent)
            xList.append(-R2 * Rt * math.sin(math.radians(theta)))
            yList.append(Rt + R2 * Rt * (1 - math.cos(math.radians(theta))))

    except Exception as e:
        errors.append(f"Section 2 (convergent) failed: {e}")
        return errors

    # Section 3: throat-to-divergent arc (R3)
    try:
        for i in range(N_throat):
            theta = i * (thetan / N_throat)
            xList.append(R3 * Rt * math.sin(math.radians(theta)))
            yList.append(Rt + R3 * Rt * (1 - math.cos(math.radians(theta))))

    except Exception as e:
        errors.append(f"Section 3 (throat blend) failed: {e}")
        return errors

    # Section 4: divergent
    if nozzle_type == "bell":
        try:
            # Bezier curve generator
            P0x, P0y = xList[-1], yList[-1]
            P2x, P2y = nozzle_length, Rt * math.sqrt(eps)

            m0 = math.tan(math.radians(thetan))
            m2 = math.tan(math.radians(thetae))

            c0, c2 = P0y - m0 * P0x, P2y - m2 * P2x
            P1x = (c2 - c0) / (m0 - m2)
            P1y = (m0 * c2 - m2 * c0) / (m0 - m2)

            for i in range(N_divergent if N_divergent > 1 else 1):
                t = i / (N_divergent - 1) if N_divergent > 1 else 1.0
                xList.append((1-t)**2 * P0x + 2*t*(1-t) * P1x + t**2 * P2x)
                yList.append((1-t)**2 * P0y + 2*t*(1-t) * P1y + t**2 * P2y)

        except Exception as e:
            errors.append(f"Section 4 (bell divergent) failed: {e}")
            return errors
        
    else:
        try:
            x_div_start, y_div_start = xList[-1], yList[-1]
            dx = (nozzle_length - x_div_start) / (N_divergent - 1) if N_divergent > 1 else 0
            for i in range(N_divergent if N_divergent > 1 else 1):
                xList.append(x_div_start + i * dx)
                yList.append(y_div_start + math.tan(math.radians(thetan)) * i * dx)
            if N_divergent <= 1:
                xList.append(nozzle_length)
                yList.append(Rt * math.sqrt(eps))
        except Exception as e:
            errors.append(f"Section 4 (conical divergent) failed: {e}")
            return errors

    # Zone identifier array
    N_injector_plate = 1
    zone_x = np.array([0] * N_injector_plate + [1] * N_chamber + [2] * N_convergent + [3] * N_throat + [4] * N_divergent)

    nozzle_params["x"] = np.array(xList) - min(xList)
    nozzle_params["R_x"] = np.array(yList)
    nozzle_params["eps_x"] = pow(np.array(yList) / Rt, 2)
    nozzle_params["zone_x"] = zone_x

    return errors