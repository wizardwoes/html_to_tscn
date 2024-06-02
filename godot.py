from dataclasses import dataclass, field
from random import choices
from string import ascii_lowercase


def generate_random_id():
    res = "".join(choices(ascii_lowercase, k=5))
    return res


@dataclass
class FileDescriptorGodot:
    load_steps: int
    uid: str
    resource_type: str = "gd_scene"
    format: int = 3

    def render(self) -> str:
        # return something like
        # [gd_scene load_steps=2 format=3 uid="uid://bcplq4fm5j6gh"]

        load_steps = f"load_steps={self.load_steps}"
        format = f"format={self.format}"
        uid = f'uid="uid://{self.uid}"'

        return f"[{self.resource_type} {load_steps} {format} {uid}]\n"


@dataclass
class NodeGodot:
    name: str
    type: str
    parent: "NodeGodot" = None
    resource_type: str = "node"
    _children: list["NodeGodot"] = field(default_factory=list)
    _default_properties: dict = field(default_factory=dict)
    properties: dict = field(default_factory=dict)
    theme_properties: dict = field(default_factory=dict)
    resources: list = field(default_factory=list)
    # for now its an external resource but probably want to unwrap it for this one
    script: "ExtResourceGodot" = None
    connections: list["ConnectionGodot"] = field(default_factory=list)

    def __post_init__(self):
        if self.parent:
            self.parent.add_child(self)
            self.parent_path = self.handle_parent_text()

        if self._default_properties:
            self._default_properties.update(self.properties)
            self.properties = self._default_properties

    @property
    def children(self):
        return self._children

    @property
    def parent_path_str(self):
        return self.handle_parent_text()

    def add_child(self, child):
        if child.name in [node.name for node in self._children]:
            suffix = generate_random_id()
            child.name = f"{child.name}-{suffix}"

        child.parent = self
        self._children.append(child)

    def add_script(self, script: "GDScriptResource"):
        if script_exists := self.script:
            for func in script.funcs.values():
                script_exists.resource.add_function(func)
        else:
            self.script = ExtResourceGodot(script, path=self.name)

    def render(self) -> str:
        # header looks something like
        # [node name="VBoxContainer" type="VBoxContainer" parent="HSplitContainer/IssuePanel"]

        name = f'name="{self.name}"'
        type = f'type="{self.type}"'

        msg = [self.resource_type, name, type]

        parent_path = self.handle_parent_text()
        # clean up later
        if parent_path:
            parent_msg = f'parent="{parent_path}"'
            msg.append(parent_msg)
        else:
            msg.append(parent_path)

        node_info = " ".join(msg)
        to_render = [f"[{node_info}]", "\n"]

        if self.properties:
            properties = self._render_properties()
            to_render.append(properties)

        # all the rendering is in the template so not sure
        # if self.theme_properties:
        #     theme_properties = self._render_theme_properties()
        #     to_render.append(theme_properties)

        if self.resources:
            resources = self._render_node_resources()
            to_render.append(resources)

        if self.script:
            to_render.append(self._render_node_script())

        return "".join(to_render)

    def handle_parent_text(self) -> str:
        parent = self.parent
        parent_text = []

        while parent:
            parent_text.append(parent.name)
            parent = parent.parent

        match len(parent_text):
            case 0:
                return ""
            case 1:
                parent_str = f"."
                return parent_str
            case _:
                rev_parent = parent_text[::-1]
                rev_parent.pop(0)
                parent_str = "/".join(rev_parent)
                return parent_str

    def _render_properties(self):
        prop_str = []
        for k, v in self.properties.items():
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

    # def _render_theme_properties(self):
    #     prop_str = []
    #     for k, v in self.theme_properties.items():
    #         match v:
    #             case bool():
    #                 s = str(v).lower()
    #                 fstr = f"theme_override_constants/{k} = {s}"
    #                 prop_str.append(fstr)
    #             case str():
    #                 fstr = f'theme_override_constants/{k} = "{v}"'
    #                 prop_str.append(fstr)
    #             case None:
    #                 continue
    #             case _:
    #                 fstr = f"theme_override_constants/{k} = {str(v)}"
    #                 prop_str.append(fstr)

    #     return "\n".join(prop_str) + "\n"

    def renderable_properties(self):
        # this is called from the template
        # maybe a terrible decision in hindsight
        renderable = {}
        for k, v in self.properties.items():
            match v:
                case bool():
                    s = str(v).lower()
                    renderable[k] = s
                case str():
                    renderable[k] = f'"{v}"'
                case _:
                    renderable[k] = str(v)

        return renderable

    def renderable_theme_properties(self):
        # where we would prepend like
        # fstr = f"theme_override_constants/{k} = {s}"
        renderable = {}
        val = None
        for k, v in self.theme_properties.items():
            # handle formatting for value type
            match v:
                case bool():
                    s = str(v).lower()
                    val = s
                case str():
                    val = f'"{v}"'
                case None:
                    continue
                case _:
                    val = str(v)

            # handle formatting for theme property type
            # this could probably be somewhere else?
            match k:
                case "margin_left" | "margin_right" | "margin_top" | "margin_bottom":
                    override_name = f"theme_override_constants/{k}"
                    renderable[override_name] = val
                case "font_size" | "normal_font_size":
                    override_name = f"theme_override_font_sizes/{k}"
                    renderable[override_name] = val
            
        return renderable

    def _render_node_resources(self):
        res_str = []
        for resource in self.resources:
            ext_res_id = f'ExtResource("{resource.id}")'
            fstr = f"{resource.resource.as_property_field()} = {ext_res_id}"

            res_str.append(fstr)

        return "\n".join(res_str) + "\n"

    def _render_node_script(self):
        ext_res_id = f'ExtResource("{self.script.id}")'
        fstr = f"{self.script.resource.as_property_field()} = {ext_res_id}"

        return fstr + "\n"
    
    def apply_font_family(self, font):
        font_res = FontFileGodot()
        res = ExtResourceGodot(font_res, path=font_res.name)
        res.path = self.name
        self.resources.append(res)

    def apply_font_size(self, size):
        pass


@dataclass
class HBoxContainer(NodeGodot):
    type: str = "HBoxContainer"


@dataclass
class VBoxContainer(NodeGodot):
    type: str = "VBoxContainer"


@dataclass
class RichTextLabel(NodeGodot):
    type: str = "RichTextLabel"

    def apply_font_size(self, size):
        self.theme_properties["normal_font_size"] = size


@dataclass
class Label(NodeGodot):
    type: str = "Label"

    def apply_font_size(self, size):
        self.theme_properties["font_size"] = size

@dataclass
class LinkButton(NodeGodot):
    type: str = "LinkButton"
    theme_properties: dict = field(
        default_factory=lambda: {
            "font_size": None,
            "font": None
        }
    )

    def __post_init__(self):
        # hack for our homepage link class/id being empty
        if self.name == "":
            self.name = "home-page"
            self.properties["text"] = "wizard woes"
            self.properties["link_path"] = "home/"
            self.properties["link_name"] = "home"
    
    def apply_font_size(self, size):
        self.theme_properties["font_size"] = size

@dataclass
class LinkButtonExternal(NodeGodot):
    type: str = "LinkButton"
    


@dataclass
class TextureRect(NodeGodot):
    type: str = "TextureRect"
    _default_properties: dict = field(
        default_factory=lambda: {
            "layout_mode": 2,
            "size_flags_vertical": 3,
            "expand_mode": 5,
            "stretch_mode": 4,
        }
    )


@dataclass
class MarginContainer(NodeGodot):
    type: str = "MarginContainer"
    theme_properties: dict = field(
        default_factory=lambda: {
            "margin_left": None,
            "margin_top": None,
            "margin_right": None,
            "margin_bottom": None,
        }
    )

    def __post_init__(self):
        # just going to cheat and handle padding and margins the exact same way
        # need to find cases where an element has both of these though

        self._map_margin_values()
        self._map_padding_values()

        self.update_margins()

        self.properties.update(
            {
                "layout_mode": 2,
                "size_flags_horizontal": 3,
                "size_flags_vertical": 3,
            }
        )

    def _map_margin_values(self) -> dict:
        # this function basically handles the formatting of the two margins
        # case where margin is defined as something like
        # margin: 25px 50px 75px 100px;
        if pval := self.properties.get("margin"):
            match pval.split(" "):
                case [all_pad]:
                    # change this later
                    for k, v in self.theme_properties.items():
                        self.theme_properties[k] = all_pad

                case [top_bottom, left_right]:
                    for k in [
                        "margin_left",
                        "margin_right",
                    ]:
                        self.theme_properties[k] = left_right

                    for k in [
                        "margin_top",
                        "margin_bottom",
                    ]:
                        self.theme_properties[k] = top_bottom

                case [top, left_right, bottom]:
                    for k in [
                        "margin_left",
                        "margin_right",
                    ]:
                        self.theme_properties[k] = left_right

                    self.theme_properties["margin_top"] = top
                    self.theme_properties["margin_bottom"] = bottom

                case [top, right, bottom, left]:
                    self.theme_properties["margin_left"] = left
                    self.theme_properties["margin_top"] = top
                    self.theme_properties["margin_right"] = right
                    self.theme_properties["margin_bottom"] = bottom

            del self.properties["margin"]

        # case where we use one of the 4 margin-*
        # check if property is in our map
        # put it in our dict if it is
        # more specific so overrides whatever our margin is

        if pval := self.properties.get("margin-top"):
            self.theme_properties["margin_top"] = pval
            del self.properties["margin-top"]

        if pval := self.properties.get("margin-bottom"):
            self.theme_properties["margin_bottom"] = pval
            del self.properties["margin-bottom"]

        if pval := self.properties.get("margin-right"):
            self.theme_properties["margin_right"] = pval
            del self.properties["margin-right"]

        if pval := self.properties.get("margin-left"):
            self.theme_properties["margin_left"] = pval
            del self.properties["margin-left"]

    def _map_padding_values(self) -> dict:
        # this function basically handles the formatting of the two padding cases
        # case where padding is defined as something like
        # padding: 25px 50px 75px 100px;
        if pval := self.properties.get("padding"):
            match pval.split(" "):
                case [all_pad]:
                    # change this later
                    for k, v in self.theme_properties.items():
                        self.theme_properties[k] = all_pad

                case [top_bottom, left_right]:
                    for k in [
                        "margin_left",
                        "margin_right",
                    ]:
                        self.theme_properties[k] = left_right

                    for k in [
                        "margin_top",
                        "margin_bottom",
                    ]:
                        self.theme_properties[k] = top_bottom

                case [top, left_right, bottom]:
                    for k in [
                        "margin_left",
                        "margin_right",
                    ]:
                        self.theme_properties[k] = left_right

                    self.theme_properties["margin_top"] = top
                    self.theme_properties["margin_bottom"] = bottom

                case [top, right, bottom, left]:
                    self.theme_properties["margin_left"] = left
                    self.theme_properties["margin_top"] = top
                    self.theme_properties["margin_right"] = right
                    self.theme_properties["margin_bottom"] = bottom

            del self.properties["padding"]

        # case where we use one of the 4 padding-*
        # check if property is in our map
        # put it in our dict if it is
        # more specific so overrides whatever our padding is

        if pval := self.properties.get("padding-top"):
            self.theme_properties["margin_top"] = pval
            del self.properties["padding-top"]

        if pval := self.properties.get("padding-bottom"):
            self.theme_properties["margin_bottom"] = pval
            del self.properties["padding-bottom"]

        if pval := self.properties.get("padding-right"):
            self.theme_properties["margin_right"] = pval
            del self.properties["padding-right"]

        if pval := self.properties.get("padding-left"):
            self.theme_properties["margin_left"] = pval
            del self.properties["padding-left"]

    def update_margins(self) -> None:
        # side effect heavy
        # do i need to calculate the sizes / create this script at this point in time?
        fragments = []
        # this feels hacky
        keys = list(self.theme_properties.keys())
        for k in keys:
            if v := self.theme_properties.get(k):
                match self.convert_css_value_to_godot(v):
                    case ("script", _ as val):
                        frag = self.render_margin_fragment(k, val)
                        fragments.extend(frag)
                        del self.theme_properties[k]
                    case ("int", _ as val):
                        self.theme_properties[k] = val

        if fragments:
            # make our ready script
            func = ScriptFunction("_ready", fragments)
            script = GDScriptResource(source=self.type)
            script.add_function(func)

            self.add_script(script)

    # this may be used in other css values than just padding
    def convert_css_value_to_godot(self, value) -> tuple:
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

    def render_margin_fragment(self, margin_dir, margin_val):
        define_str = f"var {margin_dir} = {margin_val}"
        add_theme_str = f'add_theme_constant_override("{margin_dir}", {margin_dir})'

        return [define_str, add_theme_str]


@dataclass
class ConnectionGodot:
    # [connection signal="pressed" from="next-prev-wrap-margin/next-prev-wrap/next-prev-wrap__link-nhulh/text2" to="." method="_on_button_pressed"]
    signal: str
    type: str = "connection"
    from_node: str = ""
    to_node: str = ""
    method_name: str = ""

    def render(self):
        return f'[{self.type} signal="{self.signal}" from="{self.from_node}" to="{self.to_node}" method="{self.method_name}"]'

    def as_property_field(self):
        return "connection"


@dataclass
class ScriptFunction:
    name: str
    code: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = "\n".join([f"\t{line}" for line in self.code])
        return f"func {self.name}():\n" f"{lines}\n\n"


@dataclass
class GDScriptResource:
    source: str = ""
    onready: dict = field(default_factory=dict)
    funcs: dict = field(default_factory=dict)

    header: str = ""

    def as_property_field(self):
        return "script"

    def add_function(self, func: ScriptFunction) -> None:
        if func_exists := self.funcs.get(func.name):
            func_exists.code.extend(func.code)
        else:
            self.funcs[func.name] = func

    def render_onready_vars(self) -> str:
        to_str = []
        for k, v in self.onready.items():
            # example:
            # @onready var scrollbar = $".".get_v_scroll_bar()
            var_str = f"@onready var {k} = {v}"
            to_str.append(var_str)

        return "\n".join(to_str)


@dataclass
class FontFileGodot:
    name: str = "cloisterblack-webfont.woff2"
    type: str = "FontFile"
    # [ext_resource type="FontFile" uid="uid://2bsxj50j5a0v" path="res://assets/fonts/cloisterblack-webfont.woff2" id="1_7j3ep"]

    def as_property_field(self):
        return "theme_override_fonts/normal_font"


@dataclass
class Texture2DGodot:
    name: str
    type: str = "Texture2D"

    def as_property_field(self):
        return "texture"


# maybe I need some sort of "resource factory" to handle some of the base options
# like directories and shit
@dataclass
class ExtResourceGodot:
    resource: GDScriptResource | FontFileGodot | Texture2DGodot
    resource_type: str = "ext_resource"
    type: str = ""
    path: str = ""
    id: str = ""
    uid: str = ""

    def __post_init__(self):
        self.id = f"{generate_random_id()}"
        # type will need to be handled different but
        match self.resource:
            case GDScriptResource():
                self.type = "Script"
            case Texture2DGodot():
                # need to figure out better way of handling this
                self.type = self.resource.as_property_field()
            case _:
                self.type = self.resource.type

    @property
    def header(self):
        # [ext_resource type="Script" path="res://flex-column-glas--left-margin.gd" id="1_fiegk"]
        return f'[{self.resource_type} type="{self.type}" path="{self.path_str}" id="{self.id}"]'

    @property
    def path_str(self):
        match self.resource:
            case GDScriptResource():
                path_str = f"{self.path}.gd"
            case FontFileGodot():
                path_str = f"res://assets/fonts/{self.resource.name}"
            case _:
                path_str = f"{self.resource.name}"
        return path_str

    def render(self) -> str:
        match self.resource:
            case GDScriptResource() as script:
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
            case Texture2DGodot():
                pass
            case _:
                return ""


@dataclass
class SceneGodot:
    nodes: NodeGodot
    fd: FileDescriptorGodot = None
    uid: str = "idk"
    # _ext_resources: list['ExtResourceGodot'] = field(default_factory=list)
    sub_resources: list = field(default_factory=list)
    connections: list = field(default_factory=list)

    # i dont really need the load steps until im done / about to render the scene
    def __post_init__(self):
        if not self.fd:
            self.fd = FileDescriptorGodot(1, self.uid)
        self.fd.load_steps = len(self.ext_resources) + len(self.sub_resources) + 1

    @property
    def ext_resources(self) -> list[ExtResourceGodot]:
        return self._collect_ext_resources(
            self.nodes, [*self.nodes.resources, self.nodes.script]
        )

    def _collect_ext_resources(
        self, node: NodeGodot, resources=None
    ) -> list[ExtResourceGodot]:
        for child in node.children:
            if resource := child.resources:
                resources.extend(resource)
            if script := child.script:
                resources.append(script)

            self._collect_ext_resources(child, resources)

        return resources

    @property
    def scripts(self) -> list[ExtResourceGodot]:
        return self._collect_node_scripts(self.nodes, [self.nodes.script])

    def _collect_node_scripts(
        self, node: NodeGodot, scripts=None
    ) -> list[ExtResourceGodot]:
        for child in node.children:
            if script := child.script:
                scripts.append(script)

            self._collect_node_scripts(child, scripts)

        return scripts

    def flat_nodes(self) -> list[NodeGodot]:
        return self._flatten_nodes(self.nodes, [self.nodes])

    def _flatten_nodes(self, node, nodes) -> list[NodeGodot]:
        for n in node.children:
            nodes.append(n)
            self._flatten_nodes(n, nodes)

        return nodes
