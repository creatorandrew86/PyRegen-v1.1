from scipy.sparse import lil_matrix, csc_matrix
from scipy.sparse.linalg import spsolve
from scipy.interpolate import interp1d
from scipy.optimize import fsolve
import numpy as np

from core.geometry import generate_mesh

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


def _build_laplacian_matrix(mesh: dict, thermal_conductivity: float):
    """
    Builds the interior finite-difference Laplacian for wall nodes only.

    The stencil is the standard second-order FD Laplacian scaled by k:
        k * (T_{i+1,j} - 2*T_{i,j} + T_{i-1,j}) / dx²
      + k * (T_{i,j+1} - 2*T_{i,j} + T_{i,j-1}) / dy²

    Returns:
        A          : (N, N) lil_matrix — interior stencil only, NO boundary rows yet
        index_map  : (nx, ny) int array — maps (i,j) → flat DOF index, -1 for channel nodes
    """
    nx, ny        = mesh["nx"], mesh["ny"]
    channel_mask  = mesh["mask"]
    x, y          = mesh["x"], mesh["y"]
    dx            = x[1] - x[0]
    dy            = y[1] - y[0]

    kx = thermal_conductivity / dx**2   # conductance per unit area in x
    ky = thermal_conductivity / dy**2   # conductance per unit area in y

    # ── assign DOF indices to wall nodes ──────────────────────────────────────
    index_map = -np.ones((nx, ny), dtype=int)
    counter   = 0
    for i in range(nx):
        for j in range(ny):
            if channel_mask[i, j]:
                index_map[i, j] = counter
                counter         += 1

    N = counter
    A = lil_matrix((N, N))

    # ── fill interior stencil (wall-to-wall connections only) ─────────────────
    for i in range(nx):
        for j in range(ny):
            if not channel_mask[i, j]:
                continue

            p = index_map[i, j]

            for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                ni, nj = i + di, j + dj
                k_coeff = kx if di != 0 else ky

                # neighbour is inside the domain and is also a wall node
                if 0 <= ni < nx and 0 <= nj < ny and channel_mask[ni, nj]:
                    q          = index_map[ni, nj]
                    A[p, q]   += k_coeff
                    A[p, p]   -= k_coeff
                # all other cases (out-of-bounds or channel neighbour) are
                # handled in the BC assembly step below

    return A, index_map


def _apply_boundary_conditions(
    A: lil_matrix,
    b: np.ndarray,
    mesh: dict,
    index_map: np.ndarray,
    thermal_conductivity: float,
    h_gas: float,
    adiabatic_wall_temperature: float,
    h_coolant: float,
    coolant_temperature: float,
):
    """
    Modifies A and b in-place to impose:

        Bottom edge  (j == 0,      dj == -1)  : Robin — hot gas
        Channel face (wall node adjacent to channel node) : Robin — coolant
        Top edge     (j == ny-1,   dj == +1)  : adiabatic (Neumann, zero flux)
        Left/right   (i == 0/-1,   symmetry)  : adiabatic (Neumann, zero flux)

    The Robin condition for a face of width ds (either dx or dy) is:
        -k * dT/dn = h * (T_wall - T_fluid)
    which, after FD discretisation on a half-cell, gives:
        (k/ds) * T_wall + (h) * T_wall = (k/ds)*T_ghost + h * T_fluid
    → we add  h/ds  to A[p,p]  (because we already have k/ds in the stencil
      from the ghost-cell treatment; here we absorb ds into the Robin term
      directly as the standard finite-volume surface term):

        A[p,p] -= h / ds
        b[p]   -= h / ds * T_fluid

    Sign convention: A * T = b  with the Laplacian written as ∇·(k∇T) = 0,
    so all off-diagonal entries are +k_coeff and diagonal is -Σk_coeff.
    Robin terms ADD a negative contribution to the diagonal and a known RHS term.
    """
    nx, ny = mesh["nx"], mesh["ny"]
    mask   = mesh["mask"]
    x, y   = mesh["x"], mesh["y"]
    dx     = x[1] - x[0]
    dy     = y[1] - y[0]

    for i in range(nx):
        for j in range(ny):
            if not mask[i, j]:
                continue

            p = index_map[i, j]

            for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                ni, nj  = i + di, j + dj
                ds      = dx if di != 0 else dy

                # ── out-of-bounds faces ───────────────────────────────────
                if not (0 <= ni < nx and 0 <= nj < ny):

                    # top edge  → adiabatic, do nothing
                    if dj == 1 and j == ny - 1:
                        pass

                    # bottom edge → hot-gas Robin BC
                    elif dj == -1 and j == 0:
                        A[p, p] -= h_gas / dy
                        b[p]    -= h_gas / dy * adiabatic_wall_temperature

                    # left/right symmetry planes → adiabatic, do nothing
                    elif di != 0:
                        pass

                # ── channel neighbour → coolant Robin BC ─────────────────
                elif not mask[ni, nj]:
                    A[p, p] -= h_coolant / ds
                    b[p]    -= h_coolant / ds * coolant_temperature


def steady_2d_solver(
    mesh: dict,
    thermal_conductivity: float,
    coolant_temperature: float,
    adiabatic_wall_temperature: float,
    h_gas: float,
    h_coolant: float,
) -> tuple[np.ndarray, float, float]:
    """
    Solves the steady 2-D heat conduction problem in the wall cross-section.

    Boundary conditions
    -------------------
    - Bottom edge (hot-gas side)      : Robin  — h_gas,     T_aw
    - Channel-adjacent faces          : Robin  — h_coolant, coolant_temperature
    - Top edge                        : adiabatic (zero normal flux)
    - Left / right edges (symmetry)   : adiabatic (zero normal flux)

    Parameters
    ----------
    mesh                      : dict from generate_mesh()
    thermal_conductivity      : wall thermal conductivity [W/(m·K)]
    coolant_temperature       : bulk coolant temperature [K]
    adiabatic_wall_temperature: recovery / adiabatic wall temperature on hot side [K]
    h_gas                     : hot-gas convective heat transfer coefficient [W/(m²·K)]
    h_coolant                 : coolant convective heat transfer coefficient [W/(m²·K)]

    Returns
    -------
    temperature_field : (nx, ny) array — NaN for channel nodes
    T_hot_wall        : mean temperature of the bottom-edge wall nodes [K]
    T_cold_wall       : mean temperature of wall nodes adjacent to coolant channels [K]
    """
    nx, ny = mesh["nx"], mesh["ny"]
    mask   = mesh["mask"]

    # ── build interior Laplacian ──────────────────────────────────────────────
    A, index_map = _build_laplacian_matrix(mesh, thermal_conductivity)
    N            = index_map.max() + 1
    b            = np.zeros(N)

    # ── apply all boundary conditions in-place ────────────────────────────────
    _apply_boundary_conditions(
        A                       = A,
        b                       = b,
        mesh                    = mesh,
        index_map               = index_map,
        thermal_conductivity    = thermal_conductivity,
        h_gas                   = h_gas,
        adiabatic_wall_temperature = adiabatic_wall_temperature,
        h_coolant               = h_coolant,
        coolant_temperature     = coolant_temperature,
    )

    # ── solve ─────────────────────────────────────────────────────────────────
    temperature_flat = spsolve(A.tocsc(), b)

    # ── reconstruct 2-D temperature field ────────────────────────────────────
    temperature_field = np.full((nx, ny), np.nan)
    for i in range(nx):
        for j in range(ny):
            if index_map[i, j] >= 0:
                temperature_field[i, j] = temperature_flat[index_map[i, j]]

    # ── T_hot_wall : mean of bottom-edge (j=0) wall nodes ────────────────────
    hot_wall_temperatures = [
        temperature_field[i, 0] for i in range(nx) if mask[i, 0]
    ]
    T_hot_wall = float(np.mean(hot_wall_temperatures))

    # ── T_cold_wall : mean of wall nodes that touch a channel face ───────────
    cold_wall_temperatures = []
    for i in range(nx):
        for j in range(ny):
            if not mask[i, j]:
                continue
            for di, dj in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < nx and 0 <= nj < ny and not mask[ni, nj]:
                    cold_wall_temperatures.append(temperature_field[i, j])
                    break   # count each wall node once even if it has two channel faces
    T_cold_wall = float(np.mean(cold_wall_temperatures))

    return temperature_field, T_hot_wall, T_cold_wall


# ── 2D model ───────────────────────────────────────────────────────────────────
def wall_2d(
    state: dict,
    station_index: int,
    cold_side_model: callable,
    hot_side_model: callable,
) -> tuple[float, float, float, list[str]]:
    """
    Outer driver: iterates on T_cold_wall until hot-side and cold-side heat
    fluxes balance, then returns wall temperatures and heat flux.

    The residual is:
        Q_hot(T_hot_wall) - Q_cold(T_cold_wall) = 0

    where T_hot_wall is obtained from steady_2d_solver given h_gas and h_coolant
    evaluated at the current T_cold_wall estimate.
    """
    errors: list[str] = []

    adiabatic_wall_temperature = state["engine_parameters"]["station_T_aw"][station_index]
    coolant_temperature        = state["coolant_parameters"]["station_coolant_T"][-1]

    wall_material  = state["channel_parameters"]["wall_material"]
    wall_thickness = state["channel_parameters"]["wall_thickness"]
    ch             = state["channel_parameters"]["station_ch"][station_index]
    cw             = state["channel_parameters"]["station_cw"][station_index]
    landwidth      = state["channel_parameters"]["station_landwidth"][station_index]

    mesh = generate_mesh(nx=40, ny=40, cw=cw, ch=ch, lw=landwidth, t=wall_thickness)

    def residual(T_cold_wall: float) -> float:
        T_cold_wall = float(T_cold_wall)

        thermal_conductivity, thermal_conductivity_fetch_errors = _wall_thermal_conductivity(
            wall_material, T_cold_wall, station_index
        )
        if thermal_conductivity_fetch_errors:
            errors.extend(thermal_conductivity_fetch_errors)
            return 0.0

        h_coolant, cold_side_model_errors = cold_side_model(state, station_index, T_cold_wall)
        if cold_side_model_errors:
            errors.extend(cold_side_model_errors)
            return 0.0

        # Use h_coolant to get T_hot_wall from a first 2-D solve (h_gas unknown yet),
        # then evaluate h_gas at that T_hot_wall and re-solve once to get a
        # self-consistent pair.  Two inner iterations are cheap and remove the
        # need for the hardcoded +50 K guess that was in the original code.
        h_gas_estimate, hot_side_model_errors = hot_side_model(
            state, station_index, T_cold_wall + 50.0   # rough first guess
        )
        if hot_side_model_errors:
            errors.extend(hot_side_model_errors)
            return 0.0

        _, T_hot_wall, _ = steady_2d_solver(
            mesh                       = mesh,
            thermal_conductivity       = thermal_conductivity,
            coolant_temperature        = coolant_temperature,
            adiabatic_wall_temperature = adiabatic_wall_temperature,
            h_gas                      = h_gas_estimate,
            h_coolant                  = h_coolant,
        )

        # refine h_gas with the actual T_hot_wall from the solve
        h_gas, hot_side_model_errors = hot_side_model(state, station_index, T_hot_wall)
        if hot_side_model_errors:
            errors.extend(hot_side_model_errors)
            return 0.0

        _, T_hot_wall, T_cold_wall_result = steady_2d_solver(
            mesh                       = mesh,
            thermal_conductivity       = thermal_conductivity,
            coolant_temperature        = coolant_temperature,
            adiabatic_wall_temperature = adiabatic_wall_temperature,
            h_gas                      = h_gas,
            h_coolant                  = h_coolant,
        )

        Q_flux_hot  = h_gas     * (adiabatic_wall_temperature - T_hot_wall)
        Q_flux_cold = h_coolant * (T_cold_wall_result         - coolant_temperature)

        return Q_flux_hot - Q_flux_cold

    T_cold_wall_initial    = coolant_temperature
    T_cold_wall_solution, _, ier, msg = fsolve(residual, T_cold_wall_initial, full_output=True)
    T_cold_wall_solution   = float(T_cold_wall_solution[0])

    if ier != 1:
        errors.append(f"Station {station_index}: 2D wall solver did not converge — {msg}")
        return 0.0, 0.0, 0.0, errors

    # ── final solve at converged T_cold_wall ──────────────────────────────────
    thermal_conductivity, thermal_conductivity_fetch_errors = _wall_thermal_conductivity(
        wall_material, T_cold_wall_solution, station_index
    )
    if thermal_conductivity_fetch_errors:
        errors.extend(thermal_conductivity_fetch_errors)
        return 0.0, 0.0, 0.0, errors

    h_coolant, cold_side_model_errors = cold_side_model(state, station_index, T_cold_wall_solution)
    if cold_side_model_errors:
        errors.extend(cold_side_model_errors)
        return 0.0, 0.0, 0.0, errors

    h_gas_estimate, hot_side_model_errors = hot_side_model(
        state, station_index, T_cold_wall_solution + 50.0
    )
    if hot_side_model_errors:
        errors.extend(hot_side_model_errors)
        return 0.0, 0.0, 0.0, errors

    _, T_hot_wall_estimate, _ = steady_2d_solver(
        mesh                       = mesh,
        thermal_conductivity       = thermal_conductivity,
        coolant_temperature        = coolant_temperature,
        adiabatic_wall_temperature = adiabatic_wall_temperature,
        h_gas                      = h_gas_estimate,
        h_coolant                  = h_coolant,
    )

    h_gas, hot_side_model_errors = hot_side_model(state, station_index, T_hot_wall_estimate)
    if hot_side_model_errors:
        errors.extend(hot_side_model_errors)
        return 0.0, 0.0, 0.0, errors

    temperature_field, T_hot_wall, T_cold_wall = steady_2d_solver(
        mesh                       = mesh,
        thermal_conductivity       = thermal_conductivity,
        coolant_temperature        = coolant_temperature,
        adiabatic_wall_temperature = adiabatic_wall_temperature,
        h_gas                      = h_gas,
        h_coolant                  = h_coolant,
    )

    Q_flux = h_gas * (adiabatic_wall_temperature - T_hot_wall)

    return T_hot_wall, T_cold_wall, Q_flux, errors