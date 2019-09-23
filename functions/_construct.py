from . import _planetvar
from . import _basetypes

def _construct(
        varClass,
        *inVars,
        **stringVariants
        ):

    if issubclass(varClass, _basetypes.BaseTypes):

        outObj = varClass(
            *inVars,
            **stringVariants
            )

        return outObj

    else:

        makerTag = _planetvar.get_opHash(varClass, *inVars, **stringVariants)

        outObj = None
        for inVar in inVars:
            if hasattr(inVar, '_planetVars'):
                if makerTag in inVar._planetVars:
                    outObj = inVar._planetVars[makerTag]()
                    if isinstance(outObj, PlanetVar):
                        break
                    else:
                        outObj = None

        if outObj is None:
            message('Building new object...')
            outObj = varClass(
                *inVars,
                **stringVariants
                )
        else:
            message('Old object found - reusing.')

        for inVar in inVars:
            try:
                if not hasattr(inVar, '_planetVars'):
                    inVar._planetVars = {}
                weak_reference = weakref.ref(outObj)
                inVar._planetVars[makerTag] = weak_reference
            except:
                pass

        return outObj
