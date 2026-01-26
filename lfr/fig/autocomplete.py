from lfr.fig.fluidinteractiongraph import FluidInteractionGraph
from lfr.fig.fignode import FIGNode, IONode, IOType

def connect_orphan_IO(fig: FluidInteractionGraph) -> None:
    waste_counter = 0  # Initialize the counter for waste nodes

    # Step 1 - Go through all the flow nodes and check if any of them have zero outputs.
    for node_id in list(fig.nodes):
        if isinstance(fig.get_fignode(node_id), FIGNode):
            # Check if the node has no outgoing edges
            if fig.out_degree(node_id) == 0:
                # Step 2 - Generate a new IO node and connect it to the orphaned flow node
                new_io_node = IONode(f"out_waste_{waste_counter}", iotype=IOType.FLOW_OUTPUT)  # Generate unique ID
                fig.add_fignode(new_io_node)  # Add the IO node to the graph
                fig.connect_fignodes(fig.get_fignode(node_id), new_io_node)  # Connect flow node to the IO node
                waste_counter += 1
