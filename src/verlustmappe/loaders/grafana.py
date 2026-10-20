"""Load Grafana long-format exports ("Series";"Time";"Value") into one wide DataFrame."""
import csv, glob, os
import pandas as pd

def load_grafana(paths, encoding="utf-8-sig"):
    """paths: list of files OR a folder glob string. Returns wide df, index=UTC."""
    files = []
    for p in paths:
        if os.path.isdir(p): files += sorted(glob.glob(os.path.join(p, "*.csv")))
        else: files.append(p)
    frames = {}
    for f in files:
        rows = []
        with open(f, encoding=encoding) as fh:
            r = csv.reader(fh, delimiter=";")
            for row in r:
                if len(row) >= 3 and row[0].strip('"') != "Series":
                    raw = row[2].strip('"')
                    try: val = float(raw.replace(",", "."))
                    except (ValueError, IndexError): continue
                    rows.append((row[0].strip('"'), row[1].strip('"'), val))
        if not rows:
            import logging
            logging.getLogger("verlustmappe.loaders").warning(
                "no parseable numeric rows in %s (decimal comma with other separators? encoding?)", f)
            continue
        df = pd.DataFrame(rows, columns=["series", "time", "value"])
        for s, g in df.groupby("series"):
            if s == "Series": continue
            frames[s] = pd.Series(g["value"].values, index=pd.to_datetime(g["time"], utc=True), name=s)
    return pd.DataFrame(frames).sort_index()

# Grafana series name -> pipeline column name
FC_MAP = {"Power": "fc_power_W", "Voltage": "fc1_voltage_V", "Amperage": "fc1_current_A",
          "Anode Pressure": "anode_pressure_mbar", "Inlet Temperature": "t_in_C",
          "Outlet Temperature": "t_out_C", "Fan SP duty": "fan_duty",
          "DC/DC Current Limit": "dcdc_i_limit", "DC/DC Voltage Set Point": "dcdc_v_sp",
          "Louver Position Open": "louver_pos", "Run Hours": "run_hours",
          "Total Run Energy": "total_run_energy", "Fault Flags A": "fault_a",
          "Fault Flags B": "fault_b", "Fault Flags C": "fault_c", "Fault Flags D": "fault_d"}

def map_fc(df):
    out = df.rename(columns={k: v for k, v in FC_MAP.items() if k in df.columns})
    return out[[v for v in FC_MAP.values() if v in out.columns]]


PV_MAP = {"Real-time Active Power (W)": "ac_power_W", "DC Power": "dc_power_W",
          "Total Yield (Wh)": "ac_energy_Wh_cum", "DC Voltage": "dc_V", "DC Current": "dc_A",
          "Inverter Temperature": "inv_T_C", "Grid Frequency": "grid_Hz"}
EL_MAP = {"H2 Production, NL/hour": "h2_flow_NLh", "Total H2 Produced": "h2_total_NL_cum",
          "H2 Stack Pressure": "stack_p_bar", "H2 Outlet Pressure": "outlet_p_bar",
          "Water Inlet Pressure": "water_p_bar", "Electrolyte Tank Temperature": "el_T_C",
          "Downstream Temperature": "down_T_C", "Total Stack Runtime": "runtime_cum",
          "Stack Amperage": "el_stack_current_A", "Stack Voltage": "el_stack_voltage_V",
          "stack_amperage": "el_stack_current_A", "stack_voltage": "el_stack_voltage_V"}

def _apply(df, mapping):
    out = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    return out[[v for v in mapping.values() if v in out.columns]]

def map_pv(df): return _apply(df, PV_MAP)
def map_el(df): return _apply(df, EL_MAP)
