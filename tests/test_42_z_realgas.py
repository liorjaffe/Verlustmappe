"""Real-gas Z of hydrogen (hydrogen/z_realgas.py). Checkpoints and tolerances copied
verbatim from legacy test_02 (CoolProp / Leachman EOS values, not computed here)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from verlustmappe.physics.constants import M_H2_KG_PER_MOL, R_J_PER_MOL_K
from verlustmappe.hydrogen.z_realgas import z_h2


def test_z_checkpoints():
    assert abs(z_h2(350.0, 20.0) - 1.227) < 0.002
    assert abs(z_h2(200.0, 20.0) - 1.125) < 0.002
    assert abs(z_h2(1.013, 20.0) - 1.0) < 0.002


def test_density_at_200_bar_20_C():
    # Leachman EOS: about 14.7 kg/m3 at 200 bar absolute, 20 C (legacy test_02 band)
    pressure_Pa = 200.0e5
    temperature_K = 293.15
    density_kg_m3 = pressure_Pa * M_H2_KG_PER_MOL / (
        z_h2(200.0, 20.0) * R_J_PER_MOL_K * temperature_K)
    assert 14.6 < density_kg_m3 < 14.8, density_kg_m3
