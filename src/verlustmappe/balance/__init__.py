"""Energy bookkeeping across devices and operating modes, numbered in
accounting order: label the modes, find steady segments, detect events,
build the loss map, compute RTE.

  a_modes.py      label every sample: standby / startup / steady / event
  b_segments.py   find steady-state windows (for characteristic curves)
  c_events.py     robust event detection (median/MAD) + purge candidates
  d_loss_map.py   the loss map: all devices in a row, H2 balance, RTE
  e_rte.py        round-trip efficiency at two system boundaries
  _event_core.py  validated median/MAD detector core (user's original module)
"""
from .a_modes import partition_modes, energy_by_mode
from .b_segments import steady_segments
from .c_events import detect_events, purge_candidates
from .d_loss_map import loss_map
from .e_rte import storage_chain_rte, island_rte
