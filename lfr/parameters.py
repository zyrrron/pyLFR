import pathlib

import lfr

# Global Variables
LFR_DIR = pathlib.Path(lfr.__file__).parent.parent.absolute()
LIB_DIR = LFR_DIR.joinpath("library")
OUTPUT_DIR = LFR_DIR.joinpath("output")
PREPROCESSOR_DUMP_FILE_NAME = "pre_processor_dump.lfr"
# Set during compile to module name (e.g. flow_only_demo) so each LFR gets its own output subfolder
CURRENT_MODULE_NAME = None
# When False, skip FIG/construction .dot and .pdf (only .mint and .json are written)
PRINT_DEBUG_GRAPHS = True
