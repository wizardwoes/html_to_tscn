from dataclasses import dataclass
from urllib.parse import urlparse
from functools import singledispatch

from godot import (
    ExtResourceGodot,
    FontFileGodot,
    GDScriptResource,
    NodeGodot,
    ScriptFunction,
    Texture2DGodot,
    HBoxContainer,
    VBoxContainer,
    MarginContainer,
    LinkButton,
    LinkButtonExternal,
    RichTextLabel,
    Label,
    TextureRect,
)
from tag_token import TagCategory, Token


def make_rich_text_label(name, text, extra_properties=None):
    # figure out way to derive these properties from something else
    properties = {
        "layout_mode": 2,
        "bbcode_enabled": True,
        "fit_content": True,
        "autowrap_mode": 2,
        "text": text,
    }
    if extra_properties:
        properties.update(extra_properties)

    return RichTextLabel(name, properties=properties)


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


def render_connection_fragment(var_name, node_path, signal, method_name):
    define_str = f'var {var_name} = self.get_node("{node_path}")'
    connect_str = f"{var_name}.{signal}.connect({method_name})"

    return [define_str, connect_str]


# leaving this for now
# but can probably delete later
# def make_ready_script(node, fragments):
#     func = ScriptFunction("_ready", fragments)
#     script = GDScriptResource(source=node.type)
#     script.add_function(func)

#     return script


@dataclass
class TokenNode:
    token: Token
    node: NodeGodot


class Parser:
    def __init__(self, tokens, root_node=None) -> None:
        self.tokens = tokens
        self.current = 0
        self.root_node = root_node
        self.style_ctx = []

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
            self.apply_font_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                node.add_child(child)

            return node

        if self.match(TagCategory.BODY):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)

            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            # if margin := self.margin_node(tk_node):
            #     margin.add_child(tk_node.node)
            #     return margin

            return tk_node.node

        if self.match(TagCategory.NAV):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            # need to figure out better way to not overwrite
            # self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            # if margin := self.margin_node(tk_node):
            #     margin.add_child(tk_node.node)
            #     return margin

            return tk_node.node

        if self.match(TagCategory.FOOTER):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)

            self.apply_class_options_to_node(tk_node)
            # self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            # if margin := self.margin_node(tk_node):
            #     margin.add_child(tk_node.node)
            #     return margin

            return tk_node.node

        if self.match(TagCategory.DIV):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)

            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)
            self.apply_class_options_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

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
                    # hacky way to handle our home page link
                    # sure this won't bite me in the ass later
                    if link_name == "":
                        link_name = "home-page"
                        link_prop["text"] = "wizard woes"
                    node = LinkButton(link_name, properties=link_prop)
                case {"name": _ as name}:
                    node = LinkButton(name, properties=link_prop)

            tk_node = TokenNode(self.previous(), node)

            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                if child_text := child.properties.get("text"):
                    node.properties["text"] = child_text

            self.style_ctx.pop()

            match node:
                case LinkButtonExternal():
                    pass
                case LinkButton():
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
                    # hack for our homepage link class/id being empty
                    if path_to_node == "":
                        path_to_node = "home/home"

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
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            return tk_node.node

        if self.match(TagCategory.LI):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            return tk_node.node

        if self.match(TagCategory.H1):
            name = self.make_name_tag()
            node = make_rich_text_label(name, self.previous().str_val)
            tk_node = TokenNode(self.previous(), node)
            # self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.H4):
            name = self.make_name_tag()
            node = make_rich_text_label(name, self.previous().str_val)

            tk_node = TokenNode(self.previous(), node)
            # self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            self.style_ctx.append(self.tag_style_to_dict(tk_node.token.attrs))

            for child in self.if_children_make_nodes():
                tk_node.node.add_child(child)

            self.style_ctx.pop()

            if margin := self.margin_node(tk_node):
                margin.add_child(tk_node.node)
                return margin

            return tk_node.node

        if self.match(TagCategory.P):
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

            unjoined = []
            for child in self.if_children_make_nodes():
                match child.type:
                    case "Label":
                        if text := child.properties.get("text"):
                            unjoined.append(text)
                    case "RichTextLabel":
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
                temp_node = TokenNode(self.previous(), child)
                self.apply_font_style_to_node(temp_node)
                tk_node.node.add_child(child)

            return tk_node.node

        if self.match(TagCategory.BLOCKQUOTE):
            # basically just a paragraph but with some other shit
            node = self.basic_node()

            tk_node = TokenNode(self.previous(), node)
            self.apply_class_options_to_node(tk_node)
            self.apply_style_to_node(tk_node)
            self.apply_font_style_to_node(tk_node)

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
            node = TextureRect("img")
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
                "autowrap_mode": 0,
                "text": text,
            }

            node = Label("text", properties=properties)
            tk_node = TokenNode(self.previous(), node)

            self.apply_font_style_to_node(tk_node)

            print("current style ctx", tk_node.node.name, self.style_ctx)

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
                case (
                    {"padding": _}
                    | {"padding-left": _}
                    | {"padding-top": _}
                    | {"padding-right": _}
                    | {"padding-bottom": _}
                    | {"margin": _}
                    | {"margin-left": _}
                    | {"margin-top": _}
                    | {"margin-right": _}
                    | {"margin-bottom": _}
                ):
                    name = f"{tk_node.node.name}-margin"
                    # THIS IS WHERE WE SHOULD DO ALL THE STYLING AND THEN PASS IT
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
        match name := tk_node.node.name:
            case "flex-container-content" | "navbar__entries" | "navbar__entry":
                properties = {
                    "layout_mode": 2,
                    "size_flags_vertical": 3,
                }
                tk_node.node = HBoxContainer(name, properties=properties)
            case "footer-wrap":
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 4,
                    "size_flags_vertical": 0,
                }
                tk_node.node = VBoxContainer(name, properties=properties)
            case _:
                properties = {
                    "layout_mode": 2,
                    "size_flags_horizontal": 3,
                    "size_flags_vertical": 3,
                }
                tk_node.node = VBoxContainer(name, properties=properties)

    def apply_body_options(self, tk_node: TokenNode) -> None:
        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 3,
            "size_flags_vertical": 3,
        }

        tk_node.node = VBoxContainer(tk_node.node.name, properties=properties)

    def apply_nav_options(self, tk_node: TokenNode) -> None:
        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 3,
            "size_flags_vertical": 3,
        }

        tk_node.node = HBoxContainer(tk_node.node.name, properties=properties)

    def apply_footer_options(self, tk_node: TokenNode) -> None:
        properties = {
            "layout_mode": 2,
            "size_flags_horizontal": 4,
            "size_flags_vertical": 8,
        }
        tk_node.node = HBoxContainer(tk_node.node.name, properties=properties)

    def apply_style_to_node(self, tk_node: TokenNode) -> None:
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

    def apply_font_style_to_node(self, tk_node: TokenNode) -> None:
        try:
            style_dict = self.style_ctx[-1]
            style_dict.update(self.tag_style_to_dict(tk_node.token.attrs))
        except IndexError:
            style_dict = self.tag_style_to_dict(tk_node.token.attrs)

        if style_dict:
            # handle font type here
            match style_dict:
                case {"font-family": font}:
                    tk_node.node.apply_font_family(font)

            match style_dict:
                case {"font-size": fontsize}:
                    match convert_css_value_to_godot(fontsize):
                        # cheating since we have only px font sizes
                        # case ("script", _ as val):
                        #     frag = self.render_margin_fragment(k, val)
                        #     fragments.extend(frag)
                        #     del self.theme_properties[k]
                        case ("int", _ as val):
                            tk_node.node.apply_font_size(val)

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


# this may be used in other css values than just padding
def convert_css_value_to_godot(value) -> tuple:
    if "px" in value:
        return ("int", int(value[:-2]))
    if "%" in value:
        calc = int(value[:-1]) * 0.01
        return ("int", calc)
    if "vh" in value:
        calc = int(value[:-2]) * 0.01
        pad_str = f"{calc} * get_viewport().get_visible_rect().size.x"
        return ("script", pad_str)
    if "vw" in value:
        calc = int(value[:-2]) * 0.01
        pad_str = f"{calc} * get_viewport().get_visible_rect().size.y"
        return ("script", pad_str)
    if "auto" in value:
        return ("str", "auto value")
    if "rem" in value:
        # rem is relative to size of root element font
        # 1rem = the font size of the html element
        # for now we will cheat and say it's 16px
        multiplier = int(value[:-3])
        fontsize = 16
        calc = multiplier * fontsize
        return ("int", calc)
    if "em" in value:
        # em is relative to font size of element
        # 1em = whatever the size is, 2em = twice the size
        # if no fontsize is defined, then default is 16px
        # may need to figure out how to handle changes in fontsize later

        multiplier = int(value[:-2])
        fontsize = 16
        calc = multiplier * fontsize
        return ("int", calc)

    return ("int", int(value))
