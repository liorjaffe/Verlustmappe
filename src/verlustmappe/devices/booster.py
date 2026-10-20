"""Air-driven gas booster (Maximator DLE 30-2).

The booster itself consumes no electricity; it consumes COMPRESSED AIR made by
an electric air compressor (Kaeser). The electrical loss of the compression
stage is therefore the air compressor's energy while the booster runs.

  W_ideal = n R T ln(p2/p1)          minimum work (isothermal, IDEAL gas)
  eta_overall = W_ideal / E_air_compressor
Real-gas note: for H2 at 35->200 bar the ideal formula underestimates the true
work by ~5-8% (Z > 1). That error is inside the eta_overall GUESS band and is
documented here rather than corrected, because the GUESS dominates by an order
of magnitude. If the booster is ever metered, switch W to the real-gas form
(integral V dp with Z(p,T)).
Anchor for eta_overall (verified against the full text, 2026-10): Bovo, Poli,
Trovo, Marini, Guarnieri, IJHE 48 (2023) part 1, DOI 10.1016/j.ijhydene.2022.11.346,
Tab. 3: 78.4 kWh compression + 4.6 kWh auxiliaries for 33.22 Nm3, tank 40->200
bar. Correct fill-integral ideal work: 1.0-1.3 kWh (suction 40 vs 35 bar) ->
overall 1.2-1.6%; registered 0.014 +-30%. (Their eta_CSU = 54.5% is H2 energy
/ (H2 + compression electricity), a different quantity. The earlier "56-100
kWh consumed" reading was a mix-up with the purifier energy and is withdrawn.)
Until E_air_compressor is metered, E is estimated as W_ideal / eta_GUESS.
"""
from .. import registry as R
from .. import constants as C
from ..conversions import isothermal_work_kWh, NL_to_mol
from ..hydrogen.temperature_model import isothermal_work_mol_integral

class AirDrivenBooster:
    def account(self, throughput_NL, p_in_barg, p_out_barg, T_C=20.0, air_compressor_kWh=None,
                p_tank_start_barg=None, p_tank_end_barg=None):
        """Compressor work for moving throughput_NL of gas into storage.

        Since 2026-10 the ideal work uses the mole-weighted integral over the
        tank fill path (isothermal_work_mol_integral): the old single-shot
        formula nRT ln(p2/p1) applied at the arithmetic mean pressure overstated
        a 20->200 bar fill by ~21% and understated 100->200 bar by ~16%.
        Pass p_tank_start_barg / p_tank_end_barg (the storage window) and the
        integral runs against the suction pressure p_in_barg (EL output).
        Without a window the single-shot form at (p_in -> p_out) is kept, which
        is the correct assumption when all gas is compressed at once."""
        mol = NL_to_mol(throughput_NL)
        p_in_abs = p_in_barg + C.P_ATM_BAR
        p_out_abs = p_out_barg + C.P_ATM_BAR
        if p_tank_start_barg is not None and p_tank_end_barg is not None:
            w_ideal = isothermal_work_mol_integral(
                mol, p_tank_start_barg + C.P_ATM_BAR, p_tank_end_barg + C.P_ATM_BAR,
                T_C + 273.15, p_suction_abs_bar=p_in_abs)
            # consistency: if the throughput EXCEEDS what the tank window holds,
            # the surplus arrives before the window opens (or after it closes);
            # the honest floor is the work of the window mass itself.
            from ..conversions import mol_from_pVT
            from ..hydrogen.z_realgas import z_h2 as _z
            p1a, p2a = p_tank_start_barg + C.P_ATM_BAR, p_tank_end_barg + C.P_ATM_BAR
            mol_window = (mol_from_pVT(p2a, R.get("stor.volume_L") / 1000.0,
                                       T_C + 273.15, _z(p2a, T_C))
                          - mol_from_pVT(p1a, R.get("stor.volume_L") / 1000.0,
                                         T_C + 273.15, _z(p1a, T_C)))
            if mol > mol_window > 0:
                w_ideal = isothermal_work_mol_integral(
                    mol_window, p1a, p2a, T_C + 273.15, p_suction_abs_bar=p_in_abs)
                mol = mol_window
                throughput_NL = mol_window * C.V_MOL_NL_PER_MOL
        elif p_out_abs > p_in_abs:
            w_ideal = isothermal_work_mol_integral(mol, p_in_abs, p_out_abs, T_C + 273.15)
        else:
            w_ideal = 0.0   # storage below suction pressure: no compression needed
        if air_compressor_kWh is not None:
            return dict(unit="CSU", ideal_work_kWh=w_ideal, energy_kWh=air_compressor_kWh,
                        overall_efficiency=w_ideal / air_compressor_kWh if air_compressor_kWh else None,
                        energy_is_measured=True, warning=None)
        eta = R.get("comp.overall_efficiency")
        return dict(unit="CSU", ideal_work_kWh=w_ideal, energy_kWh=w_ideal / eta,
                    overall_efficiency=eta, energy_is_measured=False,
                    uncertainty_rel=R.entry("comp.overall_efficiency")["uncertainty"],
                    warning="compression energy = ideal work / GUESS efficiency (+-50%); meter the Kaeser")
