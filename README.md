# PyRegen-v1.1

Regenerative cooling analysis software for small and medium scale liquid-propellant rocket chambers.

---

## Overview

PyRegen computes the thermal and hydraulic behaviour of a regeneratively cooled rocket engine. Given engine operating conditions, nozzle geometry, coolant properties, and cooling channel geometry, it solves the coupled heat transfer problem station by station along the nozzle wall and produces wall temperatures, heat flux, and coolant state at each station.

---

## Capabilities

- CEA integration for combustion gas properties (temperature, specific heat, Prandtl number, viscosity, gamma, Mach number)
- Nozzle contour generation (conical and bell nozzles, configurable resolution)
- Station-by-station regenerative cooling analysis
- Coolant thermodynamic and transport property lookup
- Cooling channel geometry definition via control points with interpolation
- Heat flux and wall temperature distribution along the nozzle
- Gas-side and coolant-side heat transfer coefficient computation
- Graphical output via DearPyGui: nozzle profile viewer, configurable x/y plots of all computed quantities
- Summary output window with key results

---

## Inputs

**Engine parameters**
- Oxidizer and fuel selection
- Chamber pressure (Pc)
- Mixture ratio (MR)
- Mass flow rate or throat radius (Rt)

**Nozzle parameters**
- Contraction ratio (CR), expansion ratio (ε), characteristic length (L*)
- Nozzle type, length percentage, wall angle, contour resolution

**Coolant parameters**
- Coolant fluid selection
- Mass flow rate, inlet temperature, inlet pressure

**Channel parameters**
- Wall material and thickness
- Number of cooling channels
- Channel width and height control points (position, cw, ch)
- Interpolation type, jacket resolution

---

## Outputs

**Per-station arrays (stored in state)**
- Axial position, local radius, local area ratio
- Gas temperature, adiabatic wall temperature, Mach number, gamma
- Cold wall temperature, hot wall temperature
- Heat flux
- Gas-side and coolant-side heat transfer coefficients
- Coolant temperature, pressure, enthalpy, density, velocity, thermal conductivity
- Coolant Reynolds number, Prandtl number
- Channel width, height, land width, hydraulic diameter, flow area

**Summary results**
- Maximum heat flux (MW/m²)
- Maximum hot wall temperature (K)
- Coolant pressure drop (bar)
- Coolant temperature rise (K)

---

## State Structure

All data is held in a single `state` dictionary with five sections:

```
state
├── engine_parameters
├── nozzle_parameters
├── coolant_parameters
├── channel_parameters
└── results
```

The state is initialised to `None` for all fields via `make_state()` and populated progressively as each analysis stage runs.

---

## Dependencies

- Python 3.10+
- [RocketCEA](https://rocketcea.readthedocs.io/) — CEA wrapper for combustion gas properties
- [CoolProp](http://www.coolprop.org/) — coolant thermodynamic and transport properties
- [DearPyGui](https://github.com/hoffstadt/DearPyGui) — GUI and plotting
- NumPy
- SciPy — interpolation of channel geometry control points

---

## Project Structure

```
pyregen/
├── main.py                 # Entry point, DPG event loop
├── interface.py            # GUI layout and callbacks
├── output.py               # Graph and text output functions
├── state.py                # make_state(), state management
├── engine.py               # CEA calls, gas property computation
├── nozzle.py               # Nozzle contour generation
├── cooling.py              # Station-by-station cooling solver
└── channels.py             # Channel geometry interpolation
```

---

## Usage

```bash
python main.py
```

1. Set engine parameters and run CEA
2. Define nozzle geometry and generate contour
3. Set coolant and channel parameters
4. Run the solver
5. Use the Output section to generate graphs or view the summary window

