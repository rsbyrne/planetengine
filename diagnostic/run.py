import planetengine
from planetengine.diagnostic import diagnostics
from timeit import timeit

result = timeit(diagnostics.diagnostic_01, setup="gc.enable()", number=3)
planetengine.message(result)