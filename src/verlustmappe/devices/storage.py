"""Storage tank: mass in the tank from p, V, T and Z (real gas)."""
from .. import registry as R
from ..physics import constants as C
from ..physics.conversions import mol_from_pVT, mol_to_kg, mol_to_NL, kg_to_kWh_LHV
from ..hydrogen.z_realgas import z_h2
from ..hydrogen.temperature_model import assumed_temperature_standard_uncertainty_K

class Tank:
    def stored(self, p_barg, T_C=None, *, analyze_temperature_uncertainty=False):
        """Model state at defined temperature; optional band analysis, no Pt100 path."""
        temperature_is_assumed = T_C is None
        if temperature_is_assumed:
            T_C = R.get("stor.T_assumed_C")
        p = p_barg + C.P_ATM_BAR
        mol = mol_from_pVT(p, R.get("stor.volume_L") / 1000.0, T_C + 273.15, z_h2(p, T_C))
        kg = mol_to_kg(mol)
        analyze_assumption = analyze_temperature_uncertainty and temperature_is_assumed
        u_temperature_K = assumed_temperature_standard_uncertainty_K() if analyze_assumption else None
        u_temperature_rel = u_temperature_K / (T_C + 273.15) if analyze_assumption else None
        return dict(p_barg=p_barg, Z=z_h2(p, T_C), mol=mol, kg=kg, NL=mol_to_NL(mol),
                    kWh_LHV=kg_to_kWh_LHV(kg), T_used_C=T_C,
                    temperature_is_assumed=temperature_is_assumed,
                    temperature_source=R.entry("stor.T_assumed_C")["source"]
                    if temperature_is_assumed else "explicitly supplied; not automatically measured",
                    temperature_status="GUESS" if temperature_is_assumed else None,
                    origin="computed",
                    temperature_uncertainty_analysis_requested=analyze_temperature_uncertainty,
                    temperature_standard_uncertainty_K=u_temperature_K,
                    temperature_uncertainty_rel=u_temperature_rel,
                    temperature_mass_standard_uncertainty_kg=kg * u_temperature_rel
                    if analyze_assumption else None,
                    temperature_uncertainty_note=(
                        "optional temperature contribution only, fixed-Z first-order u_T/T; "
                        "not total mass uncertainty or measurement validation"
                        if analyze_assumption else
                        "defined model temperature; no +/-10 K band analysis performed"))
