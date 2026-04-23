import json
import os
import re
from pathlib import Path
from typing import List

import networkx as nx
from pymint.mintdevice import MINTDevice

from lfr import parameters


def printgraph(graph: nx.Graph, filename: str, output_dir: Path = None) -> None:
    """Prints the graph in a .dot file and a .pdf file (if pygraphviz and dot are available).
    If CURRENT_MODULE_NAME is set, files go under OUTPUT_DIR/CURRENT_MODULE_NAME so each
    LFR benchmark has its own folder and files are not overwritten.

    Args:
        graph (nx.Graph): graph we need to print
        filename (str): base name of the file (without .dot; .dot is appended here)
        output_dir (Path, optional): Output folder path. If None, uses parameters.OUTPUT_DIR and optional subdir by module name.
    """
    if output_dir is None:
        output_dir = Path(parameters.OUTPUT_DIR)
        if getattr(parameters, "CURRENT_MODULE_NAME", None):
            output_dir = output_dir / parameters.CURRENT_MODULE_NAME
            output_dir.mkdir(parents=True, exist_ok=True)
    graph_copy = graph.copy(as_view=False)
    dot_path = Path.joinpath(output_dir, f"{filename}.dot")
    pdf_path = Path.joinpath(output_dir, f"{filename}.pdf")
    print("output:", output_dir)
    print("output:", dot_path)
    try:
        nx.nx_agraph.to_agraph(graph_copy).write(str(dot_path))
        os.system(f"dot -Tpdf {str(dot_path.absolute())} -o {str(pdf_path.absolute())}")
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
    if "BLACK BOX" in json_string:
        print("JSON not generated due to custom component")
        return
    file_path = output_path.joinpath(f"{mint_device.device.name}_fromLFR.json")
    json_file = open(file_path, "wt")
    json_file.write(json_string)
    json_file.close()


def print_netlist(output_path: Path, mint_device: MINTDevice) -> None:
    """Stores the device as a MINT file"""

    # Generate the MINT file from the pyparchmint device
    minttext = re.sub(r'\s+;', ';', mint_device.to_MINT())

    if "BLACK BOX" in minttext:
        minttext = "# Please add default length and width to blackbox component\n" + minttext

    def modify_black_box(match):
        return f"{match.group(1)} length=[INSERT LENGTH] width=[INSERT WIDTH];"

    minttext = re.sub(r"(BLACK BOX\s+\S+)\s*;", modify_black_box, minttext)

    if "REACTION CHAMBER" in minttext:
        minttext = "# Please add default length and width to reaction chamber component\n" + minttext

    minttext = re.sub(r"(REACTION CHAMBER\s+\S+)\s*;", modify_black_box, minttext)


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
