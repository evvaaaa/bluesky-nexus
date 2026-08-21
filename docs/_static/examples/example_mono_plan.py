from bluesky import plans as bp
from ophyd_async.plan_stubs import ensure_connected

mono = PlaneGratingMonochromator(name="pgm")
RE(ensure_connected(mono, mock=True))
RE(bp.scan([mono], mono.energy, 545, 550, num=10))
