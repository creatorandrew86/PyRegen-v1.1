import inputprocessor
import interface
import geometry
import solver
import output
import cea

import state as module_state
state = module_state.make_state()

def on_generate_nozzle():
    # Get inputs from interface
    raw_engine_params = interface.get_engine_parameters()
    raw_nozzle_params = interface.get_nozzle_parameters()


    # Run the input processor and update state
    clean_params, input_errors = inputprocessor.process_inputs_on_generate(raw_engine_params, raw_nozzle_params)
    if input_errors:
        print(f"Input Errors: {input_errors}")
        interface.show_errors(input_errors)
        return
    
    state["engine_parameters"].update(clean_params["engine_parameters"])
    state["nozzle_parameters"].update(clean_params["nozzle_parameters"])


    # Run CEA with SI units
    cea_errors = cea.run_cea_SI_units(state)
    if cea_errors:
        print(f"CEA Errors: {cea_errors}")
        interface.show_errors(cea_errors)
        return 
    

    # Run CEA with default units
    cea_errors = cea.run_cea_default_units(state)
    if cea_errors:
        print(f"CEA Errors: {cea_errors}")
        interface.show_errors(cea_errors)
        return
    

    # Run Geometry
    geometry_errors = geometry.run_geometry(state)
    if geometry_errors:
        print(f"Geometry Function Errors: {geometry_errors}")
        interface.show_errors(geometry_errors)
        return

    # Upload the nozzle to the interface
    interface.update_nozzle_canvas(state)


def on_solve():
    # Check if the nozzle generator ran
    if state["nozzle_parameters"]["x"] is None:
        print("The nozzle must be generated before running PyRegen.")
        interface.show_errors(["The nozzle must be generated before running PyRegen."])
        return 
    
    # Get inputs from interface
    raw_coolant_params = interface.get_coolant_parameters()
    raw_channel_params = interface.get_channel_parameters()
    control_points = interface.get_control_points()


    # Run the input processor and update state
    clean_params, input_errors = inputprocessor.process_inputs_on_confirm_channel_geometry(raw_coolant_params, raw_channel_params, control_points, state)
    if input_errors:
        print(f"Input Errors: {input_errors}")
        interface.show_errors(input_errors)
        return

    state["coolant_parameters"].update(clean_params["coolant_parameters"])
    state["channel_parameters"].update(clean_params["channel_parameters"])


    # Run the solver 
    solver_errors = solver.run_solver(state)
    if solver_errors:
        print(f"Solver Errors: {solver_errors}")
        interface.show_errors(solver_errors)
        return
    
    output.print_main_output(state)

interface.run_interface(on_generate_nozzle, on_solve, state)