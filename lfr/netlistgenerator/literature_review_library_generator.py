from typing import Dict, List

from lfr.fig.interaction import InteractionType
from lfr.netlistgenerator.connectingoption import ConnectingOption
from lfr.netlistgenerator.connection_primitive import ConnectionPrimitive
from lfr.netlistgenerator.mappinglibrary import MappingLibrary
from lfr.netlistgenerator.primitive import Primitive, PrimitiveType
from lfr.netlistgenerator.procedural_component_algorithms.ytree import YTREE
library = MappingLibrary("mlsi")

# MICROARRAY

filter_inputs: List[ConnectingOption] = []

for i in range(10):
    filter_inputs.append(ConnectingOption(None, ["1"]))

filter_outputs: List[ConnectingOption] = []

for i in range(10):
    filter_outputs.append(ConnectingOption(None, ["3"]))

filter_loadings: List[ConnectingOption] = []
filter_carriers: List[ConnectingOption] = []

filter = Primitive(
    "FILTER",
    PrimitiveType.COMPONENT,
    r"""{
        v1:STORAGE
    }""",
    False,
    False,
    filter_inputs,
    filter_outputs,
    filter_loadings,
    filter_carriers,
    None,
)

library.add_storage_entry(filter)