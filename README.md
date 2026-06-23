# PyRegen v1.1

**Regenerative cooling analysis software for small and medium scale liquid-propellant rocket chambers and nozzles.**

PyRegen computes the thermal and hydraulic behaviour of a regeneratively cooled rocket engine. Given engine operating conditions, nozzle geometry, coolant properties, and cooling channel geometry, it solves the coupled heat transfer problem station by station along the nozzle wall, producing wall temperatures, heat flux, and coolant state at each station.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [State Structure](#state-structure)
- [License](#license)

---

## Features

- CEA integration for combustion gas properties (temperature, specific heat ratio, Prandtl number, viscosity, Mach number)
- Conical and bell nozzle contour generation with configurable resolution
- Station-by-station regenerative cooling solver
- Coolant thermodynamic and transport property lookup via CoolProp
- Cooling channel geometry defined via control points with linear or cubic spline interpolation
- Gas-side and coolant-side heat transfer coefficient computation
- Heat flux and wall temperature distribution along the nozzle
- Interactive GUI with DearPyGui: nozzle profile viewer, configurable x/y plots of all computed quantities, and a summary results window

---

## Project Structure

```
PyRegen-v1.1/
├── Source Code/
│   ├── assets/                  # Static assets (images, icons, fonts)
│   ├── main.py                  # Entry point, DearPyGui event loop
│   ├── interface.py             # GUI layout and user callbacks
│   ├── inputprocessor.py        # Input validation and preprocessing
│   ├── output.py                # Graph and text output functions
│   ├── state.py                 # State initialisation and management
│   ├── data.py                  # Data storage and retrieval
│   ├── models.py                # Heat transfer and fluid models
│   ├── geometry.py              # Nozzle contour and channel geometry
│   ├── cea.py                   # CEA calls and gas property computation
│   └── solver.py                # Station-by-station cooling solver
├── .gitignore
├── LICENSE
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| [RocketCEA](https://rocketcea.readthedocs.io/) | CEA wrapper for combustion gas properties |
| [CoolProp](http://www.coolprop.org/) | Coolant thermodynamic and transport properties |
| [DearPyGui](https://github.com/hoffstadt/DearPyGui) | GUI and plotting |
| NumPy | Numerical arrays |
| SciPy | Channel geometry control point interpolation |

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/creatorandrew86/PyRegen-v1.1.git
   cd PyRegen-v1.1
   ```

2. Install dependencies:
   ```bash
   pip install rocketcea coolprop dearpygui numpy scipy
   ```

> **Note:** RocketCEA requires NASA CEA to be installed separately. See the [RocketCEA documentation](https://rocketcea.readthedocs.io/en/latest/installCEA.html) for instructions.

---

## Usage

```bash
cd "Source Code"
python main.py
```

Once the GUI opens, follow these steps:

1. Set **engine parameters** and run CEA to compute combustion gas properties
2. Define **nozzle geometry** and generate the contour
3. Set **coolant** and **channel parameters**
4. Run the **solver**
5. Use the **Output** section to generate plots or view the summary results window

---

## Inputs

### Engine Parameters
- Oxidizer and fuel selection
- Chamber pressure (Pc)
- Mixture ratio (MR)
- Mass flow rate or throat radius (Rt)

### Nozzle Parameters
- Contraction ratio (CR), expansion ratio (ε), characteristic length (L*)
- Nozzle type (conical / bell), length percentage, wall angle, contour resolution

### Coolant Parameters
- Coolant fluid selection
- Mass flow rate, inlet temperature, inlet pressure

### Channel Parameters
- Wall material and thickness
- Number of cooling channels
- Channel width and height control points (axial position, `cw`, `ch`)
- Interpolation type (linear / cubic spline), jacket resolution

---

## Outputs

### Per-Station Arrays
| Quantity | Description |
|---|---|
| Axial position, radius, area ratio | Nozzle geometry at each station |
| Gas temperature, adiabatic wall temperature | Hot-gas thermal conditions |
| Mach number, gamma | Flow properties |
| Cold wall temp, hot wall temp | Wall thermal state |
| Heat flux | Local heat flux (W/m²) |
| Gas-side HTC, coolant-side HTC | Heat transfer coefficients |
| Coolant temperature, pressure, enthalpy | Coolant thermodynamic state |
| Coolant density, velocity, thermal conductivity | Coolant transport properties |
| Reynolds number, Prandtl number | Coolant flow regime |
| Channel width, height, land width, hydraulic diameter, flow area | Channel geometry |

### Summary Results
- Maximum heat flux (MW/m²)
- Maximum hot wall temperature (K)
- Coolant pressure drop (bar)
- Coolant temperature rise (K)

---

## State Structure

All data is held in a single `state` dictionary, initialised via `make_state()` and populated progressively as each analysis stage runs:

```
state
├── engine_parameters
├── nozzle_parameters
├── coolant_parameters
├── channel_parameters
└── results
```

---

## License

This project is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.