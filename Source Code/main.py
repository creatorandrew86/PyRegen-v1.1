import interface.interface as interface

from core.inputprocessor import process_inputs_on_generate, process_inputs_on_solve
from core.geometry import generate_nozzle_contour
from core.output import initialize_main_output
from physics.solver import run_solver
from core.cea import run_cea

from core.state import make_state 
state = make_state()

def on_generate_nozzle():
    # Get inputs from interface
    raw_engine_params = interface.get_engine_parameters()
    raw_nozzle_params = interface.get_nozzle_parameters()


    # Run the input processor and update state
    clean_params, input_errors = process_inputs_on_generate(raw_engine_params, raw_nozzle_params)
    if input_errors:
        interface.show_errors(input_errors)
        return
    
    state["engine_parameters"].update(clean_params["engine_parameters"])
    state["nozzle_parameters"].update(clean_params["nozzle_parameters"])


    # Run CEA 
    cea_errors = run_cea(state)
    if cea_errors:
        interface.show_errors(cea_errors)
    

    # Run Geometry
    geometry_errors = generate_nozzle_contour(state)
    if geometry_errors:
        interface.show_errors(geometry_errors)
        return

    # Upload the nozzle to the interface
    interface.update_nozzle_canvas(state)


def on_solve():
    # Check if the nozzle generator ran
    if state["nozzle_parameters"]["x"] is None:
        interface.show_errors(["The nozzle must be generated before running PyRegen."])
        return
    
    # Get inputs from interface
    raw_coolant_params = interface.get_coolant_parameters()
    raw_channel_params = interface.get_channel_parameters()
    raw_solver_options = interface.get_solver_options()
    control_points = interface.get_control_points()


    # Run the input processor and update state
    clean_params, input_errors = process_inputs_on_solve(raw_coolant_params, raw_channel_params, raw_solver_options, control_points, state)
    if input_errors:
        interface.show_errors(input_errors)
        return
    
    state["engine_parameters"]["N_injectors"] = clean_params["solver_options"].pop("N_injectors", None)
    state["engine_parameters"]["injector_velocity_ratio"] = clean_params["solver_options"].pop("injector_velocity_ratio", None)

    state["coolant_parameters"].update(clean_params["coolant_parameters"])
    state["channel_parameters"].update(clean_params["channel_parameters"])
    state["solver_options"].update(clean_params["solver_options"])


    initialize_main_output()

    # Run the solver 
    solver_errors = run_solver(state)
    if solver_errors:
        interface.show_errors(solver_errors)
        return

interface.run_interface(on_generate_nozzle, on_solve, state)