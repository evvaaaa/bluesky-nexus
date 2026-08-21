from bluesky import plans as bp
from ophyd.sim import SynAxis

# Now scan a very simple device and observe the generated structure.
RE(bp.count([SynAxis(name="syn_axis")]))
