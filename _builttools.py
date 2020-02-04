from collections.abc import Mapping
from functools import partial

from .utilities import interp_dicts
from .utilities import random_interp_dicts

# class Slicer:
#     def __init__(
#             self,
#             obj,
#             basket,
#             builder,
#             keywords
#             ):
#         self.obj = obj
#         self.basket = basket
#         self.builder = builder
#         self.keywords = keywords
#
#     def slice_basket_fn(self, inp):
#         return builder.build(**dict(zip(self.keywords, (obj, inputs))))
#
#     def slice_mapping_fn(self, inp):
#         sliceBasket = self.basket.build(**inp)
#         return self.slice_basket_fn(sliceBasket)
#
#     def slice_tuple_fn(self, inp):
#         for subInp in inp:
#             yield from self.slice_fn(subInp)
#
#     def slice_slice_fn(self, inp):
#         start, stop, step = inp
#
#     def slice_fn(self, inputs):
#
#
# def get_sliceFn(self, basket, builder, keywords):
#     return partial(
#         sliceFn,
#         self,
#         basket = basket,
#         builder = builder,
#         keywords = keywords
#         )

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
        if n is None:
            while True:
                yield random_interp_dicts(mins.inputs, maxs.inputs)
        else:
            for interpDict in interp_dicts(mins.inputs, maxs.inputs, n):
                inBasket = basket.build(**interpDict)
                yield from yield_sliceFn(
                    self, inBasket, basket, builder, keywords
                    )
    elif isinstance(inputs, basket.CLASS):
        yield builder.build(**dict(zip(keywords, (self, inputs))))
    else:
        raise TypeError
