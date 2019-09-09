LOADTYPE = True
from planetengine.initials import load

IC = load.IC

def build(*args, **kwargs):
    return load.build(*args, **kwargs)
