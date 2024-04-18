#!/usr/bin/env python3

# Copyright (c) 2024 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

"""
Tool to find differences autonomous systems of Bitcoin nodes ...

TODO:
Tool to convert a compact-serialized UTXO set to a SQLite3 database.
The input UTXO set can be generated by Bitcoin Core with the `dumptxoutset` RPC:
$ bitcoin-cli dumptxoutset ~/utxos.dat
The created database contains a table `utxos` with the following schema:
(txid TEXT, vout INT, value INT, coinbase INT, height INT, scriptpubkey TEXT)
"""

import argparse
import ipaddress
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import asmap
from asmap import net_to_prefix
from asmap_tool import load_file


@dataclass
class Node:
    """Data class representing a node."""

    last_seen: int
    address: str
    port: int


def parse_args():
    """Parse command-line arguments."""
    # parser = argparse.ArgumentParser()
    #     description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    # )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "node_addresses_file",
        help="node address file (generated with `getnodeaddresses 0` RPC)",
        type=Path,
    )
    parser.add_argument(
        "previous_asmap_file",
        help="first asmap file",
        type=Path,
    )
    parser.add_argument(
        "current_asmap_file",
        help="second asmap file",
        type=Path,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="show details about each UTXO"
    )

    args = parser.parse_args()

    def check_input(file: Path):
        """Run sanity checks on input files."""
        if not file.exists():
            print(f"Error: input '{file}' doesn't exist.")
            sys.exit(1)
        if not file.is_file():
            print(f"Error: input '{file}' isn't a file.")
            sys.exit(1)

    # for file in [arg for arg in args if isinstance(arg, Path)]:
    #     check_input(file)
    for file in [
        args.node_addresses_file,
        args.previous_asmap_file,
        args.current_asmap_file,
    ]:
        check_input(file)

    return args


def get_clearnet_nodes(filepath: Path) -> list[Node]:
    """Parse node address file and return a list of ipv4/ipv6 nodes."""
    with open(filepath, "r", encoding="ascii") as f:
        data = json.load(f)
    nodes = []
    for entry in data:
        if entry["network"] not in ["ipv4", "ipv6"]:
            continue
        node = Node(entry["time"], entry["address"], entry["port"])
        nodes.append(node)
    print(f"Extracted {len(nodes)} clearnet nodes from {filepath}.")
    return nodes


def read_asmap(filepath: Path):
    """Read compressed AS map file and return AS map."""

    with open(filepath, "rb") as file:
        data = load_file(file)
    print(f"Loaded ASMap data from {filepath} (date type = {type(data)}).")
    return data
    # try:
    #     data = filepath.read_text(encoding="ASCII")
    #     print(f"[verbose] '{filepath}' is ascii file. Returning.")
    #     return data
    # except UnicodeDecodeError:
    #     print(
    #         f"[verbose] '{filepath}' is non-ascii file. Trying to decode binary asmap..."
    #     )
    #     try:
    #         bin_data = filepath.read_bytes()
    #         data = asmap.ASMap.from_binary(bin_data)
    #         print(f"[verbose] Successfully decoded ASMap in '{filepath}'.")
    #     except ValueError:
    #         print(f"[verbose] Could not decod ASMap in '{filepath}'.")
    #         print(f"Error: Unsupported format '{filepath}'")
    #         sys.exit(1)
    #
    # return data


def compare_asmaps(asmap_prev, asmap_cur, nodes: list[Node], age: int = 0):
    """Comapre AS maps and print differences."""
    # TEST

    # if age:
    #     print(f"Filtering nodes with age > {age} days.")
    #     ...

    # def compare_asmap_threshold(...)
    #

    epoch_now = int(time.time())
    thresholds = {
        "all": 0,
        "last week": epoch_now - 7 * 24 * 60 * 60,
        "last day": epoch_now - 24 * 60 * 60,
        "last hour": epoch_now - 60 * 60,
    }

    for thres_name, thres_epoch in thresholds.items():
        nodes_changed = 0
        nodes_total = 0
        for node in nodes:
            if node.last_seen < thres_epoch:
                continue
            nodes_total += 1
            prefix = net_to_prefix(ipaddress.ip_network(node.address))
            if asmap_prev.lookup(prefix) != asmap_cur.lookup(prefix):
                nodes_changed += 1
        if nodes_total == 0:
            print(f"horizon={thres_name}, total={nodes_total}")
            continue

        nodes_changed_share = nodes_changed / nodes_total
        print(
            f"horizon={thres_name}, total={nodes_total}, changed={nodes_changed}, share={100*nodes_changed_share:.1f}%"
        )


def main():
    """XXX TODO Main function to demonstrate script functionality."""
    args = parse_args()

    nodes = get_clearnet_nodes(args.node_addresses_file)
    asmap_prev = read_asmap(args.previous_asmap_file)
    asmap_cur = read_asmap(args.current_asmap_file)

    compare_asmaps(asmap_prev, asmap_cur, nodes)

    print(args)
    print("Hello, world!")


if __name__ == "__main__":
    main()
