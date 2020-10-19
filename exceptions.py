class PlanetEngineException(Exception):
    '''PlanetEngine exception.'''
    pass

class NaNFound(PlanetEngineException):
    '''Nan was found.'''
    pass

class AcceptableToleranceNotFound(PlanetEngineException):
    '''Acceptable tolerance could not be found.'''
    pass

class NotYetImplemented(PlanetEngineException):
    '''Feature not implemented yet.'''
    pass

class MissingMethod(PlanetEngineException):
    pass

class MissingAsset(PlanetEngineException):
    pass
