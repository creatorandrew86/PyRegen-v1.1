import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from pathlib import Path

from rocketcea.cea_obj import CEA_Obj as CEA_Obj_default_units


def _ask_save_path(default_filename: str) -> Path | None:
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    root.update()

    path = filedialog.asksaveasfilename(
        parent=root,
        defaultextension=".txt",
        initialfile=default_filename,
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Save Output As",
    )

    root.destroy()
    return Path(path) if path else None


def write_full_cea_output(state: dict) -> list[str]:
    errors = []

    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        errors.append("PyRegen must run before attempting to print any output")
        return errors

    # ── Unpack ───────────────────────────────────────────────────────────
    Pc              = state["engine_parameters"]["Pc"]
    Pc_psia         = Pc / 6894.7
    MR              = state["engine_parameters"]["MR"]
    eps             = state["nozzle_parameters"]["eps"]
    c_default_units : CEA_Obj_default_units = state["engine_parameters"]["CEA_Obj_default_units"]

    full_cea_output = c_default_units.get_full_cea_output(Pc=Pc_psia, MR=MR, eps=eps, output='siunits')

    # ── Save ─────────────────────────────────────────────────────────────
    path = _ask_save_path("CEA Output.txt")
    if path is None:
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(full_cea_output)

    print(f"CEA output written to {path}")

    return errors


def write_full_pyregen_output(state: dict) -> list[str]:
    errors = []

    # Check if PyRegen ran
    if state["results"]["Q_flux"] is None:
        errors.append("PyRegen must run before attempting to print any output")
        return errors

    # ── Unpack engine ────────────────────────────────────────────────────
    oxidizer        = state["engine_parameters"]["oxidizer"]
    fuel            = state["engine_parameters"]["fuel"]
    Pc              = state["engine_parameters"]["Pc"]
    MR              = state["engine_parameters"]["MR"]
    Tc              = state["engine_parameters"]["Tc"]
    Isp             = state["engine_parameters"]["Isp"]
    Ivac            = state["engine_parameters"]["Ivac"]
    C_star          = state["engine_parameters"]["C_star"]
    Rt              = state["engine_parameters"]["Rt"]
    At              = state["nozzle_parameters"]["At"]
    eps             = state["nozzle_parameters"]["eps"]
    CR              = state["nozzle_parameters"]["CR"]
    mass_flow_rate  = state["engine_parameters"]["mass_flow_rate"]
    chamber_Cp      = state["engine_parameters"]["chamber_Cp"]
    chamber_Pr      = state["engine_parameters"]["chamber_Pr"]

    coolant         = state["coolant_parameters"]["coolant"]
    coolant_mfr     = state["coolant_parameters"]["coolant_mass_flow_rate"]
    coolant_T_in    = state["coolant_parameters"]["coolant_inlet_temperature"]
    coolant_p_in    = state["coolant_parameters"]["coolant_inlet_pressure"]
    coolant_T_out   = state["coolant_parameters"]["station_coolant_T"][-1]
    coolant_p_out   = state["coolant_parameters"]["station_coolant_p"][-1]

    wall_material   = state["channel_parameters"]["wall_material"]
    wall_thickness  = state["channel_parameters"]["wall_thickness"]
    N_channels      = state["channel_parameters"]["N_cooling_channels"]

    ctrl_positions      = state["channel_parameters"]["control_points_position"]
    ctrl_cw             = state["channel_parameters"]["control_points_cw"]
    ctrl_ch             = state["channel_parameters"]["control_points_ch"]

    station_x       = state["nozzle_parameters"]["station_x"]
    station_cw      = state["channel_parameters"]["station_cw"]
    station_ch      = state["channel_parameters"]["station_ch"]
    station_lw      = state["channel_parameters"]["station_landwidth"]

    station_Re      = state["coolant_parameters"]["station_coolant_Re"]
    station_vel     = state["coolant_parameters"]["station_coolant_velocity"]
    station_T_cool  = state["coolant_parameters"]["station_coolant_T"][:-1]
    station_p_cool  = state["coolant_parameters"]["station_coolant_p"][:-1]

    station_T_cold  = state["results"]["T_cold_wall"]
    station_T_hot   = state["results"]["T_hot_wall"]
    station_Q       = state["results"]["Q_flux"]
    station_hl      = state["results"]["h_coolant"]
    station_hg      = state["results"]["h_gas"]

    pressure_drop_model = state["solver_options"]["pressure_drop_model"]
    cold_side_model     = state["solver_options"]["cold_side_model"]
    hot_side_model      = state["solver_options"]["hot_side_model"]
    wall_model          = state["solver_options"]["wall_model"]

    n = len(station_x)


    # ── Save ─────────────────────────────────────────────────────────────
    path = _ask_save_path(f"Full Output.txt")
    if path is None:
        return

    # ── Column widths ────────────────────────────────────────────────────
    C1_width = 22
    C2_width = 36
    C3_width = 44
    C4_width = 62
    total_width  = C1_width + C2_width + C3_width + C4_width + 5

    def row(c1, c2, c3, c4):
        return f"│{c1:<{C1_width}}│{c2:<{C2_width}}│{c3:<{C3_width}}│{c4:<{C4_width}}│"

    with open(path, "w", encoding="utf-8") as f:

        f.write("=" * total_width + "\n")
        f.write(f"  PyRegen — Full Solver Output\n")
        f.write(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * total_width + "\n\n")

        f.write("── Engine Definition " + "─" * (total_width - 21) + "\n\n")
        f.write(f"  {'Oxidizer:':<28} {oxidizer}\n")
        f.write(f"  {'Fuel:':<28} {fuel}\n")
        f.write(f"  {'Chamber Pressure:':<28} {Pc/1e5:.2f} bar\n")
        f.write(f"  {'Mixture Ratio (O/F):':<28} {MR:.2f}\n")
        f.write(f"  {'Combustion Temperature:':<28} {Tc:.2f} K\n")
        f.write(f"  {'Characteristic Velocity:':<28} {C_star:.2f} m/s\n")
        f.write(f"  {'Specific Impulse:':<28} {Isp:.2f} s\n")
        f.write(f"  {'Vacuum Specific Impulse:':<28} {Ivac:.2f} s\n")
        f.write(f"  {'Throat Radius:':<28} {Rt*100:.2f} cm\n")
        f.write(f"  {'Throat Area:':<28} {At*1e4:.3f} cm²\n")
        f.write(f"  {'Expansion Ratio:':<28} {eps:.2f}\n")
        f.write(f"  {'Contraction Ratio:':<28} {CR:.2f}\n")
        f.write(f"  {'Mass Flow Rate:':<28} {mass_flow_rate:.2f} kg/s\n")
        f.write(f"  {'Gas Specific Heat (frozen):':<28} {chamber_Cp:.2f} J/(kg·K)\n")
        f.write(f"  {'Pr Number (frozen):':<28} {chamber_Pr:.4f}\n")
        f.write("\n\n")

        f.write("── Jacket Definition " + "─" * (total_width - 21) + "\n\n")
        f.write(f"  {'Coolant:':<28} {coolant}\n")
        f.write(f"  {'Coolant Mass Flow Rate:':<28} {coolant_mfr:.2f} kg/s\n")
        f.write(f"  {'Inlet Temperature:':<28} {coolant_T_in:.2f} K\n")
        f.write(f"  {'Inlet Pressure:':<28} {coolant_p_in/1e5:.2f} bar\n")
        f.write(f"  {'Outlet Temperature:':<28} {coolant_T_out:.2f} K\n")
        f.write(f"  {'Outlet Pressure:':<28} {coolant_p_out/1e5:.2f} bar\n")
        f.write(f"  {'Pressure Drop:':<28} {(coolant_p_in - coolant_p_out)/1e5:.2f} bar\n")
        f.write(f"  {'Temperature Rise:':<28} {coolant_T_out - coolant_T_in:.2f} K\n")
        f.write(f"  {'Wall Material:':<28} {wall_material}\n")
        f.write(f"  {'Wall Thickness:':<28} {wall_thickness*1000:.2f} mm\n")
        f.write(f"  {'Number of Channels:':<28} {N_channels}\n\n")

        f.write(f"\n  Control Points:\n")
        f.write(f"    {'#':>4}  {'x[cm]':>10}    {'cw[mm]':>10}    {'ch[mm]':>10}\n")
        for i, (xp, cw, ch) in enumerate(zip(ctrl_positions, ctrl_cw, ctrl_ch)):
            f.write(f"    {i+1:>4}   {xp*100:>10.3f}   {cw*1000:>10.3f}   {ch*1000:>10.3f}\n")
        f.write("\n\n")

        f.write("── Solver Options " + "─" * (total_width - 21) + "\n\n")
        f.write(f"  {'Pressure Drop Model:':<28} {pressure_drop_model}\n")
        f.write(f"  {'Cold Side Model:':<28} {cold_side_model}\n")
        f.write(f"  {'Hot Side Model:':<28} {hot_side_model}\n")
        f.write(f"  {'Wall Model:':<28} {wall_model}\n")
        f.write("\n\n")

        f.write("── Station Data " + "\n")

        f.write("─" * (total_width - 21) + "\n")
        f.write(row(
            " Station / Position",
            " Channel Geometry",
            " Coolant Properties",
            " Thermal Properties",
        ) + "\n")

        f.write("─" * (total_width - 21) + "\n")
        f.write(row(
            "    #      x[cm]",
            "   cw[mm]    ch[mm]     lw[mm]",
            "       Re     v[m/s]     T[K]    p[bar]",
            "   T_cw[K]    T_hw[K]   Q[MW/m²]  hl[kW/m²]   hg[kW/m²]",
        ) + "\n")

        f.write("─" * (total_width - 21) + "\n")
        for i in range(n):
            c1 = f"  {i:>4d}   {station_x[i]*100:>7.2f}"
            c2 = (
                f"  {station_cw[i]*1000:>6.3f}"
                f"     {station_ch[i]*1000:>6.3f}"
                f"     {station_lw[i]*1000:>6.3f}"
            )
            c3 = (
                f"  {station_Re[i]:>9.0f}"
                f"  {station_vel[i]:>7.3f}"
                f"  {station_T_cool[i]:>8.2f}"
                f"  {station_p_cool[i]/1e5:>7.2f}"
            )
            c4 = (
                f"  {station_T_cold[i]:>8.2f}"
                f"  {station_T_hot[i]:>8.2f}"
                f"  {station_Q[i]/1e6:>8.2f}"
                f"  {station_hl[i]/1e3:>9.2f}"
                f"  {station_hg[i]/1e3:>9.2f}"
            )
            f.write(row(c1, c2, c3, c4) + "\n")

        f.write("─" * (total_width - 21) + "\n")

    print(f"Full PyRegen output written to {path}")

    return errors