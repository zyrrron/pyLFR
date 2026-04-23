import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import networkx as nx
from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.FileStream import FileStream

from lfr.antlrgen.lfr.lfrXLexer import lfrXLexer
from lfr.antlrgen.lfr.lfrXParser import lfrXParser
from lfr.parameters import PREPROCESSOR_DUMP_FILE_NAME

# `import "..."` where the string may contain a bare basename ("foo.lfr"),
# a relative path ("subdir/foo.lfr") or an absolute path ("/abs/foo.lfr").
IMPORT_FILE_PATTERN = r"(`import\s+\"([^\"]+\.lfr)\")"

# Extracts "module <NAME>(" / "module <NAME>;" declarations.
# Mirrors grammar rule: moduledefinition: 'module' ID ('(' ioblock ')')? ';'
MODULE_NAME_PATTERN = re.compile(
    r"^\s*module\s+([A-Za-z_][A-Za-z_0-9]*)\s*(?:\(|;)",
    re.MULTILINE,
)


class PreProcessor:
    def __init__(self, file_list: List[str], lib_dir_list: List[str] = []) -> None:
        r"""Instantiates a new instance of the preprocessor.

        Args:
            file_list: top-level LFR files supplied by the user.
            lib_dir_list: directories scanned (recursively) for reusable
                ``.lfr`` files that can be pulled in via ``\`import "..."``.
        """
        self.resolved_paths: Dict[str, Path] = {}
        self.full_text: Dict[str, str] = {}
        self.text_dump = None
        # basename -> absolute path (legacy fast-path lookup)
        self._lib_file_list: Dict[str, str] = {}
        # directories, preserved for relative-path resolution
        self._lib_dirs: List[Path] = []

        print("Loading all LFR Files from lib Directories:")
        if lib_dir_list is not None:
            for dir_ref in lib_dir_list:
                print("-- Loading form path {}".format(dir_ref))
                path = Path(dir_ref).resolve()
                if not path.is_dir():
                    print(
                        "   (warning: {} is not an existing directory, skipping)".format(
                            path
                        )
                    )
                    continue
                self._lib_dirs.append(path)

                for file in path.rglob("*.lfr"):
                    path_object = Path(file)
                    full_path = path_object.resolve()
                    print("Storing into library: {}".format(full_path))
                    existing = self._lib_file_list.get(str(path_object.name))
                    if existing is not None and existing != str(full_path):
                        # Two files share the same basename; later wins, but we
                        # warn because `import "foo.lfr"` is ambiguous.
                        print(
                            "   (warning: duplicate basename {!r} shadows {} with {})".format(
                                path_object.name, existing, full_path
                            )
                        )
                    self._lib_file_list[str(path_object.name)] = str(full_path)

        for file_path in file_list:
            extension = Path(file_path).suffix
            if extension != ".lfr":
                print("Unrecognized file Extension")
                sys.exit()

            p = Path(file_path).resolve()
            self.__store_full_text(p)

    def check_syntax_errors(self) -> bool:
        """Checks if there are any syntax errors in the top-level input files.

        Returns:
            bool: True if there are syntax errors, False otherwise.
        """
        syntax_errors = 0
        for file_path in list(self.resolved_paths.values()):
            print("File: {}".format(file_path))
            finput = FileStream(str(file_path), encoding="utf-8")

            lexer = lfrXLexer(finput)

            stream = CommonTokenStream(lexer)

            parser = lfrXParser(stream)

            parser.skeleton()
            syntax_errors += parser.getNumberOfSyntaxErrors()

        return syntax_errors > 0

    def check_case_collisions(self, strict: bool = False) -> bool:
        r"""Warn when two ``.lfr`` files in the same directory have stems that
        differ only in letter case (e.g. ``aaa.lfr`` and ``aAA.lfr``).

        LFR itself is case-sensitive (the ANTLR lexer treats ``aaa`` and ``aAA``
        as distinct identifiers), so this never produces a semantic conflict at
        parse time. However, the compiler writes outputs as
        ``<module_name>_fromLFR.mint`` / ``.json``; on case-insensitive
        filesystems (default Windows NTFS, default macOS HFS+) the two
        output paths collide and one silently overwrites the other. Emitting
        this warning early lets projects catch the issue before a cross-OS
        move bites them.

        Args:
            strict: if True, a collision raises ``ValueError``; otherwise it is
                logged as a warning and compilation proceeds.

        Returns:
            True if no collisions were found, False otherwise.
        """
        from collections import defaultdict

        buckets: Dict[str, List[Path]] = defaultdict(list)
        seen: Set[Path] = set()
        for raw_handle in list(self.full_text.keys()) + list(
            self._lib_file_list.values()
        ):
            try:
                p = Path(raw_handle).resolve()
            except OSError:
                continue
            if p in seen:
                continue
            seen.add(p)
            if p.suffix != ".lfr":
                continue
            key = "{}::{}".format(str(p.parent), p.stem.lower())
            buckets[key].append(p)

        all_ok = True
        for _, paths in buckets.items():
            if len(paths) <= 1:
                continue
            all_ok = False
            names = sorted(p.name for p in paths)
            parent = paths[0].parent
            msg = (
                "LFR files {} in {!r} have stems that differ only in case; "
                "outputs will collide on case-insensitive filesystems "
                "(Windows NTFS, default macOS HFS+). "
                "Consider renaming to distinct stems.".format(names, str(parent))
            )
            if strict:
                raise ValueError("LFR naming convention violation: " + msg)
            print("WARNING: " + msg, file=sys.stderr)

        return all_ok

    def check_filename_module_convention(self, strict: bool = False) -> bool:
        r"""Verify that every loaded file declares exactly one module whose
        name equals the file stem (the ``Valve`` in ``Valve.lfr``).

        The "one file == one module == one function name" convention makes
        cross-file reuse unambiguous (``\`import "Valve.lfr"`` +
        ``Valve v1(...)``).

        Args:
            strict: if True, a violation raises ``ValueError``; otherwise it is
                logged as a warning and compilation proceeds.

        Returns:
            True if every file satisfies the convention, False otherwise.
        """
        all_ok = True
        for file_handle, text in self.full_text.items():
            stem = Path(file_handle).stem
            names = MODULE_NAME_PATTERN.findall(text)

            if len(names) == 0:
                msg = "file {!r} declares no `module ...` block".format(file_handle)
            elif len(names) > 1:
                msg = (
                    "file {!r} declares multiple modules {}; "
                    "convention requires exactly one module per file".format(
                        file_handle, names
                    )
                )
            elif names[0] != stem:
                msg = (
                    "file {!r} declares `module {}` but convention requires "
                    "`module {}` (module name must match file stem)".format(
                        file_handle, names[0], stem
                    )
                )
            else:
                continue

            all_ok = False
            if strict:
                raise ValueError("LFR naming convention violation: " + msg)
            print("WARNING: " + msg, file=sys.stderr)

        return all_ok

    def _resolve_import(
        self, import_spec: str, importing_file_handle: str
    ) -> Optional[Path]:
        r"""Resolve ``\`import "<spec>"`` to an absolute path.

        Resolution order:
          1. Absolute path -> use as-is if it exists.
          2. Path containing a directory component -> try, in order,
             (a) relative to the directory of the importing file,
             (b) relative to each preload / library directory.
          3. Bare basename -> try, in order,
             (a) the preloaded library index (by basename),
             (b) the directory of the importing file.
        """
        p = Path(import_spec)

        if p.is_absolute():
            return p.resolve() if p.exists() else None

        importer_dir = self.resolved_paths[importing_file_handle].parent
        has_dir_component = len(p.parts) > 1

        if has_dir_component:
            candidate = (importer_dir / p).resolve()
            if candidate.exists():
                return candidate
            for lib_dir in self._lib_dirs:
                candidate = (lib_dir / p).resolve()
                if candidate.exists():
                    return candidate
            return None

        basename = p.name
        if basename in self._lib_file_list:
            return Path(self._lib_file_list[basename]).resolve()
        candidate = (importer_dir / basename).resolve()
        if candidate.exists():
            return candidate
        return None

    def process(
        self, preprocesser_dump_path: Path = Path(f"./{PREPROCESSOR_DUMP_FILE_NAME}")
    ) -> None:
        r"""Resolve ``\`import`` directives, inline dependencies, and dump
        the concatenated LFR source so the ANTLR pass sees every module in
        one stream.

        Transitive imports are followed: if a library file itself imports
        another library file, the second one is pulled in automatically.

        Args:
            preprocesser_dump_path: where to write the concatenated dump.

        Raises:
            Exception: when an import cannot be resolved.
        """
        dep_graph = nx.DiGraph()
        for file_handle in self.full_text:
            dep_graph.add_node(file_handle)

        # BFS over all files (top-level + transitively imported) so nested
        # imports in library files are also followed.
        pending: List[str] = list(self.full_text.keys())
        processed: Set[str] = set()

        while pending:
            file_handle = pending.pop(0)
            if file_handle in processed:
                continue
            processed.add(file_handle)

            text = self.full_text[file_handle]
            find_results = re.findall(IMPORT_FILE_PATTERN, text)

            for result in find_results:
                import_spec = result[1]
                delete_string = result[0]

                resolved_path = self._resolve_import(import_spec, file_handle)
                if resolved_path is None:
                    raise Exception(
                        "Could not resolve `import {!r} in {} (searched "
                        "importing file's dir and {} library dir(s))".format(
                            import_spec, file_handle, len(self._lib_dirs)
                        )
                    )

                import_handle = resolved_path.name

                if import_handle not in dep_graph.nodes:
                    existing = self.resolved_paths.get(import_handle)
                    if existing is not None and existing.resolve() != resolved_path:
                        print(
                            "WARNING: basename collision while resolving `import "
                            "{!r}: {} vs {} (using newly resolved path)".format(
                                import_spec, existing, resolved_path
                            ),
                            file=sys.stderr,
                        )
                    print("Using Library Design at Path: {0}".format(resolved_path))
                    self.__store_full_text(resolved_path)
                    dep_graph.add_node(import_handle)
                    pending.append(import_handle)

                dep_graph.add_edge(file_handle, import_handle)

                text = text.replace(delete_string, "// Removed import")

            self.full_text[file_handle] = text

        try:
            ordering = list(reversed(list(nx.topological_sort(dep_graph))))
        except nx.NetworkXUnfeasible as exc:
            raise Exception(
                "Circular `import dependency detected: {}".format(
                    list(nx.find_cycle(dep_graph))
                )
            ) from exc

        final_dump = ""
        print(ordering)
        for file_handle in ordering:
            final_dump += "// Dumping File - {}\n\n\n".format(file_handle)
            final_dump += self.full_text[file_handle]
            final_dump += "\n\n\n\n\n"

        file = open(preprocesser_dump_path, "w")
        file.write(final_dump)
        file.close()

    def __store_full_text(self, file_path: Path):
        """Stores the full text of the given file into the preprocessor store.

        Args:
            file_path (Path): Path object of the file
        """
        print("Input Path: {0}".format(file_path))
        file = open(file_path, mode="r")

        all_of_the_file_text = file.read()

        file.close()

        self.resolved_paths[file_path.name] = file_path
        self.full_text[file_path.name] = all_of_the_file_text
