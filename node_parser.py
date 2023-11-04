from dataclasses import dataclass
from urllib.parse import urlparse

from tag_token import Token, TagCategory
from godot import (
    NodeGodot,
    ConnectionGodot,
    ScriptFunction,
    GDScriptResource,
    ExtResourceGodot,
    Texture2DGodot,
    FontFileGodot,
)


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


def make_rich_text_label(name, text, extra_properties=None):
    # figure out way to derive these properties from something else
    properties = {
        "layout_mode": 2,
        "bbcode_enabled": True,
        "fit_content": True,
        "text": text,
    }
    if extra_properties:
        properties.update(extra_properties)

    return NodeGodot(name, type="RichTextLabel", properties=properties)


# @dataclass
# class TextureRect(NodeGodot):
#     type: str = "TextureRect"


def make_texture_rect(name, extra_properties=None):
    # figure out way to derive these properties from something else
    properties = {
        "layout_mode": 2,
        "size_flags_vertical": 3,
        "expand_mode": 5,
        "stretch_mode": 4,
    }

    if extra_properties:
        properties.update(extra_properties)

    return NodeGodot(name, type="TextureRect", properties=properties)


def on_link_button_pressed_func(method_name, path_to_node):
    # example
    # func _on_button_pressed():
    #   Global.goto_scene(get_path(),"res://test.tscn")
    name = method_name
    new_path = f"res://{path_to_node}.tscn"
    code = [f'Global.goto_scene("{new_path}")']
    return ScriptFunction(name, code)


def attach_connection(node: NodeGodot, connection: ConnectionGodot) -> None:
    node.connections.append(connection)


def collect_ext_resources(node: NodeGodot, resources=None) -> list[ExtResourceGodot]:
    for child in node.children:
        if resource := child.resources:
            resources.extend(resource)

        collect_ext_resources(child, resources)

    return resources


def collect_node_scripts(node: NodeGodot, scripts=None) -> list[ExtResourceGodot]:
    for child in node.children:
        if script := child.script:
            scripts.append(script)

        collect_node_scripts(child, scripts)

    return scripts


def collect_connections(node: NodeGodot, connections=None) -> list[ConnectionGodot]:
    for child in node.children:
        if connection := child.connections:
            for cxn in connection:
                node_parent = child.handle_parent_text()
                cxn.from_node = node_parent + "/" + cxn.from_node

            connections.extend(connection)

        collect_connections(child, connections)

    return connections


def render_script(script: GDScriptResource) -> str:
    ready = "\n".join([f"\t{line}" for line in script.ready])
    # [sub_resource type="GDScript" id="GDScript_x1emt"]
    return (
        f"extends {script.source}\n"
        f"\n\n\n"
        f"# Called when the node enters the scene tree for the first time.\n"
        f"func _ready():\n"
        f"{ready}\n\n"
        f"func _process(delta):\n"
        f"\tpass\n"
    )


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


class Parser:
    def __init__(self, tokens, root_node=None) -> None:
        self.tokens = tokens
        self.current = 0
        self.root_node = root_node

    def parse(self) -> list[NodeGodot]:
        nodes = []

        while not self.is_at_end():
            node = self.make_node()
            nodes.append(node)

        return nodes

    def make_node(self) -> NodeGodot:
        if self.match(TagCategory.HEAD):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                node.add_child(child)

            return node

        if self.match(TagCategory.BODY):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.NAV):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            # need to figure out better way to not overwrite
            # self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.FOOTER):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            # print("foot node", tk_node.node)
            # self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.DIV):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_style_to_node(tk_node)
            self.apply_class_options_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.A):
            # need to handle if an internal link vs a real external link

            link_attrs = self.link_attributes()

            link_prop = {"unique_name_in_owner": True, "size_flags_horizontal": 0}
            # this could be done better
            match link_attrs:
                case {"uri": _ as uri}:
                    link_prop["uri"] = uri
                    node = LinkButtonExternal("link", properties=link_prop)
                case {"name": "", "link_name": _ as link_name}:
                    node = LinkButton(link_name, properties=link_prop)
                case {"name": _ as name}:
                    node = LinkButton(name, properties=link_prop)

            for child in self.if_children_make_nodes():
                if child_text := child.properties.get("text"):
                    node.properties["text"] = child_text

            match node:
                case LinkButtonExternal():
                    pass
                case _:
                    # set up the connection, can probably be refactored
                    connection_path = f"{node.name}".replace("-", "_")
                    method_name = f"_{connection_path}_on_button_pressed"

                    # make the "_ready" function
                    # so we can cheat and make these unique names
                    ready_fragment = render_connection_fragment(
                        connection_path, f"%{node.name}", "pressed", method_name
                    )

                    # make our function that we call script
                    path_to_node = link_attrs["link_path"] + link_attrs["link_name"]
                    fragment = on_link_button_pressed_func(method_name, path_to_node)
                    # shoe-horn in our signal emitter
                    fragment.code.append("Global.on_internal_link_press.emit()")
                    if root := self.root_node:
                        ready = ScriptFunction("_ready", ready_fragment)
                        script = GDScriptResource(source="Node")

                        for f in [ready, fragment]:
                            script.add_function(f)

                        root.add_script(script)

            return node

        if self.match(TagCategory.UL):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            return tk_node.node

        if self.match(TagCategory.LI):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            return tk_node.node

        if self.match(TagCategory.H1):
            name = self.make_name_tag()
            node = make_rich_text_label(name, self.previous().str_val)

            tk_node = TokenNode(self.previous(), node)
            # self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.P):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            # unjoined = []
            # Basically need to be merge all p nodes containing text
            # but not those containing images

            unjoined = []
            # Basically need to be merge all p nodes containing text
            # but not those containing images
            for child in self.if_children_make_nodes():
                match child.type:
                    # case "RichTextLabel":
                    #     if unjoined:
                    #         child_text = " ".join(unjoined)
                    #         child_unjoined = make_rich_text_label("text", child_text)
                    #         tk_node.node.add_child(child_unjoined)

                    #         unjoined = []

                    #     tk_node.node.add_child(child)
                    case "Label":
                        if text := child.properties.get("text"):
                            unjoined.append(text)
                    case _:
                        if unjoined:
                            child_text = " ".join(unjoined)
                            child_unjoined = make_rich_text_label("text", child_text)
                            tk_node.node.add_child(child_unjoined)

                            unjoined = []
                        
                        tk_node.node.add_child(child)

            if unjoined:
                child_text = " ".join(unjoined)
                child = make_rich_text_label("text", child_text)
                tk_node.node.add_child(child)

            return tk_node.node

        if self.match(TagCategory.BLOCKQUOTE):
            # basically just a paragraph but with some other shit
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            return tk_node.node

        if self.match(TagCategory.SPAN):
            prev = self.previous()
            if style_dict := self.tag_style_to_dict(prev.attrs):
                match style_dict:
                    case {"color": _ as color_val}:
                        text = f"[color={color_val}]{prev.str_val}[/color]"
                    case _:
                        text = prev.str_val

            node = make_rich_text_label("text", text)

            return node

        if self.match(TagCategory.IMG):
            prev = self.previous()
            node = make_texture_rect("img")
            fname = prev.attrs.get("src").split("/")[-1]
            img_texture = Texture2DGodot(fname)
            res = ExtResourceGodot(img_texture, path=node.name)

            attach_resource(node, res)
            return node

        if self.match(TagCategory.EM):
            text = f"[i]{self.previous().str_val}[/i]"
            node = make_rich_text_label("text", text)

            return node

        if self.match(TagCategory.TEXT):
            text = self.previous().str_val
            # rich text label issues zzzz
            # node = make_rich_text_label("text", text)
            properties = {
                "layout_mode": 2,
                "fit_content": True,
                "text": text,
            }

            node = NodeGodot("text", type="Label", properties=properties)

            return node

        # for all the other classes we gotta support
        self.advance()
        name = self.make_name_tag()
        node = NodeGodot(name, "VBoxContainer")

        for child in self.if_children_make_nodes():
            node.add_child(child)

        return node

    def link_attributes(self):
        name = ""
        if prev_name := self.previous().attrs.get("title"):
            name = prev_name.replace(" ", "-")

        uri = self.previous().attrs.get("href")
        parsed_uri = urlparse(uri)
        match parsed_uri.netloc:
            case "wizardwoes.online" | "":
                # if parsed_uri.netloc == "wizardwoes.online":
                link_name = parsed_uri.path.split("/")[-2]
                link_path = parsed_uri.path[1:]
                return {"name": name, "link_name": link_name, "link_path": link_path}
            case _:
                return {
                    "name": name,
                    "uri": uri,
                    "link_name": "idk",
                    "link_path": "linmk path",
                }

    def basic_node(self):
        name = self.make_name_tag()
        return NodeGodot(name, "PanelContainer")

    def margin_node(self, tk_node: TokenNode) -> MarginContainer:
        # oh yeah this needs to be fixed
        if style_dict := self.tag_style_to_dict(tk_node.token.attrs):
            match style_dict:
                case {"padding": _} | {"padding-left": _} | {"padding-top": _} | {
                    "padding-right": _
                } | {"padding-bottom": _} | {"margin": _} | {"margin-left": _} | {
                    "margin-top": _
                } | {
                    "margin-right": _
                } | {
                    "margin-bottom": _
                }:
                    name = f"{tk_node.node.name}-margin"
                    return MarginContainer(name, properties=style_dict)

        return None

    def make_name_tag(self) -> str:
        prev = self.previous()
        cnt = 1
        while prev.name in [TagCategory.START_CHILDREN, TagCategory.END_CHILDREN]:
            cnt += 1
            prev = self.previous_n(cnt)

        return self.handle_tag_name(prev)

    def handle_tag_name(self, tag):
        match tag.attrs:
            case {"id": id_name}:
                name = id_name
                return f"{name}"
            case {"class": class_name}:
                name = "-".join(class_name)
                return f"{name}"
            case _:
                name = str(tag.name).lower().split(".")[-1]
                return f"{name}"

    def if_children_make_nodes(self) -> list:
        if self.check(TagCategory.START_CHILDREN):
            children = self.make_children()
            return children

        return []

    def make_children(self) -> list[NodeGodot]:
        children = []

        self.consume(TagCategory.START_CHILDREN, "Should be some children around here")

        while not self.check(TagCategory.END_CHILDREN) and not self.is_at_end():
            children.append(self.make_node())

        self.consume(TagCategory.END_CHILDREN, "Start of children need END OF CHILDREN")
        return children

    def apply_class_options_to_node(self, tk_node: TokenNode) -> None:
        match tk_node.token.name:
            case TagCategory.DIV:
                self.apply_div_class_options(tk_node)
            case TagCategory.NAV:
                self.apply_nav_options(tk_node)
            case TagCategory.BODY:
                self.apply_body_options(tk_node)
            case TagCategory.FOOTER:
                self.apply_footer_options(tk_node)
            case TagCategory.P:
                tk_node.node.type = "VBoxContainer"
            case TagCategory.UL:
                tk_node.node.type = "VBoxContainer"
            case TagCategory.LI:
                tk_node.node.type = "VBoxContainer"
            case _:
                # this should be a logger.DEBUG kinda thing
                print(
                    "apply_class_options_to_node not implemented yet for",
                    tk_node.token.name,
                )

    def apply_div_class_options(self, tk_node: TokenNode) -> None:
        match tk_node.node.name:
            case "flex-container-content":
                tk_node.node.type = "HBoxContainer"
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 3,
                    "size_flags_vertical": 3,
                }
            case "navbar__entries":
                tk_node.node.type = "HBoxContainer"
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 3,
                    "size_flags_vertical": 3,
                }
            case "navbar__entry":
                tk_node.node.type = "HBoxContainer"
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 0,
                    "size_flags_vertical": 0,
                }
            case _:
                tk_node.node.type = "VBoxContainer"
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 3,
                    "size_flags_vertical": 3,
                }

        tk_node.node.properties.update(properties)

    def apply_body_options(self, tk_node: TokenNode) -> None:
        tk_node.node.type = "VBoxContainer"

        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 3,
            "size_flags_vertical": 3,
        }

        tk_node.node.properties.update(properties)

    def apply_nav_options(self, tk_node: TokenNode) -> None:
        tk_node.node.type = "HBoxContainer"

        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 3,
            "size_flags_vertical": 3,
        }

        tk_node.node.properties.update(properties)

    def apply_footer_options(self, tk_node: TokenNode) -> None:
        tk_node.node.type = "HBoxContainer"

        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 3,
            "size_flags_vertical": 3,
        }

        tk_node.node.properties.update(properties)

    def apply_style_to_node(self, tk_node: TokenNode) -> None:
        # tk_node.node.properties.update(properties)

        if style_dict := self.tag_style_to_dict(tk_node.token.attrs):
            match style_dict:
                case {"display": "flex", "flex-direction": "column"}:
                    tk_node.node.type = "VBoxContainer"
                case {"display": "flex", "flex-direction": "row"}:
                    tk_node.node.type = "HBoxContainer"
                case {"display": "flex"}:
                    tk_node.node.type = "HBoxContainer"
                case _:
                    pass

            match style_dict:
                case {"font-family": font}:
                    font_res = FontFileGodot()
                    res = ExtResourceGodot(font_res, path=font_res.name)
                    attach_resource(tk_node.node, res)

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

    def match(self, *token_types: TagCategory) -> bool:
        for _type in token_types:
            if self.check(_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TagCategory, error: str) -> Token:
        if self.check(token_type):
            return self.advance()

        raise Exception(self.peek(), error)

    # will need to figure out what we're checking
    def check(self, token_type: TagCategory) -> bool:
        if self.is_at_end():
            return False

        return self.peek().name == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1

        return self.previous()

    def is_at_end(self) -> bool:
        match self.peek().name:
            case TagCategory.EOF:
                return True
            case _:
                return False

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def previous_n(self, n) -> Token:
        return self.tokens[self.current - n]