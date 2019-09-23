class Clip(Function):

    opTag = 'Clip'

    def __init__(
            self,
            inVar,
            lBnd = None,
            lClipVal = 'null',
            uBnd = None,
            uClipVal = 'null',
            **kwargs
            ):

        inVar = convert(inVar)
        inVars = [inVar]
        stringVariants = {}
        parameters = []
        clauses = []
        nullVal = [np.nan for dim in range(inVar.varDim)]

        if lBnd is None:
            stringVariants['lower'] = 'open'
        else:
            lBnd = convert(lBnd)
            if not lBnd in inVars:
                inVars.append(lBnd)
            lBnd = Parameter(lBnd.minFn)
            parameters.append(lBnd)
            if lClipVal is 'null':
                lClipVal = nullVal
                stringVariants['lower'] = 'null'
            elif lClipVal == 'fill':
                lClipVal = lBnd
                stringVariants['lower'] = 'fill'
            else:
                raise Exception
            clauses.append((inVar < lBnd, lClipVal))

        if uBnd is None:
            stringVariants['lower'] = 'open'
        else:
            uBnd = convert(uBnd)
            if not uBnd in inVars:
                inVars.append(uBnd)
            uBnd = Parameter(uBnd.maxFn)
            parameters.append(uBnd)
            if uClipVal is 'null':
                uClipVal = nullVal
                stringVariants['upper'] = 'null'
            elif uClipVal == 'fill':
                uClipVal = uBnd
                stringVariants['upper'] = 'fill'
            else:
                raise Exception
            clauses.append((inVar > uBnd, uClipVal))

        clauses.append((True, inVar))

        if stringVariants['lower'] == stringVariants['upper']:
            stringVariants['both'] = stringVariants['lower']
            del stringVariants['lower']
            del stringVariants['upper']

        var = fn.branching.conditional(clauses)

        self.stringVariants = stringVariants
        self.inVars = list(inVars)
        self.parameters = parameters
        self.var = var

        super().__init__(**kwargs)

    @staticmethod
    def torange(inVar, clipVar, **kwargs):
        inVar, clipVar = convert(inVar, clipVar)
        return Clip(
            inVar,
            lBnd = clipVar,
            uBnd = clipVar,
            **kwargs
            )
