"""Dryer DRY 2.1: TSA/PSA with two alternating cartridges.

Electrical loss: two datasheet numbers exist and disagree in interpretation:
  200 W 'operative' (upper envelope) vs 0.045 kWh/Nm3 (flow-proportional, 112 W
  at rated flow). We report BOTH and flag that the dryer must be metered.
Gas loss: regeneration blows down the off-line cartridge; the vented H2 is
  bounded above by the device hold-up (47 NL) per regeneration. Unmeasured
  frequency -> modelled as a GUESS fraction of throughput.
"""
from .. import registry as R
from ..conversions import NL_to_kg, kg_to_kWh_LHV

class Dryer:
    def account(self, duration_h, throughput_NL, measured_kWh=None):
        e_env = R.get("dry.power_operative_W") / 1000.0 * duration_h
        e_spec = R.get("dry.spec_energy_kWh_Nm3") * throughput_NL / 1000.0
        e = measured_kWh if measured_kWh is not None else e_env
        vent_NL = throughput_NL * R.get("dry.vent_fraction")
        return dict(unit="DRY", energy_kWh=e,
                    energy_kWh_envelope_200W=e_env, energy_kWh_spec_0p045=e_spec,
                    energy_is_measured=measured_kWh is not None,
                    gas_loss_NL=vent_NL, gas_loss_kWh_LHV=kg_to_kWh_LHV(NL_to_kg(vent_NL)),
                    gas_loss_uncertainty_rel=R.entry("dry.vent_fraction")["uncertainty"],
                    warning="dryer electrical energy is an envelope, not measured; "
                            "vent fraction is a GUESS bounded only by tank-pV vs Faraday residual")
