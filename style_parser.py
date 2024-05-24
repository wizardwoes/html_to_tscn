from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import css_inline
from bs4 import BeautifulSoup

from godot import (
    ExtResourceGodot,
    FontFileGodot,
    GDScriptResource,
    NodeGodot,
    SceneGodot,
    ScriptFunction,
    Texture2DGodot,
)
from node_parser import Parser, make_rich_text_label
from scanner import HtmlScanner
from tag_token import TagCategory, Token


@dataclass
class HBoxContainer(NodeGodot):
    type: str = "HboxContainer"


# @dataclass
# class RichTextLabel(NodeGodot):
#     type: str = "RichTextLabel"


@dataclass
class LinkButton(NodeGodot):
    type: str = "LinkButton"


@dataclass
class LinkButtonExternal(NodeGodot):
    type: str = "LinkButton"


# def make_rich_text_label(name, text, extra_properties=None):
#     # figure out way to derive these properties from something else
#     properties = {
#         "layout_mode": 2,
#         "bbcode_enabled": True,
#         "fit_content": True,
#         "text": text,
#     }
#     if extra_properties:
#         properties.update(extra_properties)

#     return NodeGodot(name, type="RichTextLabel", properties=properties)


# # @dataclass
# # class TextureRect(NodeGodot):
# #     type: str = "TextureRect"


# def make_texture_rect(name, extra_properties=None):
#     # figure out way to derive these properties from something else
#     properties = {
#         "layout_mode": 2,
#         "size_flags_vertical": 3,
#         "expand_mode": 5,
#         "stretch_mode": 4,
#     }

#     if extra_properties:
#         properties.update(extra_properties)

#     return NodeGodot(name, type="TextureRect", properties=properties)


def on_link_button_pressed_func(method_name, path_to_node):
    # example
    # func _on_button_pressed():
    #   Global.goto_scene(get_path(),"res://test.tscn")
    name = method_name
    new_path = f"res://{path_to_node}.tscn"
    code = [f'Global.goto_scene("{new_path}")']
    return ScriptFunction(name, code)


def attach_resource(node: NodeGodot, resource) -> None:
    resource.path = node.name
    node.resources.append(resource)


@dataclass
class MarginContainer(NodeGodot):
    type: str = "MarginContainer"

    # turn this into a huge map of css to godot options ig
    @property
    def padding_map(self):
        return {
            "padding-left": "theme_override_constants/margin_left",
            "padding-top": "theme_override_constants/margin_top",
            "padding-right": "theme_override_constants/margin_right",
            "padding-bottom": "theme_override_constants/margin_bottom",
        }

    @property
    def margin_map(self):
        return {
            "margin-left": "theme_override_constants/margin_left",
            "margin-top": "theme_override_constants/margin_top",
            "margin-right": "theme_override_constants/margin_right",
            "margin-bottom": "theme_override_constants/margin_bottom",
        }

    def __post_init__(self):
        # self.properties = self._map_padding_values()
        # self.properties.update(self._map_margin_values())
        self.properties.update(self._map_padding_values())
        # self.properties.update(self._map_margin_values())
        self.properties.update(
            {
                "layout_mode": 2,
                "size_flags_horizontal": 3,
                "size_flags_vertical": 3,
            }
        )
        self.update_margins()

    def _map_padding_values(self) -> dict:
        properties = {}
        # iterate through map and set our properties if found
        for k, v in self.padding_map.items():
            if pval := self.properties.get(k):
                properties[v] = pval

        if pval := self.properties.get("padding"):
            match pval.split(" "):
                case [all_pad]:
                    for v in self.padding_map.values():
                        properties[v] = all_pad

                case [top_bottom, left_right]:
                    for k in [
                        "theme_override_constants/margin_left",
                        "theme_override_constants/margin_right",
                    ]:
                        properties[k] = left_right

                    for k in [
                        "theme_override_constants/margin_top",
                        "theme_override_constants/margin_bottom",
                    ]:
                        properties[k] = top_bottom

                case [top, left_right, bottom]:
                    for k in [
                        "theme_override_constants/margin_left",
                        "theme_override_constants/margin_right",
                    ]:
                        properties[k] = left_right

                    properties["theme_override_constants/margin_top"] = top
                    properties["theme_override_constants/margin_bottom"] = bottom

                case [top, right, bottom, left]:
                    properties["theme_override_constants/margin_left"] = left
                    properties["theme_override_constants/margin_top"] = top
                    properties["theme_override_constants/margin_right"] = right
                    properties["theme_override_constants/margin_bottom"] = bottom

        return properties

    def _map_margin_values(self) -> dict:
        properties = {}
        for k, v in self.margin_map.items():
            if pval := self.properties.get(k):
                properties[v] = pval

        if pval := self.properties.get("margin"):
            match pval.split(" "):
                case [all_pad]:
                    for v in self.margin_map.values():
                        properties[v] = all_pad

                case [top_bottom, left_right]:
                    for k in [
                        "theme_override_constants/margin_left",
                        "theme_override_constants/margin_right",
                    ]:
                        properties[k] = left_right

                    for k in [
                        "theme_override_constants/margin_top",
                        "theme_override_constants/margin_bottom",
                    ]:
                        properties[k] = top_bottom

                case [top, left_right, bottom]:
                    for k in [
                        "theme_override_constants/margin_left",
                        "theme_override_constants/margin_right",
                    ]:
                        properties[k] = left_right

                    properties["theme_override_constants/margin_top"] = top
                    properties["theme_override_constants/margin_bottom"] = bottom

                case [top, right, bottom, left]:
                    properties["theme_override_constants/margin_left"] = left
                    properties["theme_override_constants/margin_top"] = top
                    properties["theme_override_constants/margin_right"] = right
                    properties["theme_override_constants/margin_bottom"] = bottom

        return properties

    def update_margins(self) -> None:
        # ok this is side-effect heavy BUT
        # script = GDScriptResource(source=self.type)
        fragments = []

        for k, v in self.padding_map.items():
            if pval := self.properties.get(v):
                match self.convert_padding_to_godot(pval):
                    case ("script", _ as val):
                        m = v.split("/")[-1]
                        frag = self.render_margin_fragment(m, val)
                        fragments.extend(frag)
                        del self.properties[v]
                    case ("int", _ as val):
                        self.properties[v] = val

        # # running into issue where option is already set
        # for k, v in self.margin_map.items():
        #     if pval := self.properties.get(v):
        #         try:
        #             match self.convert_padding_to_godot(pval):
        #                 case ("script", _ as val):
        #                     m = val.split("/")[-1]
        #                     frag = self.render_margin_fragment(m, val)
        #                     script.ready.extend(frag)
        #                     del self.properties[v]
        #                 case ("int", _ as val):
        #                     self.properties[v] = val
        #         except TypeError:
        #             print("is value already set?", self.properties.get(v), pval)

        if fragments:
            script = make_ready_script(self, fragments)
            self.add_script(script)

    # this may be used in other css values than just padding
    def convert_padding_to_godot(self, pad_value) -> tuple:
        if "px" in pad_value:
            return ("int", int(pad_value[:-2]))
        if "%" in pad_value:
            calc = int(pad_value[:-1]) * 0.01
            return ("int", calc)
        if "vh" in pad_value:
            calc = int(pad_value[:-2]) * 0.01
            pad_str = f"{calc} * get_viewport().get_visible_rect().size.x"
            return ("script", pad_str)
        if "vw" in pad_value:
            calc = int(pad_value[:-2]) * 0.01
            pad_str = f"{calc} * get_viewport().get_visible_rect().size.y"
            return ("script", pad_str)
        if "auto" in pad_value:
            return ("str", "auto value")
        if "rem" in pad_value:
            return ("str", "rem value")
        if "em" in pad_value:
            return ("str", "em value")

        return ("int", int(pad_value))

    def render_margin_fragment(self, margin_dir, margin_val):
        define_str = f"var {margin_dir} = {margin_val}"
        add_theme_str = f'add_theme_constant_override("{margin_dir}", {margin_dir})'

        return [define_str, add_theme_str]


def render_connection_fragment(var_name, node_path, signal, method_name):
    define_str = f'var {var_name} = self.get_node("{node_path}")'
    connect_str = f"{var_name}.{signal}.connect({method_name})"

    return [define_str, connect_str]


def make_ready_script(node, fragments):
    func = ScriptFunction("_ready", fragments)
    script = GDScriptResource(source=node.type)
    script.add_function(func)

    return script


@dataclass
class TokenNode:
    token: Token
    node: NodeGodot


@dataclass
class StyleParser:
    token_nodes: list[TokenNode] = field(default_factory=list)
    root: TokenNode = None
    scope: list = field(default_factory=list)

    def parse(self) -> list[NodeGodot]:
        nodes = []

        while not self.is_at_end():
            node = self.make_node()
            nodes.append(node)

        return nodes

    def _parse(self, token_node: TokenNode, nodes: list[NodeGodot]) -> list[NodeGodot]:
        p_style = self.tag_style_to_dict(token_node.token.attrs)
        self.scope.append(p_style)

        if children := token_node.node.children:
            self.scope.append(p_style)
            # iterate through styles and apply them

        self.scope.pop()

        pass
    
    def apply_style(self, token_node: TokenNode) -> NodeGodot:
        print("style applied", self.scope[-1])
        return token_node.node

    def tag_style_to_dict(self, tag):
        styled = {}
        if styles := tag.get("style"):
            for s in styles.strip().split(";"):
                try:
                    k, v = s.split(": ")
                    styled[k] = v
                except ValueError:
                    pass

        return styled

def tag_style_to_dict(tag):
    styled = {}
    if styles := tag.get("style"):
        for s in styles.strip().split(";"):
            try:
                k, v = s.split(": ")
                styled[k] = v
            except ValueError:
                pass

    return styled


if __name__ == "__main__":
    test_doc = Path("src_html\glas\page-90\index.html")
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

    scanner = HtmlScanner(soup.html.body.find(id="content"))
    tokens = scanner.scan_tokens()

    for token in tokens:
        styled = tag_style_to_dict(token.attrs)
        print("token type", token.name)
        print("stlyed?", styled)

    # parser = Parser(tokens, root_node=root_node)
    # token_nodes = parser.parse()

    # style_parser = StyleParser()
    # nodes = style_parser.parse()

    # for child in nodes:
    #     root_node.add_child(child)

    # # resources.extend(scripts)

    # scene = SceneGodot(root_node)
