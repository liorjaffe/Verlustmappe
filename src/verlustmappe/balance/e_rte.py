"""Round-trip efficiency (RTE) at two boundaries. Both are needed:

  storage-chain RTE  = E_AC,out / E_AC,in(charge)
      boundary: AC bus. Comparable to literature (Veritas 10%/24% CHP, etc.)
      E_in  = E_EL + E_dryer + E_compression + E_standby(charge side)
      E_out = (E_FC,terminal - E_control) * eta_inverter

  island RTE         = E_AC,out / E_PV,AC  (what fraction of the solar
      electricity that entered the storage path came back as usable AC)

Definitions follow the energy-storage convention (ratio of discharged to
charged electrical energy over one full cycle), e.g. IEC 62933-2-1.
"""

def storage_chain_rte(E_el_kWh, E_dryer_kWh, E_comp_kWh, E_fc_out_kWh, E_ctrl_kWh, eta_inverter=1.0,
                      E_standby_kWh=0.0, E_water_kWh=0.0):
    e_in = E_el_kWh + E_dryer_kWh + E_comp_kWh + E_water_kWh
    e_out = (E_fc_out_kWh - E_ctrl_kWh) * eta_inverter
    return dict(boundary="storage_chain", E_in_kWh=e_in, E_out_kWh=e_out,
                rte=e_out / e_in if e_in > 0 else None,
                breakdown=dict(EL=E_el_kWh, DRY=E_dryer_kWh, CSU=E_comp_kWh, WATER=E_water_kWh,
                               standby=E_standby_kWh,
                               FC_out=E_fc_out_kWh, control=E_ctrl_kWh, inverter_eta=eta_inverter))

def island_rte(E_pv_ac_kWh, storage_result):
    return dict(boundary="island", E_pv_ac_kWh=E_pv_ac_kWh, E_out_kWh=storage_result["E_out_kWh"],
                rte=storage_result["E_out_kWh"] / E_pv_ac_kWh if E_pv_ac_kWh > 0 else None,
                storage_chain_rte=storage_result["rte"])
