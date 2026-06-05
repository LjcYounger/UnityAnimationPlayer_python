from .parsers import XCurves
from .parsers import Events

def parse_anim(anim_dict):
    anim_dict = anim_dict["AnimationClip"]

    stop_time, paths = XCurves.parse(anim_dict)
    events = Events.parse(anim_dict)
    return stop_time, paths, events