"""One module per physical device, sorted in ENERGY-FLOW ORDER.

Read the filenames top to bottom and you are reading the energy path of the
island system. The deep explanation (what is measured vs assumed, which
formula, which uncertainty) lives in each file's docstring.

    pv_measured.py         PV array, DC side (legacy array telemetry)        measured
    pv_prelim_channel.py   preliminary PV loss channel ("vorerst")        PRELIM
    pv_inverter.py         PV-side inverter, PV DC -> AC bus              measured / PRELIM
    electrolyzer.py        electrolyser unit (Enapter EL 2.1 + PSU)       AC -> H2
    booster.py             air-driven gas booster (Maximator DLE 30-2)    H2 35 -> 200 bar
    dryer.py               H2 dryer (Enapter DRY 2.1)                     gas + electrical
    tank.py                storage tank (VITKOVICE 800 L)                 pV state, Route 2
    fuel_cell.py           fuel cell system (2x IE-LIFT 802)              H2 -> DC
    inverter.py            FC-side inverter, 48-52 V bus -> AC island     PRELIM / measured

The two inverters are separate files on purpose (different devices, different
DC voltage classes, separately analysable); inverter.py = FC side, pv_inverter.py
= PV side, names chosen so alphabetical order never mixes them.

Each account() answers the same three questions for a time window: energy in?
energy/hydrogen out? what was lost, and how sure are we? Every returned dict
carries 'unit', energies in kWh, and explicit measured-vs-assumed flags.
"""
from ._common import t_seconds  # noqa: F401
from .pv_measured import PVSystem
from .pv_prelim_channel import pv_account, cell_temperature
from .pv_inverter import PVInverter
from .electrolyzer import ElectrolyzerUnit
from .booster import AirDrivenBooster
from .dryer import Dryer
from .water_system import WaterSystem
from .tank import Tank
from .fuel_cell import FuelCellSystem
from .inverter import FCInverter
