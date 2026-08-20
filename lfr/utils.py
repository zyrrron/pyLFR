import json
import os
import re
import subprocess
from pathlib import Path
from typing import List

import networkx as nx
from pymint.mintdevice import MINTDevice

from lfr import parameters


def printgraph(
    graph: nx.Graph,
    filename: str,
    output_dir: Path = None,
    write_dot: bool = True,
) -> None:
    """Prints the graph in a .dot file and a .pdf file (if pygraphviz and dot are available).
    If CURRENT_MODULE_NAME is set, files go under OUTPUT_DIR/CURRENT_MODULE_NAME so each
    LFR benchmark has its own folder and files are not overwritten.

    Args:
        graph (nx.Graph): graph we need to print
        filename (str): base name of the file (without .dot; .dot is appended here)
        output_dir (Path, optional): Output folder path. If None, uses parameters.OUTPUT_DIR and optional subdir by module name.
        write_dot (bool): Keep the Graphviz .dot next to the PDF. Topology PDFs
            set this False so only ``*_fromLFR_topology.pdf`` remains.
    """
    if output_dir is None:
        output_dir = Path(parameters.OUTPUT_DIR)
        if getattr(parameters, "CURRENT_MODULE_NAME", None):
            output_dir = output_dir / parameters.CURRENT_MODULE_NAME
            output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    graph_copy = graph.copy(as_view=False)
    dot_path = Path.joinpath(output_dir, f"{filename}.dot")
    pdf_path = Path.joinpath(output_dir, f"{filename}.pdf")
    print("output:", output_dir)
    print("output:", dot_path)
    try:
        nx.nx_agraph.to_agraph(graph_copy).write(str(dot_path))
        dot_abs = str(dot_path.resolve())
        pdf_abs = str(pdf_path.resolve())
        # Avoid shell word-splitting on spaces/apostrophes in OUTPUT_DIR paths.
        subprocess.run(
            ["dot", "-Tpdf", dot_abs, "-o", pdf_abs],
            check=False,
            capture_output=True,
            text=True,
        )
        if not write_dot:
            try:
                dot_path.unlink()
            except OSError:
                pass
    except (ImportError, Exception):
        # pygraphviz or dot not available; skip FIG visualization
        pass


def get_ouput_path(filename: str) -> str:
    """Returns the path to the output file"""
    return os.path.join(parameters.OUTPUT_DIR, filename)


def serialize_netlist(output_path: Path, mint_device: MINTDevice) -> None:
    """Serializes the netlist to a json file"""

    # Generate the JSON file from the pyparchmint device
    json_data = mint_device.to_parchmint()
    json_string = json.dumps(json_data)
    # DIYCOMPONENT / sized BLACK BOX are first-class placeholders with real
    # length/width/height — still emit JSON. Only unsized legacy BLACK BOX
    # stubs without dimensions are blocked.
    if "BLACK BOX" in json_string and "DIYCOMPONENT" not in json_string:
        if "length=" not in json_string and '"length"' not in json_string:
            print("JSON not generated due to unsized custom BLACK BOX component")
            return
    file_path = output_path.joinpath(f"{mint_device.device.name}_fromLFR.json")
    json_file = open(file_path, "wt")
    json_file.write(json_string)
    json_file.close()


def print_netlist(output_path: Path, mint_device: MINTDevice) -> None:
    """Stores the device as a MINT file"""

    # Generate the MINT file from the pyparchmint device
    # Keep writer spacing intact; collapsing whitespace before ';' can
    # accidentally alter token boundaries needed by strict MINT parsing.
    minttext = mint_device.to_MINT()

    def modify_unsized_placeholder(match):
        # Only inject INSERT markers when the component has no size params yet.
        head = match.group(1)
        if re.search(r"\b(length|width)\s*=", head):
            return match.group(0)
        return f"{head} length=[INSERT LENGTH] width=[INSERT WIDTH];"

    if "BLACK BOX" in minttext and "length=" not in minttext:
        minttext = "# Please add default length and width to blackbox component\n" + minttext
    minttext = re.sub(r"(BLACK BOX\s+\S+)\s*;", modify_unsized_placeholder, minttext)

    if "REACTION CHAMBER" in minttext and "length=" not in minttext:
        minttext = "# Please add default length and width to reaction chamber component\n" + minttext
    minttext = re.sub(r"(REACTION CHAMBER\s+\S+)\s*;", modify_unsized_placeholder, minttext)


    mint_name = f"{mint_device.device.name}_fromLFR.mint"
    file_path = Path.joinpath(output_path, mint_name)
    mint_file = open(file_path, "wt")
    mint_file.write(minttext)
    mint_file.close()


def convert_list_to_str(lst: List) -> str:
    """Returns a string list formatted as a string

    Args:
        lst (List): list we need to convert into a string

    Returns:
        str: list formatted as a string
    """
    ret = "[{0}]".format(", ".join([str(i) for i in lst]))
    return ret
