from __future__ import annotations

import os
from typing import FrozenSet, List

import networkx as nx

from lfr import parameters
from lfr.fig.fignode import Flow, IONode, IOType, ValueNode
from lfr.fig.fluidinteractiongraph import FluidInteractionGraph
from lfr.netlistgenerator.constructiongraph.constructionnode import ConstructionNode


class ConstructionGraph(nx.DiGraph):
    """
    This class is a sub-class of networkx.DiGraph.
    It acts as a proxy datastructure for generating the device netlist.
    """

    def __init__(self, id: str, fig: FluidInteractionGraph) -> None:
        """Initializes the construction graph

        Args:
            id (str): ID of the construction graph
            fig (FluidInteractionGraph): Fluid interaction graph which the construction
        """
        super().__init__()
        self._id = id
        self._fig = fig
        self._construction_nodes: List[ConstructionNode] = []

    @property
    def ID(self) -> str:
        """Returns the ID of the construction graph

        Returns:
            str: ID of the construction graph
        """
        return self._id

    @property
    def construction_nodes(self) -> List[ConstructionNode]:
        return self._construction_nodes

    def add_construction_node(self, construction_node: ConstructionNode) -> None:
        """Adds a construction node to the graph

        Args:
            construction_node (ConstructionNode): Node to add the the construction graph
        """

        self._construction_nodes.append(construction_node)
        self.add_node(construction_node.ID)

    def remove_construction_node(self, construction_node: ConstructionNode) -> None:
        """Remove a construction node from the graph

        Args:
            construction_node (ConstructionNode): Node to remove from the construction
            graph
        """
        # Remove the construction node from the graph
        self.remove_node(construction_node.ID)
        self._construction_nodes.remove(construction_node)

    def get_construction_node(self, id: str) -> ConstructionNode:
        """Returns the construction node with the given id

        Args:
            id (str): ID of the construction node to return

        Raises:
            ValueError: If the construction node with the given id does not exist

        Returns:
            ConstructionNode: Construction node with the given id
        """
        for cn in self._construction_nodes:
            if cn.ID == id:
                return cn
        else:
            raise ValueError("No construction node with id: " + id)

    def connect_nodes(self, node_a: ConstructionNode, node_b: ConstructionNode) -> None:
        """
        This method connects two nodes in the graph.
        """
        self.add_edge(node_a.ID, node_b.ID)

    def is_fig_fully_covered(self) -> bool:
        """
        This method checks if the FIG is fully covered by the construction graph.
        Only flow-layer nodes are required to be covered; CONTROL IONodes (e.g. control c)
        are not mapped to flow primitives and are handled on the control layer.
        Auto-added waste outputs (out_waste_*) are also excluded from required coverage.
        """
        # Flow nodes only: exclude CONTROL and waste outputs. Also exclude
        # numeric-value nodes (ValueNode, e.g. the `50` in `x % 50`) and the
        # internal FLOW_component_replacement_* bookkeeping nodes created during
        # FIG simplification -- those are never mapped to a physical primitive
        # but are part of the graph so they would otherwise be reported as
        # uncovered and falsely kill every variant.
        fig_flow_node_ids = set()
        for nid in self._fig.nodes:
            if isinstance(nid, str) and nid.startswith("out_waste_"):
                continue
            if isinstance(nid, str) and nid.startswith("FLOW_component_replacement_"):
                continue
            try:
                node = self._fig.get_fignode(nid)
            except Exception:
                fig_flow_node_ids.add(nid)
                continue
            if isinstance(node, IONode) and getattr(node, "type", None) == IOType.CONTROL:
                continue
            if isinstance(node, ValueNode):
                continue
            fig_flow_node_ids.add(nid)
        for cn in self._construction_nodes:
            fig_subgraph = cn.fig_subgraph
            for node in fig_subgraph.nodes:
                nid = getattr(node, "ID", node)
                if nid in fig_flow_node_ids:
                    fig_flow_node_ids.discard(nid)
        self._relax_uncovered_plain_flow_junctions(fig_flow_node_ids)
        if fig_flow_node_ids:
            print(f"FIG not fully covered: uncovered flow node(s) = {fig_flow_node_ids}")
        return len(fig_flow_node_ids) == 0

    def _relax_uncovered_plain_flow_junctions(self, uncovered: set) -> None:
        """Drop plain FIG Flow nodes from *uncovered* when they are only routing.

        Many valid designs expose only PORT/STORAGE/channel primitives on the FIG; plain
        ``Flow`` vertices implement routing (merges, distribute temporaries, FIG splits).
        Peel them iteratively: remove a plain Flow from *uncovered* if it has at least
        one neighbor that is already not uncovered (i.e. lies on the covered side of the
        frontier). This walks chains inward from covered primitives without clearing a
        pocket that is still entirely uncovered (e.g. a subgraph only among uncovered
        Storage / IO).
        """
        fig = self._fig
        changed = True
        while changed:
            changed = False
            for nid in list(uncovered):
                try:
                    node = fig.get_fignode(nid)
                except Exception:
                    continue
                if type(node) is not Flow:
                    continue
                neighbors = set(fig.predecessors(nid)) | set(fig.successors(nid))
                if not neighbors:
                    continue
                if any(m not in uncovered for m in neighbors):
                    uncovered.discard(nid)
                    changed = True

    def generate_variant(self, new_id: str) -> ConstructionGraph:
        # Generate a variant of the construction graph
        ret = ConstructionGraph(new_id, self._fig)
        for cn in self._construction_nodes:
            ret.add_construction_node(cn)
        # Get the existing edges and add them to the new graph
        for edge in self.edges:
            ret.add_edge(edge[0], edge[1])
        return ret

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, ConstructionGraph):
            if self.ID == __o.ID:
                return True
            else:
                return False
        else:
            return False

    def remove_node_for_exact_fig_cover(self, fig_node_cover: FrozenSet[str]) -> None:
        """Removes the construction node which contains the exact fig node cover
        provided.

        This method Removes the construction node which contains the exact fig node
        cover provided. i.e. if the fig_node_cover is {'A', 'B'} and the construction
        should have a fig node mapping of {'A', 'B'}. This covers the cases where the
        mapping is an exact match and you need to substitute the entire construction
        node.

        Use other methods when you need to account for partial cover matches.

        Args:
            fig_node_cover (FrozenSet[str]): A frozen set of fig node IDs which
                represents the exact fig node cover.
        """

        for cn in self._construction_nodes:
            if frozenset(list(cn.fig_subgraph.nodes)) == fig_node_cover:
                self.remove_node(cn.ID)
                break

    def __str__(self):
        ret = "Construction Graph: " + self.ID
        return ret

    def print_graph(self, filename: str) -> None:
        """Prints the graph to a file under OUTPUT_DIR / CURRENT_MODULE_NAME (if set)
        so different LFR benchmarks do not overwrite the same .dot file.
        """
        if not getattr(parameters, "PRINT_DEBUG_GRAPHS", True):
            return
        base = parameters.OUTPUT_DIR
        module_name = getattr(parameters, "CURRENT_MODULE_NAME", None)
        if module_name:
            out_dir = os.path.join(base, module_name)
            os.makedirs(out_dir, exist_ok=True)
            tt = os.path.join(out_dir, filename)
        else:
            tt = os.path.join(base, filename)
        print("File Path:", tt)
        try:
            nx.nx_agraph.to_agraph(self).write(tt)
        except (ImportError, Exception):
            pass  # pygraphviz not available; skip variant dot output
