from scipy.interpolate import interp1d
import numpy as np

from assets.data import NOZZLE_DATA


def generate_nozzle_contour(state: dict) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    Rt                       = state["engine_parameters"]["Rt"]
    eps                      = state["nozzle_parameters"]["eps"]
    CR                       = state["nozzle_parameters"]["CR"]
    L_star                   = state["nozzle_parameters"]["L_star"]
    nozzle_type              = state["nozzle_parameters"]["nozzle_type"]
    nozzle_length_percentage = state["nozzle_parameters"]["nozzle_length_percentage"] if nozzle_type == "bell" else None
    nozzle_angle             = state["nozzle_parameters"]["nozzle_angle"]             if nozzle_type == "conical" else None
    N                        = int(state["nozzle_parameters"]["nozzle_resolution"])

    # ── Arc radii and convergent half-angle ──────────────────────────────
    R1, R2, R3 = 0.7, 1.5, 0.382 
    theta_conv  = 45.0

    # ── Station counts ───────────────────────────────────────────────────
    if nozzle_type == "bell":
        N_chamber    = int(0.10 * N)
        N_convergent = int(0.15 * N)
        N_throat     = int(0.20 * N)
    else:
        N_chamber    = int(0.20 * N)
        N_convergent = int(0.25 * N)
        N_throat     = int(0.35 * N)

    N_divergent = N - N_chamber - N_convergent - N_throat

    # ── Divergent geometry ───────────────────────────────────────────────
    if nozzle_type == "bell":
        try:
            percentages    = np.array([60, 70, 80, 90, 100])
            thetan_values  = []
            thetae_values  = []

            for pct in percentages:
                n_data = NOZZLE_DATA[f"thetan_{pct}"]
                e_data = NOZZLE_DATA[f"thetae_{pct}"]
                thetan_values.append(interp1d(n_data["X"], n_data["Y"], kind="linear", fill_value="extrapolate")(eps))
                thetae_values.append(interp1d(e_data["X"], e_data["Y"], kind="linear", fill_value="extrapolate")(eps))

            thetan = float(interp1d(percentages, thetan_values, kind="linear", fill_value="extrapolate")(nozzle_length_percentage))
            thetae = float(interp1d(percentages, thetae_values, kind="linear", fill_value="extrapolate")(nozzle_length_percentage))

            nozzle_length = (nozzle_length_percentage / 100) * (np.sqrt(eps) - 1) * Rt / np.tan(np.radians(15))

        except Exception as e:
            errors.append(f"Bell angle lookup failed: {e}")
            return errors

    else:
        thetan        = nozzle_angle
        nozzle_length = (np.sqrt(eps) - 1) * Rt / np.tan(np.radians(nozzle_angle))

    # ── Convergent start x-coordinate ────────────────────────────────────
    sin_conv = np.sin(np.radians(theta_conv))
    cos_conv = np.cos(np.radians(theta_conv))
    cot_conv = 1.0 / np.tan(np.radians(theta_conv))

    x_conv_start = (
        - R2 * Rt * sin_conv
        - R1 * Rt * sin_conv
        - (cot_conv * Rt * (np.sqrt(CR) - 1)
           - R2 * Rt * (1 - cos_conv)
           - R1 * Rt * (1 - cos_conv))
    )

    xList, yList = [], []

    # ── Injector plate point ─────────────────────────────────────────────
    xList.append(x_conv_start - L_star / CR)
    yList.append(Rt * np.sqrt(CR))

    # ── Section 1 : chamber blend arc (R1) ───────────────────────────────
    try:
        thetas = np.linspace(0, theta_conv, N_chamber, endpoint=False)
        for theta in thetas:
            xList.append(x_conv_start + R1 * Rt * np.sin(np.radians(theta)))
            yList.append(Rt * np.sqrt(CR) - R1 * Rt * (1 - np.cos(np.radians(theta))))

    except Exception as e:
        errors.append(f"Section 1 (chamber blend) failed: {e}")
        return errors

    # ── Section 2 : convergent arc (R2) ──────────────────────────────────
    try:
        thetas = np.linspace(theta_conv, 0, N_convergent, endpoint=False)
        for theta in thetas:
            xList.append(-R2 * Rt * np.sin(np.radians(theta)))
            yList.append(Rt + R2 * Rt * (1 - np.cos(np.radians(theta))))

    except Exception as e:
        errors.append(f"Section 2 (convergent) failed: {e}")
        return errors

    # ── Section 3 : throat blend arc (R3) ────────────────────────────────
    try:
        thetas = np.linspace(0, thetan, N_throat, endpoint=False)
        for theta in thetas:
            xList.append(R3 * Rt * np.sin(np.radians(theta)))
            yList.append(Rt + R3 * Rt * (1 - np.cos(np.radians(theta))))

    except Exception as e:
        errors.append(f"Section 3 (throat blend) failed: {e}")
        return errors

    # ── Section 4 : divergent ─────────────────────────────────────────────
    if nozzle_type == "bell":
        try:
            P0x, P0y = xList[-1], yList[-1]
            P2x, P2y = nozzle_length, Rt * np.sqrt(eps)

            m0 = np.tan(np.radians(thetan))
            m2 = np.tan(np.radians(thetae))
            c0 = P0y - m0 * P0x
            c2 = P2y - m2 * P2x

            P1x = (c2 - c0) / (m0 - m2)
            P1y = (m0 * c2 - m2 * c0) / (m0 - m2)

            t_values = np.linspace(0, 1, max(N_divergent, 2))
            for t in t_values:
                xList.append((1-t)**2 * P0x + 2*t*(1-t) * P1x + t**2 * P2x)
                yList.append((1-t)**2 * P0y + 2*t*(1-t) * P1y + t**2 * P2y)

        except Exception as e:
            errors.append(f"Section 4 (bell divergent) failed: {e}")
            return errors

    else:
        try:
            P0x, P0y = xList[-1], yList[-1]

            x_values = np.linspace(P0x, nozzle_length, max(N_divergent, 2))
            for x in x_values:
                xList.append(x)
                yList.append(P0y + np.tan(np.radians(thetan)) * (x - P0x))

        except Exception as e:
            errors.append(f"Section 4 (conical divergent) failed: {e}")
            return errors

    # ── Zone identifier array ─────────────────────────────────────────────
    zone_x = np.array([0] * 1 + [1] * N_chamber + [2] * N_convergent + [3] * N_throat + [4] * N_divergent)

    # ── Write to state ────────────────────────────────────────────────────
    x_array = np.array(xList)
    y_array = np.array(yList)

    state["nozzle_parameters"]["x"]      = x_array - x_array.min()
    state["nozzle_parameters"]["R_x"]    = y_array
    state["nozzle_parameters"]["eps_x"]  = (y_array / Rt) ** 2
    state["nozzle_parameters"]["zone_x"] = zone_x

    return errors


def generate_jacket_geometry(state: dict) -> list[str]:
    errors = []

    # ── Unpack ───────────────────────────────────────────────────────────
    nozzle_x    = np.array(state["nozzle_parameters"]["x"])
    nozzle_R    = np.array(state["nozzle_parameters"]["R_x"])
    nozzle_eps  = np.array(state["nozzle_parameters"]["eps_x"])
    nozzle_zone = np.array(state["nozzle_parameters"]["zone_x"])

    control_points_position = state["channel_parameters"]["control_points_position"]
    control_points_cw       = state["channel_parameters"]["control_points_cw"]
    control_points_ch       = state["channel_parameters"]["control_points_ch"]
    N_channels              = state["channel_parameters"]["N_cooling_channels"]
    jacket_resolution       = state["channel_parameters"]["jacket_resolution"]
    interpolation_type      = state["channel_parameters"]["interpolation_type"]

    if interpolation_type == "Linear": interpolation_type = "linear"
    if interpolation_type == "Piecewise Constant": interpolation_type = "zero"


    # ── Build Jacket Geometry ────────────────────────────────────────────
    station_x    = np.linspace(control_points_position[0], control_points_position[-1], jacket_resolution)
    station_R    = np.interp(station_x, nozzle_x, nozzle_R)
    station_eps  = np.interp(station_x, nozzle_x, nozzle_eps)
    station_zone = [max(1, int(nozzle_zone[np.argmin(np.abs(nozzle_x - x))])) for x in station_x]


    # ── Flip control points if coolant flows outlet → inlet ──────────────
    if control_points_position[0] > control_points_position[-1]:
        control_points_position = control_points_position[::-1]
        control_points_cw = control_points_cw[::-1]
        control_points_ch = control_points_ch[::-1]

    
    cw_interp = interp1d(control_points_position, control_points_cw, kind=interpolation_type)
    ch_interp = interp1d(control_points_position, control_points_ch, kind=interpolation_type)

    station_cw = cw_interp(station_x)
    station_ch = ch_interp(station_x)

    station_Dh = 2.0 * station_cw * station_ch / (station_cw + station_ch)
    station_landwidth = (2.0 * np.pi * station_R / N_channels) - station_cw
    station_A_channel = station_cw * station_ch
    station_A_heat_transfer = 2.0 * np.pi * station_R * abs(np.gradient(station_x))


    # Important naming scheme : station_value refers to the list of the values at each station
    state["nozzle_parameters"]["station_x"] = station_x.tolist()
    state["nozzle_parameters"]["station_R"] = station_R.tolist()
    state["nozzle_parameters"]["station_eps"] = station_eps.tolist()
    state["nozzle_parameters"]["station_zone"] = station_zone

    state["channel_parameters"]["station_cw"] = station_cw.tolist()
    state["channel_parameters"]["station_ch"] = station_ch.tolist()
    state["channel_parameters"]["station_Dh"] = station_Dh.tolist()
    state["channel_parameters"]["station_landwidth"] = station_landwidth.tolist()
    state["channel_parameters"]["station_A_channel"] = station_A_channel.tolist()
    state["channel_parameters"]["station_A_heat_transfer"] = station_A_heat_transfer.tolist()

    # Check landwidth
    if np.any(station_landwidth <= 0):
        for i in (np.where(station_landwidth <= 0)[0]):
            errors.append(f"Landwidth <= 0 at station {i} (x={station_x[i]*100:.2f} cm): cw={station_cw[i]*1000:.2f} mm exceeds available wall pitch")
        return errors

    return errors


def generate_mesh(nx: int, ny: int, cw: float, ch: float, lw: float, t: float) -> dict:
    mesh_width = (lw + cw) / 2
    mesh_height = ch + 2 * t

    x = np.linspace(0, mesh_width, nx)
    y = np.linspace(0, mesh_height, ny)

    # Channel bounds
    x0 = (mesh_width - cw / 2)
    x1 = x0 + cw
    y0 = (mesh_height - ch - t)
    y1 = y0 + ch

    mask = np.ones((nx, ny), dtype=bool)
    index_map = -np.ones((nx, ny), dtype=int)

    counter = 0
    for i in range(nx):
        for j in range(ny):
            if (x0 <= x[i] <= x1 and y0 <= y[j] <= y1):
                mask[i, j] = False
            else:
                index_map[i, j] = counter
                counter += 1

    mesh = {"nx": nx, "ny": ny, "x": x, "y": y, "mask": mask, "index_map": index_map}

    return mesh