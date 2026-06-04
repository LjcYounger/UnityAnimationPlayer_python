from .parsers import XCurves
from .parsers import Events
from .utils import timer

@timer(name="parse_anim")
def parse_anim(anim_dict):
    anim_dict = anim_dict["AnimationClip"]

    stop_time, paths = XCurves.parse(anim_dict)
    events = Events.parse(anim_dict)
    return stop_time, paths, events