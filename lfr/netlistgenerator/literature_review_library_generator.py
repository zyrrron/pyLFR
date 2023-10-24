# MICROARRAY

filter_inputs: List[ConnectingOption] = []

filter_inputs.append(ConnectingOption(None, ["1"]))

filter_outputs: List[ConnectingOption] = []

filter_outputs.append(ConnectingOption(None, ["2"]))

filter_loadings: List[ConnectingOption] = []
filter_carriers: List[ConnectingOption] = []

filter = Primitive(
    "FILTER",
    PrimitiveType.COMPONENT,
    r"""{
        v1:PROCESS
    }""",
    False,
    False,
    filter_inputs,
    filter_outputs,
    filter_loadings,
    filter_carriers,
    None,
)

library.add_operator_entry(filter, InteractionType.TECHNOLOGY_PROCESS)