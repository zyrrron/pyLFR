from typing import Dict, List

from lfr.fig.interaction import InteractionType
from lfr.netlistgenerator.connectingoption import ConnectingOption
from lfr.netlistgenerator.connection_primitive import ConnectionPrimitive
from lfr.netlistgenerator.mappinglibrary import MappingLibrary
from lfr.netlistgenerator.primitive import Primitive, PrimitiveType
from lfr.netlistgenerator.procedural_component_algorithms.ytree import YTREE
library = MappingLibrary("mlsi")

# MICROARRAY

microarray_inputs: List[ConnectingOption] = []

for i in range(10):
    microarray_inputs.append(ConnectingOption(None, ["1"]))

microarray_outputs: List[ConnectingOption] = []

for i in range(10):
    microarray_outputs.append(ConnectingOption(None, ["3"]))

microarray_loadings: List[ConnectingOption] = []
microarray_carriers: List[ConnectingOption] = []

microarray = Primitive(
    "MICROARRAY",
    PrimitiveType.COMPONENT,
    r"""{
        v1:STORAGE
    }""",
    False,
    False,
    microarray_inputs,
    microarray_outputs,
    microarray_loadings,
    microarray_carriers,
    None,
)

library.add_storage_entry(microarray)