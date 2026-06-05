from ..utils import timer

@timer(name="Events.parse")
def parse(anim_dict):
    return anim_dict['m_Events']