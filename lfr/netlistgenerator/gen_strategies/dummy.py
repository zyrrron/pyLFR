from lfr.fig.fluidinteractiongraph import FluidInteractionGraph
from lfr.netlistgenerator.gen_strategies.genstrategy import GenStrategy


class DummyStrategy(GenStrategy):
    def __init__(
        self,
        fig: FluidInteractionGraph,
        strategy_name: str = "mlsi",
    ) -> None:
        super().__init__(strategy_name, fig)
