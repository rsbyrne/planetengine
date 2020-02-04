from collections.abc import Mapping
from functools import partial

from .utilities import interp_dicts
from .utilities import random_interp_dicts

# class Slicer:
#     def __init__(
#             self,
#             obj,
#             vector,
#             builder,
#             keywords
#             ):
#         self.obj = obj
#         self.vector = vector
#         self.builder = builder
#         self.keywords = keywords
#
#     def slice_vector_fn(self, inp):
#         return builder.build(**dict(zip(self.keywords, (obj, inputs))))
#
#     def slice_mapping_fn(self, inp):
#         sliceVector = self.vector.build(**inp)
#         return self.slice_vector_fn(sliceVector)
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
# def get_sliceFn(self, vector, builder, keywords):
#     return partial(
#         sliceFn,
#         self,
#         vector = vector,
#         builder = builder,
#         keywords = keywords
#         )

def sliceFn(self, inputs, vector, builder, keywords):
    if isinstance(inputs, vector.CLASS):
        return builder.build(**dict(zip(keywords, (self, inputs))))
    elif type(inputs) is slice or type(inputs) is tuple:
        return yield_sliceFn(
            self, inputs, vector, builder, keywords
            )
    elif isinstance(inputs, Mapping):
        return sliceFn(self, vector.build(**inputs), vector, builder, keywords)
    else:
        raise TypeError

def yield_sliceFn(self, inputs, vector, builder, keywords):
    if type(inputs) is tuple:
        inTuple = inputs
        for inVector in inTuple:
            yield from yield_sliceFn(
                self, inVector, vector, builder, keywords
                )
    elif isinstance(inputs, Mapping):
        yield from yield_sliceFn(
            self, vector.build(**inputs), vector, builder, keywords
            )
    elif type(inputs) is slice:
        slicer = inputs
        mins, maxs, n = slicer.start, slicer.stop, slicer.step
        if n is None:
            while True:
                yield random_interp_dicts(mins.inputs, maxs.inputs)
        else:
            for interpDict in interp_dicts(mins.inputs, maxs.inputs, n):
                inVector = vector.build(**interpDict)
                yield from yield_sliceFn(
                    self, inVector, vector, builder, keywords
                    )
    elif isinstance(inputs, vector.CLASS):
        yield builder.build(**dict(zip(keywords, (self, inputs))))
    else:
        raise TypeError
