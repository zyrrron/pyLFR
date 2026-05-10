from typing import Dict, List, Set, Tuple

import networkx as nx
from parchmint import Target
from parchmint.connection import Connection
from pymint.mintdevice import MINTDevice

from lfr.netlistgenerator.connectingoption import ConnectingOption
from lfr.netlistgenerator.constructiongraph.constructiongraph import ConstructionGraph
from lfr.netlistgenerator.mappinglibrary import MappingLibrary
from lfr.netlistgenerator.namegenerator import NameGenerator
from lfr.netlistgenerator.primitive import PrimitiveType, ProceduralPrimitive


def generate_device(
    construction_graph: ConstructionGraph,
    scaffhold_device: MINTDevice,
    name_generator: NameGenerator,
    mapping_library: MappingLibrary,
) -> Dict[str, List[str]]:
    # TODO - Generate the device
    # Step 1 - go though each of the construction nodes and genrate the corresponding
    # components
    # Step 2 - generate the connections between the outputs to input on the connected
    # construction nodes
    # Step 3 - TODO - Generate the control network

    cn_component_mapping: Dict[str, List[str]] = {}

    node_ids = nx.dfs_preorder_nodes(construction_graph)
    print("Nodes to Traverse:", node_ids)

    # Go through the ordered nodes and start creating the components
    for node_id in node_ids:
        cn = construction_graph.get_construction_node(node_id)

        # raise and error if the construction node has no primitive
        if cn.primitive is None:
            raise ValueError(f"Construction Node: {node_id} has no primitive")

        # Generate the netlist based on the primitive type
        if cn.primitive.type is PrimitiveType.COMPONENT:
            # Generate the component
            component = cn.primitive.get_default_component(
                name_generator, scaffhold_device.device.layers[0]
            )

            # Add to the scaffhold device
            scaffhold_device.device.add_component(component)

            # Add to the component mapping
            cn_component_mapping[node_id] = [component.ID]

        elif cn.primitive.type is PrimitiveType.NETLIST:
            netlist = cn.primitive.get_default_netlist(cn.ID, name_generator)

            # Merge the netlist into the scaffhold device
            scaffhold_device.device.merge_netlist(netlist)

            # Add to the component mapping
            cn_component_mapping[node_id] = [
                component.ID for component in netlist.components
            ]

        elif cn.primitive.type is PrimitiveType.PROCEDURAL:
            layer = scaffhold_device.device.layers[0]
            proc = cn.primitive
            if not isinstance(proc, ProceduralPrimitive):
                raise TypeError(
                    f"Expected ProceduralPrimitive for {node_id}, got {type(proc)}"
                )
            component = proc.get_procedural_component(
                name_generator, layer, cn.fig_subgraph
            )
            scaffhold_device.device.add_component(component)
            cn_component_mapping[node_id] = [component.ID]

    # Go through the edges and connect the components using the inputs and outputs of
    # the primitives
    for source_cn_id, target_cn_id in construction_graph.edges:

        source_cn = construction_graph.get_construction_node(source_cn_id)
        target_cn = construction_graph.get_construction_node(target_cn_id)

        # Get the output ConnectingOptions of the source cn
        output_options = source_cn.output_options.copy()
        input_options = target_cn.input_options.copy()

        # Pop and make a connection between the output and the input
        source_option = output_options.pop()
        target_option = input_options.pop()

        #Source option exists here
        #print(source_option.component_port)

        # Generate the target from the source option
        source_targets = get_targets(
            source_option, source_cn_id, name_generator, cn_component_mapping
        )

        target_targets = get_targets(
            target_option, target_cn_id, name_generator, cn_component_mapping
        )

        #print(source_targets)
        #print(target_targets)
        # If there is 1 source and 1 target, then connect the components
        if len(source_targets) == 1 and len(target_targets) == 1:
            create_device_connection(
                source_targets.pop(),
                target_targets.pop(),
                name_generator,
                scaffhold_device,
                mapping_library,
            )

        elif len(source_targets) == len(target_targets):
            raise NotImplementedError("Bus targets not implemented")
        elif len(source_targets) == 1 and len(target_targets) > 1:
            raise NotImplementedError("Multiple targets not implemented")
        elif len(source_targets) > 1 and len(target_targets) == 1:
            raise NotImplementedError("Multiple sources not implemented")

    return cn_component_mapping


def _fig_id_from_node(n) -> str:
    """Return FIG node ID (string) from a node in fig_subgraph (object or str)."""
    return getattr(n, "ID", str(n))


def generate_control_network(
    module,
    variant: ConstructionGraph,
    cn_component_mapping: Dict[str, List[str]],
    scaffhold_device: MINTDevice,
) -> None:
    """Add CONTROL layer, valves on flow connections, and Cport components from FIG state_tables.

    Control-layer ports are named Cport_0, Cport_1, ... to distinguish from flow layer.
    """
    from parchmint.device import ValveType
    from pymint.mintlayer import MINTLayerType

    fig = module.FIG
    if not fig.state_tables:
        return

    # Build fig_node_id -> set(device component IDs)
    fig_to_components: Dict[str, set] = {}
    for cn in variant.construction_nodes:
        try:
            sub = cn.fig_subgraph
        except Exception:
            continue
        fig_ids = set(_fig_id_from_node(n) for n in sub.nodes)
        comps = set(cn_component_mapping.get(cn.ID, []))
        for fid in fig_ids:
            fig_to_components.setdefault(fid, set()).update(comps)

    # Collect all control mappings from state tables
    control_entries: List[Tuple[Tuple[str, str], str, str]] = []
    for st in fig.state_tables:
        control_entries.extend(st.get_control_mapping())

    if not control_entries:
        return

    # Resolve FIG node ID to component set (use _removed_to_surviving alias after simplification)
    def resolve_fig_id(fig_id: str) -> Set[str]:
        out = set(fig_to_components.get(fig_id, set()))
        if not out and getattr(fig, "_removed_to_surviving", None):
            aliased = fig._removed_to_surviving.get(fig_id)
            if aliased:
                out = set(fig_to_components.get(aliased, set()))
        return out

    # Ensure CONTROL layer exists (id "1", name "control")
    control_layer_id = "1"
    try:
        scaffhold_device.device.get_layer(control_layer_id)
    except KeyError:
        scaffhold_device.create_mint_layer(
            control_layer_id, "control", 1, MINTLayerType.CONTROL
        )

    for idx, ((fig_src, fig_tgt), valve_id, _ctrl_id) in enumerate(control_entries):
        src_comps = resolve_fig_id(fig_src)
        tgt_comps = resolve_fig_id(fig_tgt)
        conn = None
        for c in scaffhold_device.device.connections:
            if c.layer is None or c.layer.ID != "0":
                continue
            src_ok = c.source and c.source.component in src_comps
            snk = c.sinks[0] if c.sinks else None
            tgt_ok = snk and snk.component in tgt_comps
            if src_ok and tgt_ok:
                conn = c
                break
        if conn is None:
            continue

        # Add control-layer port first (so we can connect Ctrlchannel from it to valve)
        cport_name = "Cport_{}".format(idx)
        if not any(c.ID == cport_name for c in scaffhold_device.device.components):
            scaffhold_device.create_mint_component(
                name=cport_name,
                technology="PORT",
                params={"position": [-1, -1]},
                layer_ids=[control_layer_id],
            )

        # Add valve on this flow connection (on control layer).
        # VALVE3D uses valveRadius (not planar VALVE width/length). Explicit
        # componentSpacing avoids fluigi's global default (9000 µm) being injected
        # for every component when serializing to *_fromLFR.mint / JSON.
        if not any(v.ID == valve_id for v in scaffhold_device.device.valves):
            scaffhold_device.create_valve(
                name=valve_id,
                technology="VALVE3D",
                params={
                    "position": [-1, -1],
                    "controlPort": cport_name,
                    "componentSpacing": 1000,
                    "valveRadius": 400,
                    "height": 250,
                },
                layer_ids=[control_layer_id],
                connection=conn,
                valve_type=ValveType.NORMALLY_OPEN,
            )

        scaffhold_device.device.set_valve_control_port(valve_id, cport_name)

        # Control-layer channel from Cport to valve (Ctrlchannel to distinguish from flow CHANNELs)
        ctrl_channel_name = "Ctrlchannel_{}".format(idx)
        if not any(c.ID == ctrl_channel_name for c in scaffhold_device.device.connections):
            src_target = Target(component_id=cport_name, port="1")
            sink_target = Target(component_id=valve_id, port="1")
            scaffhold_device.create_mint_connection(
                name=ctrl_channel_name,
                technology="CHANNEL",
                params={"position": [-1, -1]},
                source=src_target,
                sinks=[sink_target],
                layer_id=control_layer_id,
            )


def create_device_connection(
    source_target: Target,
    target_target: Target,
    name_generator: NameGenerator,
    scaffhold_device: MINTDevice,
    mapping_library: MappingLibrary,
) -> None:
    # TODO - Create the connection based on parameters from the connecting option
    # Step 1 - Get the connection from the mapping library
    # TODO: Create new method stubs to get the right connection primitives from the
    # mapping library (this would need extra criteria that that will need evaulation
    # in the future (RAMA Extension))
    primitive = mapping_library.get_default_connection_entry()
    # Step 2 - Create the connection in the device
    connection_name = name_generator.generate_name(primitive.mint)
    connection = Connection(
        name=connection_name,
        ID=connection_name,
        entity=primitive.mint,
        source=source_target,
        sinks=[target_target],
        layer=scaffhold_device.device.layers[
            0
        ],  # TODO - This will be replaced in the future when we introduce layer sharding
    )
    scaffhold_device.device.add_connection(connection)


def get_targets(
    option: ConnectingOption,
    connection_node_id: str,
    name_generator: NameGenerator,
    cn_name_map,
) -> List[Target]:
    ret: List[Target] = []

    if option.component_name is None:
        # TODO: Clarify the logic for doing this later on and put it in the docstring
        component_names = cn_name_map[connection_node_id]
    else:
        # TODO: Clarify the logic for doing this later on and put it in the docstring
        old_name = option.component_name
        component_name = name_generator.get_cn_name(connection_node_id, old_name)
        component_names = [component_name]
    for component_name in component_names:
        for port_name in option.component_port:
            # Check and make sure that the component name is valid
            if component_name is None:
                raise ValueError(
                    "Could not generate connection target for construction node"
                    f" {connection_node_id} since Port name is None"
                )
            target = Target(component_name, port_name)
            ret.append(target)

    return ret
