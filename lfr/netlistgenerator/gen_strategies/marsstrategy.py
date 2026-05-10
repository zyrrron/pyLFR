from __future__ import annotations

from lfr.fig.fluidinteractiongraph import FluidInteractionGraph
from lfr.netlistgenerator.gen_strategies.genstrategy import GenStrategy


class MarsStrategy(GenStrategy):
    def __init__(self, fig: FluidInteractionGraph) -> None:
        super().__init__("mars", fig)
