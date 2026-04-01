"""
Defines a set of rule functions that return a Report
"""

import re
import logging

import networkx as nx
import xmlschema

from pathlib import Path

from avid_validator.common.archive import ValidationContext
from avid_validator.common.report import OptReport, fail, ok
from avid_validator.common import utils
from avid_validator.common.graph import TableNode

logger = logging.getLogger(__name__)


def require_dirs(ctx: ValidationContext, *names: str) -> OptReport:
    """
    Require directories
    """
    missing = [n for n in names if not (ctx.root / n).is_dir()]
    if missing:
        return fail(f"Missing required directories: {', '.join(missing)}")
    return ok()


def require_files(base: Path, *names: str) -> OptReport:
    """
    Require filenames in specified path
    """
    missing = [n for n in names if not (base / n).is_file()]
    if missing:
        return fail(f"Missing required files in {base.name}: {', '.join(missing)}")
    return ok()


def require_name_startswith(p: Path, prefix: str, msg: str) -> OptReport:
    """
    Require a path object to be prefixed by 'prefix'
    """
    return ok() if p.name.startswith(prefix) else fail(msg)


def require_dir_entries_max(base: Path, limit: int, msg: str) -> OptReport:
    """
    Require directory to contain at most 'limit' items
    """
    # Using iterdir avoids materializing full lists unless needed
    count = sum(1 for _ in base.iterdir())
    return ok() if count <= limit else fail(msg)


def require_numbered_folders(
    base: Path, pattern: str, start_at: int = 1, label: str = "folder"
) -> OptReport:
    """
    Require folders to be numbered starting at 1
    """
    rx = re.compile(pattern)
    ids = []
    for p in base.iterdir():
        if not p.is_dir():
            continue
        m = rx.match(p.name)
        if not m:
            return fail(f"{label} name '{p.name}' does not match {pattern}")
        ids.append(int(m.group(1)))
    if not ids:
        return fail(f"No {label}s found in {base}")
    if len(ids) != len(set(ids)):
        return fail(f"{label} names must be unique")
    if min(ids) != start_at:
        return fail(f"First {label} index must start with {start_at}")
    return ok()


def validate_xml_against_standard_schema(
    ctx: ValidationContext, xml_file: Path
) -> OptReport:
    """
    Validate an XML file against "standard" XSD schema file -- Here standard means it lies in Schemas/standard
    """
    xsd = ctx.schemas / "standard" / f"{xml_file.stem}.xsd"
    if not xsd.is_file():
        return fail(f"Missing schema for {xml_file.name}: {xsd}")
    try:
        utils.lazy_xml_validate(xml_file, xsd)
    except xmlschema.XMLSchemaValidationError as e:
        return fail(str(e.reason))
    return ok()


def require_node_connectivity(nodes: list[TableNode]) -> OptReport:
    """
    Require a node graph to be weakly connected -- Ignoring reference directions, all nodes are connected.
    """
    G = nx.DiGraph()

    # Add nodes and references
    for node in nodes:
        if not G.has_node(node.name):
            G.add_node(node.name)

        for ref in node.referenced_tables:
            if not G.has_node(ref):
                G.add_node(ref)

            G.add_edge(node.name, ref)

    # Check incoming/outgoing
    for n in G.nodes:
        if G.out_degree(n) == 0 and G.in_degree(n) == 0:
            return fail(f"{n} has no incomming or outgoing references!")

    if not nx.is_weakly_connected(G):
        comps = list(nx.weakly_connected_components(G))
        # comps is a list of sets of node names
        msg = "Table references has islands:\n" + "\n".join(
            f"- component {i+1} ({len(c)} nodes): {sorted(c)}"
            for i, c in enumerate(comps)
        )
        return fail(msg)

    return ok()
