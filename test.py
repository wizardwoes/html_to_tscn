from dataclasses import dataclass, field
from random import choices
from string import ascii_lowercase

from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import css_inline


# [gd_scene load_steps=2 format=3 uid="uid://bcplq4fm5j6gh"]
@dataclass
class FileDescriptorGodot:
    load_steps: int
    uid: str
    resource_type: str = "gd_scene"
    format: int = 3


def render_fd(fd: FileDescriptorGodot) -> str:
    load_steps = f"load_steps={fd.load_steps}"
    format = f"format={fd.format}"
    uid = f'uid="uid://{fd.uid}"'

    return f"[{fd.resource_type} {load_steps} {format} {uid}]\n"


# [node name="VBoxContainer" type="VBoxContainer" parent="HSplitContainer/IssuePanel"]
# layout_mode = 2
@dataclass
class NodeGodot:
    name: str
    type: str
    parent: "NodeGodot" = None
    resource_type: str = "node"
    _children: list["NodeGodot"] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    resources: list = field(default_factory=list)

    # def __post_init__(self):
    #     if self.parent:
    #         self.parent.add_child(self)

    @property
    def children(self):
        return self._children

    def add_child(self, child):
        child.parent = self
        self._children.append(child)


def generate_random_id():
    res = "".join(choices(ascii_lowercase, k=5))
    return res


# TODO handle this better
# if a script has more than the default functions
# its gonna suck
@dataclass
class GDScriptResource:
    source: str = ""
    ready: list[str] = field(default_factory=list)
    header: str = ""


# [ext_resource type="FontFile" uid="uid://2bsxj50j5a0v" path="res://assets/fonts/cloisterblack-webfont.woff2" id="1_7j3ep"]


@dataclass
class FontFileGodot:
    name: str = "cloisterblack-webfont.woff2"


@dataclass
class SubResourceGodot:
    resource: GDScriptResource
    resource_type: str = "sub_resource"
    type: str = "GDScript"
    path: str = ""
    id: str = ""
    uid: str = ""
    header: str = ""

    def __post_init__(self):
        rand_id = generate_random_id()
        self.id = f"{self.type}_{rand_id}"
        # type will need to be handled different but
        match self.resource:
            case GDScriptResource():
                self.type = "GDScript"
            case _:
                self.type = "UNKNOWN TYPE ITS GONNA BREAK"
        self.header = f'[{self.resource_type} type="{self.type}" id="{self.id}"]'

    def header(self):
        return f'[{self.resource_type} type="{self.type}" id="{self.id}"]'


def render_sub_resource(resource: SubResourceGodot) -> str:
    script = resource.resource
    ready = "\n".join([f"\t{line}" for line in script.ready])
    # [sub_resource type="GDScript" id="GDScript_x1emt"]
    return (
        f"{script.header}\n"
        f'script/source = "extends {script.source}\n'
        f"\n\n\n"
        f"# Called when the node enters the scene tree for the first time.\n"
        f"func _ready():\n"
        f"{ready}\n\n"
        f"func _process(delta):\n"
        f"\tpass\n"
        f'"\n'
    )


# [ext_resource type="Script" path="res://flex-column-glas--left-margin.gd" id="1_fiegk"]
@dataclass
class ExtResourceGodot:
    resource: GDScriptResource | FontFileGodot
    resource_type: str = "ext_resource"
    type: str = "Script"
    path: str = ""
    id: str = ""
    uid: str = ""
    _header: str = ""
    node: NodeGodot = None

    def __post_init__(self):
        rand_id = generate_random_id()
        self.id = f"{rand_id}"
        # type will need to be handled different but
        match self.resource:
            case GDScriptResource():
                self.type = "Script"
            case FontFileGodot():
                self.type = "FontFile"
            case _:
                self.type = "UNKNOWN TYPE ITS GONNA BREAK"

    @property
    def header(self):
        path_str = ""
        match self.resource:
            case GDScriptResource():
                path_str = f"res://{self.path}.gd"
            case FontFileGodot():
                path_str = f"res://assets/fonts/{self.resource.name}"
        return f'[{self.resource_type} type="{self.type}" path="{path_str}" id="{self.id}"]'


def render_ext_resource(resource: ExtResourceGodot) -> str:
    match resource.resource:
        case GDScriptResource():
            script = resource.resource
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
        case FontFileGodot():
            pass


@dataclass
class SceneGodot:
    fd: FileDescriptorGodot
    nodes: NodeGodot
    connections: str = ""
    ext_resources: list = field(default_factory=list)
    sub_resources: list = field(default_factory=list)

    # i dont really need the load steps until im done / about to render the scene
    def __post_init__(self):
        self.fd.load_steps = len(self.ext_resources) + len(self.sub_resources) + 1


def collect_ext_resources(node: NodeGodot, resources=None) -> list[ExtResourceGodot]:
    for child in node.children:
        if resource := child.resources:
            resources.extend(resource)

        collect_ext_resources(child, resources)

    return resources


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
    node.resources.append(resource)


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
    return NodeGodot(name, "RichTextLabel", properties=properties)


def render_properties(properties):
    prop_str = []
    for k, v in properties.items():
        match v:
            case bool():
                s = str(v).lower()
                fstr = f"{k} = {s}"
                prop_str.append(fstr)
            case str():
                fstr = f'{k} = "{v}"'
                prop_str.append(fstr)
            case _:
                fstr = f"{k} = {str(v)}"
                prop_str.append(fstr)

    return "\n".join(prop_str) + "\n"


def render_node_resources(resources):
    res_str = []
    for resource in resources:
        match resource:
            case ExtResourceGodot():
                s = f'ExtResource("{resource.id}")'
                fstr = f"{resource.type.lower()} = {s}"
                res_str.append(fstr)

    return "\n".join(res_str) + "\n"


def handle_parent_text(node: NodeGodot) -> str:
    parent = node.parent
    parent_text = []

    while parent:
        parent_text.append(parent.name)
        parent = parent.parent

    match len(parent_text):
        case 0:
            return ""
        case 1:
            parent_str = f'parent="."'
            return parent_str
        case _:
            rev_parent = parent_text[::-1]
            rev_parent.pop(0)
            path_name = "/".join(rev_parent)
            parent_str = f'parent="{path_name}"'
            return parent_str


# i think you're gonna need a lexer or something
def ptag_to_str(tag) -> str:
    text = []
    for t in tag.children:
        match t:
            case NavigableString():
                fmt = [ts.strip() for ts in t.string.split("\n")]
                t_str = " ".join(fmt).strip()
                text.append(t_str)
            case _:
                match t.name:
                    case "em":
                        fmt = [ts.strip() for ts in t.string.split("\n")]
                        t_str = " ".join(fmt).strip()
                        other_str = f"[i]{t_str}[/i]"
                        text.append(other_str)
                    case _:
                        fmt = [ts.strip() for ts in t.string.split("\n")]
                        t_str = " ".join(fmt).strip()
                        other_str = f"[{t.name}]{t_str}[/{t.name}]"
                        text.append(other_str)

    return "".join(text)


def render(entity) -> str:
    match entity:
        case SceneGodot():
            return render_scene(entity)
        case NodeGodot():
            return render_node(entity)
        case FileDescriptorGodot():
            return render_fd(entity)
        case SubResourceGodot():
            return render_sub_resource(entity)
        case ExtResourceGodot():
            print("here", entity)
            return render_ext_resource(entity)
        case GDScriptResource():
            return render_script(entity)


def render_scene(scene: SceneGodot) -> list[str]:
    out = []

    fd = render(scene.fd)
    out.append(fd)

    # ext_resources need to be written to their own file
    # onnly the header ends up here

    ext_resources = [res.header for res in scene.ext_resources]
    out.extend(ext_resources)
    out.append("\n")

    sub_resources = [render_sub_resource(res) for res in scene.sub_resources]
    out.extend(sub_resources)

    nodes = render_nodes(scene.nodes, [])
    out.extend(nodes)

    return out


def render_nodes(node, scene):
    if not scene:
        scene = [render(node)]

    for n in node.children:
        scene.append(render(n))
        render_nodes(n, scene)

    return scene


def render_node(node: NodeGodot) -> str:
    name = f'name="{node.name}"'
    type = f'type="{node.type}"'

    msg = [node.resource_type, name, type]

    parent_msg = handle_parent_text(node)
    msg.append(parent_msg)

    node_info = " ".join(msg)
    to_render = [f"[{node_info}]", "\n"]

    if has_properties := node.properties:
        properties = render_properties(has_properties)
        to_render.append(properties)

    if has_resources := node.resources:
        resources = render_node_resources(has_resources)
        to_render.append(resources)

    return "".join(to_render)


# could probably rewrite so that it doesn't know the parent
def make_node(tag) -> NodeGodot:

    div_properties = {
        "layout_mode": 2,
        "size_flags_horizontal": 3,
        "size_flags_vertical": 3,
    }
    match tag.name:
        case "p" | "a":
            p_str = ptag_to_str(tag)
            print("why", p_str)
            suffix = generate_random_id()
            name = f"richtext-{suffix}"
            return make_rich_text_label(name, p_str)

        case "h1":
            if styles := tag.attrs.get("style"):
                style_d = style_to_dict(styles)

            p_str = ptag_to_str(tag)
            suffix = generate_random_id()
            name = f"h1-{suffix}"
            node = make_rich_text_label(name, p_str)

            match style_d:
                case {"font-family": font}:
                    font_res = FontFileGodot()
                    res = ExtResourceGodot(font_res, path=font_res.name)
                    attach_resource(node, res)

            return node
        case "div":
            return make_container(tag, div_properties)
        case "nav":
            return make_container(tag, div_properties)
        case "body":
            return NodeGodot(tag.name, "VBoxContainer", properties=div_properties)
        case _:
            return None


# 1 step away from a lexer
def convert_padding_to_godot(pad_value) -> tuple:
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

    return ("int", int(pad_value))


def render_margin_fragment(margin_dir, margin_val):
    define_str = f"var {margin_dir} = {margin_val}"
    add_theme_str = f'add_theme_constant_override("{margin_dir}", {margin_dir})'

    return [define_str, add_theme_str]


def handle_margins(node: NodeGodot) -> None:
    # ok this is side-effect heavy BUT
    script = GDScriptResource(source=node.type)
    res = ExtResourceGodot(script, path=node.name)

    properties = node.properties
    margin_keys = [
        "theme_override_constants/margin_left",
        "theme_override_constants/margin_top",
        "theme_override_constants/margin_right",
        "theme_override_constants/margin_bottom",
    ]

    for key in margin_keys:
        if pval := properties.get(key):
            val = convert_padding_to_godot(pval)
            match val:
                case ("script", _ as v):
                    m = key.split("/")[-1]
                    frag = render_margin_fragment(m, v)
                    script.ready.extend(frag)
                    del properties[key]
                case ("int", _ as v):
                    properties[key] = v

    if script.ready:
        attach_resource(node, res)


def make_margin_container(name, margins: dict, properties=None) -> NodeGodot:
    # handle the margins/padding
    # will need to break down some dumb shit
    # will need to refactor this

    if pval := margins.get("padding-left"):
        properties["theme_override_constants/margin_left"] = pval

    if pval := margins.get("padding-top"):
        properties["theme_override_constants/margin_top"] = pval

    if pval := margins.get("padding-right"):
        properties["theme_override_constants/margin_right"] = pval

    if pval := margins.get("padding-bottom"):
        properties["theme_override_constants/margin_bottom"] = pval

    if pval := margins.get("padding"):
        match pval.split(" "):
            case [all_pad]:
                properties["theme_override_constants/margin_left"] = all_pad
                properties["theme_override_constants/margin_top"] = all_pad
                properties["theme_override_constants/margin_right"] = all_pad
                properties["theme_override_constants/margin_bottom"] = all_pad
            case [top_bottom, left_right]:
                properties["theme_override_constants/margin_left"] = left_right
                properties["theme_override_constants/margin_top"] = top_bottom
                properties["theme_override_constants/margin_right"] = left_right
                properties["theme_override_constants/margin_bottom"] = top_bottom
            case [top, left_right, bottom]:
                properties["theme_override_constants/margin_left"] = left_right
                properties["theme_override_constants/margin_top"] = top
                properties["theme_override_constants/margin_right"] = left_right
                properties["theme_override_constants/margin_bottom"] = bottom
            case [top, right, bottom, left]:
                properties["theme_override_constants/margin_left"] = left
                properties["theme_override_constants/margin_top"] = top
                properties["theme_override_constants/margin_right"] = right
                properties["theme_override_constants/margin_bottom"] = bottom

    return NodeGodot(name, "MarginContainer", properties=properties)


def make_container(tag, properties=None):
    margin_node = None
    if styles := tag.attrs.get("style"):
        name = handle_tag_name(tag)
        style_d = style_to_dict(styles)

        # setup the properties
        match style_d:
            case {"width": "100%"}:
                properties["size_flags_horizontal"] = 3

        # margin containers
        # what if this was moved to the traverse tree?
        match style_d:
            case {"padding": _} | {"padding-left": _} | {"padding-top": _} | {
                "padding-right": _
            } | {"padding-bottom": _}:
                pad_properties = dict(properties)
                margin_node = make_margin_container(
                    f"{name}-margin", style_d, pad_properties
                )
                # now need to handle attaching the margin container and the child container
                handle_margins(margin_node)

        # specific rules idk
        match name:
            case "flex-container-content":
                node = NodeGodot(name, "HBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case "navbar":
                node = NodeGodot(name, "HBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case "navbar__homelink":
                pass
            case "citation":
                # these are a nightmare why did i set it up this way
                p_str = ptag_to_str(tag)
                node = make_rich_text_label(name, p_str, properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case _:
                pass

        # general rules
        match style_d:
            case {"display": "flex", "flex-direction": "column"}:
                node = NodeGodot(name, "VBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case {"display": "flex", "flex-direction": "row"}:
                node = NodeGodot(name, "HBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case {"display": "flex"}:
                node = NodeGodot(name, "HBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
            case _:
                node = NodeGodot(name, "VBoxContainer", properties=properties)
                if margin_node:
                    margin_node.add_child(node)
                    return margin_node
                return node
    else:
        try:
            name = "-".join(tag.get("class"))
        except TypeError:
            name = "idk this is a name"
        return NodeGodot(name, "PanelContainer")


def handle_tag_name(tag, has_suffix=False):
    suffix = ""
    if has_suffix:
        suffix = generate_random_id()

    match tag.attrs:
        case {"id": id_name}:
            name = id_name
            return f"{name}{suffix}"
        case {"class": class_name}:
            name = "-".join(class_name)
            return f"{name}{suffix}"
        case _:
            name = tag.name
            return f"{name}{suffix}"


def style_to_dict(styles):
    styled = {}
    for s in styles.strip().split(";"):
        try:
            k, v = s.split(": ")
            styled[k] = v
        except ValueError:
            pass
    return styled


def traverse_tree(tag, parent_node):
    for t in tag.children:
        if not isinstance(t, NavigableString):
            # what if we made node based on structure
            # then applied the style based properties?
            node = make_node(t)
            # node = None until we support more tags ig

            try:
                if node.name in [child.name for child in parent_node.children]:
                    suffix = generate_random_id()
                    node.name = f"{node.name}-{suffix}"

                parent_node.add_child(node)

                # this is hacky but it works
                match node.type:
                    case "MarginContainer":
                        traverse_tree(t, node.children[0])
                    case _:
                        traverse_tree(t, node)

            except AttributeError:
                pass

    return parent_node


def write_out_node_script(node: NodeGodot) -> None:
    out_f = Path(f".\{node.name}.gd")

    with open(out_f, "w") as f:
        f.write(render(node.script))


# can only have 1 script attached to node
# everything else is external script?

# would have to handle @media in the _ready function

if __name__ == "__main__":
    test_doc = Path("page 90.html")
    inliner = css_inline.CSSInliner(base_url="file://wizardwoes.css")

    with open(test_doc, "r", encoding="utf-8") as f:
        inlined = css_inline.inline(f.read())

    soup = BeautifulSoup(inlined, features="lxml")

    # mostly works
    root_properties = {
        "anchors_preset": 15,
        "anchor_right": 1.0,
        "anchor_bottom": 1.0,
        "size_flags_horizontal": 3,
        "size_flags_vertical": 3,
        "horizontal_scroll_mode": 0,
        "vertical_scroll_mode": 2,
    }

    root_node = NodeGodot(
        "HtmlNode", "ScrollContainer", None, properties=root_properties
    )
    descriptor = FileDescriptorGodot(1, "idk")
    # get rid of head for now
    nodes = traverse_tree(soup.html, root_node)
    resources = collect_ext_resources(root_node, [])

    scene = SceneGodot(descriptor, nodes, ext_resources=resources)

    rendered = render(scene)

    outfile = Path("test.tscn")
    print(f"write it out to {outfile}")
    with open(outfile, "w", encoding="utf-8") as f:
        for rend in rendered:
            f.write(rend)
            f.write("\n")

    for resource in resources:
        match resource.resource:
            case GDScriptResource():
                outfile = Path(f"{resource.path}.gd")
                with open(Path("gdscripts") + outfile, "w", encoding="utf-8") as f:
                    f.write(render(resource.resource))
            case _:
                print("we dont write to file", resource.resource)
