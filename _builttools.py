from collections.abc import Mapping
from functools import partial

from .utilities import interp_dicts

def get_sliceFn(self, basket, builder, keywords):
    return partial(
        sliceFn,
        self,
        basket = basket,
        builder = builder,
        keywords = keywords
        )

def sliceFn(self, inputs, basket, builder, keywords):
    if isinstance(inputs, basket.CLASS):
        return builder.build(**dict(zip(keywords, (self, inputs))))
    elif type(inputs) is slice or type(inputs) is tuple:
        return yield_sliceFn(
            self, inputs, basket, builder, keywords
            )
    elif isinstance(inputs, Mapping):
        return sliceFn(self, basket.build(**inputs), basket, builder, keywords)
    else:
        raise TypeError

def yield_sliceFn(self, inputs, basket, builder, keywords):
    if type(inputs) is tuple:
        inTuple = inputs
        for inBasket in inTuple:
            yield from yield_sliceFn(
                self, inBasket, basket, builder, keywords
                )
    elif isinstance(inputs, Mapping):
        yield from yield_sliceFn(
            self, basket.build(**inputs), basket, builder, keywords
            )
    elif type(inputs) is slice:
        slicer = inputs
        mins, maxs, n = slicer.start, slicer.stop, slicer.step
        for interpDict in interp_dicts(mins.inputs, maxs.inputs, n):
            inBasket = basket.build(**interpDict)
            yield from yield_sliceFn(self, inBasket, basket, builder, keywords)
    elif isinstance(inputs, basket.CLASS):
        yield builder.build(**dict(zip(keywords, (self, inputs))))
    else:
        raise TypeError
