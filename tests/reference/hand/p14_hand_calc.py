"""Independent P14 numerical reference. Standard library only.

Uses the approved conventional molar mass and rounded-MJ LHV basis.
F = 96485.33212 C/mol is the rounded CODATA display of the exact SI
product e * N_A = 96485.3321233100184 C/mol.
Does not import production/legacy code or validate plant performance.
Zero comparisons are numeric, never string/repr comparisons.
"""

from decimal import Decimal, localcontext


D = Decimal


def calculate(
    el_ac_input_power_W: Decimal,
    stack_current_A: Decimal,
    operating_time_s: Decimal,
    el_ac_standby_power_W: Decimal,
    standby_time_s: Decimal,
) -> dict[str, Decimal]:
    with localcontext() as context:
        context.prec = 50

        faraday_C_per_mol = D("96485.33212")
        molar_mass_kg_per_mol = D("0.002016")
        lhv_kWh_per_kg = D("119.96") / D("3.6")
        joules_per_kWh = D("3600000")
        n_cells = D("120")
        faradaic_efficiency = D("0.98")

        operating_energy_kWh = (
            el_ac_input_power_W * operating_time_s / joules_per_kWh
        )
        standby_energy_kWh = (
            el_ac_standby_power_W * standby_time_s / joules_per_kWh
        )
        hydrogen_amount_mol = (
            faradaic_efficiency
            * n_cells
            * stack_current_A
            * operating_time_s
            / (D("2") * faraday_C_per_mol)
        )
        hydrogen_mass_kg = hydrogen_amount_mol * molar_mass_kg_per_mol
        hydrogen_lhv_energy_kWh = hydrogen_mass_kg * lhv_kWh_per_kg

        return {
            "operating_energy_kWh": operating_energy_kWh,
            "standby_energy_kWh": standby_energy_kWh,
            "hydrogen_amount_mol": hydrogen_amount_mol,
            "hydrogen_mass_kg": hydrogen_mass_kg,
            "hydrogen_lhv_energy_kWh": hydrogen_lhv_energy_kWh,
        }


def main() -> None:
    cases = (
        (
            "A: approved synthetic reference",
            (D("2100"), D("8"), D("2700"), D("20"), D("1800")),
        ),
        (
            "Z1: complete zero calculation; not a balance proof",
            (D("0"), D("0"), D("2700"), D("0"), D("1800")),
        ),
        (
            "Z2: isolated zero-current algebraic edge case",
            (D("2100"), D("0"), D("2700"), D("20"), D("1800")),
        ),
    )
    display_formats = {
        "operating_energy_kWh": ".3f",
        "standby_energy_kWh": ".3f",
        "hydrogen_amount_mol": ".13f",
        "hydrogen_mass_kg": ".16f",
        "hydrogen_lhv_energy_kWh": ".15f",
    }

    print("P14 independent numerical reference")
    print("No plant validation, loss decomposition, RTE or output uncertainty.")
    print("Constant AC power and DC current; non-overlapping standby period.")
    print("Molar mass: conventional 0.002016 kg/mol.")
    print("LHV basis: rounded 119.96 MJ/kg, then divided by 3.6.")
    print("Display rounding only; compare zero numerically, not by string/repr.")

    for label, inputs in cases:
        print(f"\n{label}")
        for name, value in calculate(*inputs).items():
            print(f"{name} = {format(value, display_formats[name])}")


if __name__ == "__main__":
    main()
