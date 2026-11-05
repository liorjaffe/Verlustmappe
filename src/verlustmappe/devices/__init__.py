"""One module per physical device, sorted in ENERGY-FLOW ORDER.

Read the filenames top to bottom and you are reading the energy path of the
island system. The deep explanation (what is measured vs assumed, which
formula, which uncertainty) lives in each file's docstring.

    pv_array.py      PV array F8: preliminary loss channel and measured mode     PRELIM / measured
    pv_inverter.py   PV-side inverter, PV DC -> AC bus                            measured / PRELIM
    el.py            electrolyser unit (Enapter EL 2.1 + PSU)                     AC -> H2
    dryer.py         H2 dryer (Enapter DRY 2.1)                                   gas + electrical
    water.py         water system: RO unit and filter train with pump             electrical + water
    booster.py       air-driven gas booster (HULC, see plant/booster.toml)        H2 35 -> storage
    storage.py       storage tank (VITKOVICE 800 L)                               pV state, Route 2
    fc.py            fuel cell system (2x IE-LIFT 802)                            H2 -> DC
    fc_inverter.py   FC-side inverter, 48-52 V bus -> AC island                   PRELIM / measured

Every module has the same name as its parameter file plant/<device>.toml. The two inverters
are separate devices (different DC voltage classes): pv_inverter = PV side, fc_inverter = FC side.

Each account() answers the same three questions for a time window: energy in?
energy/hydrogen out? what was lost, and how sure are we? Every returned dict
carries 'unit', energies in kWh, and explicit measured-vs-assumed flags.
"""
from ._common import t_seconds  # noqa: F401
from .pv_array import pv_account, cell_temperature, PVSystem
from .pv_inverter import PVInverter
from .el import ElectrolyzerUnit
from .dryer import Dryer
from .booster import AirDrivenBooster
from .water import WaterSystem
from .storage import Tank
from .fc import FuelCellSystem
from .fc_inverter import FCInverter
