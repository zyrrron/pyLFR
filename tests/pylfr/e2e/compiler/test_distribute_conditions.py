from pathlib import Path

import pytest

from lfr import api


def _synthesize_distribute(tmp_path: Path, filename: str, body: str):
    test_file = tmp_path / filename
    test_file.write_text(
        body,
        encoding="utf-8",
    )
    return api.synthesize_module(
        input_path=test_file,
        no_annotations_flag=True,
        print_fig=False,
    )


def test_distribute_condition_signal_logical_and_compiles(tmp_path: Path):
    listener = _synthesize_distribute(
        tmp_path,
        "dist_signal_and.lfr",
        """module dist_signal_and(
    finput a, b,
    foutput y,
    control c1, c2
);

distribute@(c1, c2)
begin
    if (c1 && c2)
        y <= a;
    else
        y <= b;
end

endmodule
""",
    )

    assert listener.success is True
    assert listener.currentModule is not None
    assert len(listener.currentModule.FIG.state_tables) == 1
    state_table = listener.currentModule.FIG.state_tables[0]
    assert len(state_table._connectivity_states) == 4


def test_distribute_condition_chained_logical_expression_compiles(tmp_path: Path):
    listener = _synthesize_distribute(
        tmp_path,
        "dist_chain_expr.lfr",
        """module dist_chain_expr(
    finput a, b,
    foutput y,
    control c1, c2, c3
);

distribute@(c1, c2, c3)
begin
    if (c1 && c2 || c3)
        y <= a;
    else
        y <= b;
end

endmodule
""",
    )

    assert listener.success is True
    assert listener.currentModule is not None
    assert len(listener.currentModule.FIG.state_tables) == 1
    state_table = listener.currentModule.FIG.state_tables[0]
    assert len(state_table._connectivity_states) == 8


def test_distribute_condition_parenthesized_expression_compiles(tmp_path: Path):
    listener = _synthesize_distribute(
        tmp_path,
        "dist_parenthesized_expr.lfr",
        """module dist_parenthesized_expr(
    finput a, b,
    foutput y,
    control c1, c2, c3
);

distribute@(c1, c2, c3)
begin
    if ((c1 && c2) || c3)
        y <= a;
    else
        y <= b;
end

endmodule
""",
    )

    assert listener.success is True
    assert listener.currentModule is not None
    assert len(listener.currentModule.FIG.state_tables) == 1
    state_table = listener.currentModule.FIG.state_tables[0]
    assert len(state_table._connectivity_states) == 8


def test_distribute_condition_signal_width_mismatch_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="signal widths do not match"):
        _synthesize_distribute(
            tmp_path,
            "dist_width_mismatch.lfr",
            """module dist_width_mismatch(
    finput a, b,
    foutput y,
    control [0:1] route,
    control sel
);

distribute@(route, sel)
begin
    if (route == sel)
        y <= a;
    else
        y <= b;
end

endmodule
""",
        )
