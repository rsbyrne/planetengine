# from ._copy import Copy
#
# class State(Copy):
#
#     from .state import __file__ as _file_
#
#     def __init__(
#             self,
#             real = None,
#             varName = None,
#             state = None,
#             **kwargs
#             ):
#
#         def initialise():
#             with real.bounce():
#             if not state(real):
#                 real[state]()
#             return real
#
#         super().__init__(
#             initialise,
#             varName,
#             **kwargs
#             )
