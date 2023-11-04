from pathlib import Path
from bs4 import BeautifulSoup
import css_inline

from scanner import HtmlScanner

# need a better way of doing collect_ext_resources, collect_node_scripts
from node_parser import (
    Parser,
    collect_ext_resources,
    collect_node_scripts,
)

from render_godot import SceneWriter

from godot import NodeGodot, SceneGodot, ScriptFunction, GDScriptResource


def setup_ready_script():
    script = GDScriptResource()

    extra_ready_lines = [
        "self.get_node(content_sibling).add_sibling(content_scene)",
        "Global.on_internal_link_press.connect(_on_internal_link_press)",
    ]

    ready_func = ScriptFunction("_ready", extra_ready_lines)
    script.add_function(ready_func)

    # set up our callable
    # func _on_internal_link_press() -> void:
    #     self.scroll_vertical = scrollbar.min_value
    callable_func = ScriptFunction(
        "_on_internal_link_press", ["self.scroll_vertical = scrollbar.min_value"]
    )
    script.add_function(callable_func)

    # set up our onready vars
    script.onready["scrollbar"] = f'$".".get_v_scroll_bar()'
    script.onready["content_sibling"] = f'\"body-margin/body/navbar-margin\"'
    script.onready["content_scene"] = f'preload("home/home.tscn").instantiate()'

    return script


if __name__ == "__main__":
    test_doc = Path("src_html\wizard woes.html")
    inliner = css_inline.CSSInliner()

    with open(test_doc, "r", encoding="utf-8") as f:
        inlined = inliner.inline(f.read())

    soup = BeautifulSoup(inlined, features="lxml")

    # mostly works
    root_properties = {
        "size_flags_horizontal": 3,
        "size_flags_vertical": 3,
        "anchors_preset": 15,
        "anchor_right": 1.0,
        "anchor_bottom": 1.0,
        "horizontal_scroll_mode": 0,
        "vertical_scroll_mode": 2,
    }

    # remove the head tag
    soup.html.head.extract()
    soup.html.body.find(id="main").extract()

    # only need the navbar
    # soup.html.body.find(id="content").extract()

    root_node = NodeGodot("HtmlNode", "ScrollContainer", properties=root_properties)

    # Global.on_internal_link_press.connect(_on_internal_link_press)

    script = setup_ready_script()
    script.source = root_node.type

    root_node.add_script(script)

    scanner = HtmlScanner(soup.html)
    tokens = scanner.scan_tokens()

    parser = Parser(tokens, root_node=root_node)
    nodes = parser.parse()

    for child in nodes:
        root_node.add_child(child)

    scene = SceneGodot(root_node)

    outfile = Path("main")
    base_dir = Path("godot_output")

    writer = SceneWriter(scene, base_dir, outfile)
    writer.write_out_scene()
    writer.write_out_resources()
