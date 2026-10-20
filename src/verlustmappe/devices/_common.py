import numpy as np
def t_seconds(index):
    """DatetimeIndex or TimedeltaIndex -> float seconds."""
    try:
        return index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    except Exception:
        return (index.values.astype("timedelta64[ns]").astype(np.int64) / 1e9)
