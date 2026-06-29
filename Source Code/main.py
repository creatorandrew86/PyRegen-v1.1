import interface.interface as ui

from core.input import inputs_on_generate, inputs_on_solve
from core.geometry import generate_nozzle_contour
from physics.solver import run_solver
from core.cea import run_cea

from core.state import make_state 
state = make_state()

def on_generate_nozzle():
    # Get inputs from interface
    input_errors = inputs_on_generate(state)
    if input_errors:
        ui.show_errors(input_errors)
        return


    # Run CEA 
    cea_errors = run_cea(state)
    if cea_errors:
        ui.show_errors(cea_errors)
        return
    

    # Run Geometry
    geometry_errors = generate_nozzle_contour(state)
    if geometry_errors:
        ui.show_errors(geometry_errors)
        return

    # Upload the nozzle to the interface
    ui.update_nozzle_canvas(state)


def on_solve():
    # Check if the nozzle generator ran
    if state["nozzle_parameters"]["x"] is None:
        ui.show_errors(["The nozzle must be generated before running PyRegen."])
        return
    
    input_errors = inputs_on_solve(state)
    if input_errors:
        ui.show_errors(input_errors)
        return

    # Run the solver 
    solver_errors = run_solver(state)
    if solver_errors:
        ui.show_errors(solver_errors)
        return


if __name__ == "__main__":
    ui.run_interface(on_generate_nozzle, on_solve, state)