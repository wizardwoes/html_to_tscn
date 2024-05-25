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
    properties: dict = field(default_factory=dict)
    resources: list = field(default_factory=list)
    # for now its an external resource but probably want to unwrap it for this one
    script: "ExtResourceGodot" = None
    connections: list["ConnectionGodot"] = field(default_factory=list)

    def __post_init__(self):
        if self.parent:
            self.parent.add_child(self)
            self.parent_path = self.handle_parent_text()

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

    def renderable_properties(self):
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
        for k,v in self.onready.items():
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
        return self._collect_ext_resources(self.nodes, [*self.nodes.resources, self.nodes.script])

    def _collect_ext_resources(self, node: NodeGodot, resources=None) -> list[ExtResourceGodot]:
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

    def _collect_node_scripts(self, node: NodeGodot, scripts=None) -> list[ExtResourceGodot]:
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