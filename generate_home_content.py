import argparse

from pathlib import Path
from bs4 import BeautifulSoup
import css_inline

from scanner import HtmlScanner

# need a better way of doing collect_ext_resources, collect_node_scripts
from node_parser import Parser
from render_godot import SceneWriter

from godot import (
    NodeGodot,
    SceneGodot,
)

arg_parser = argparse.ArgumentParser(description="make a scene from the <content>")
arg_parser.add_argument("--src", help="source html")
arg_parser.add_argument("--outfile")
arg_parser.add_argument("--outdir")


def main(args):
    test_doc = Path(args.src)
    inliner = css_inline.CSSInliner()

    with open(test_doc, "r", encoding="utf-8") as f:
        inlined = inliner.inline(f.read())

    soup = BeautifulSoup(inlined, features="lxml")

    # mostly works
    root_properties = {
        "size_flags_horizontal": 3,
        "size_flags_vertical": 3,
        # "anchors_preset": 15,
        # "anchor_right": 1.0,
        # "anchor_bottom": 1.0,
        # "horizontal_scroll_mode": 0,
        # "vertical_scroll_mode": 2,
    }

    # remove the head tag
    soup.html.head.extract()

    # remove the navbar (for now)
    soup.html.body.nav.extract()

    # remove the footer (for now)
    soup.html.body.footer.extract()

    root_node = NodeGodot("content", "VBoxContainer", properties=root_properties)

    scanner = HtmlScanner(soup.html.body.find(id="main"))
    tokens = scanner.scan_tokens()

    parser = Parser(tokens, root_node=root_node)
    nodes = parser.parse()

    for child in nodes:
        root_node.add_child(child)

    scene = SceneGodot(root_node)

    outfile = f"home"
    base_dir = Path(f"godot_output\{outfile}")

    writer = SceneWriter(scene, base_dir, outfile)
    writer.write_out_scene()
    writer.write_out_resources()

if __name__ == "__main__":
    args = arg_parser.parse_args()
    main(args)