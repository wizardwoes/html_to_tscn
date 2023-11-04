from dataclasses import dataclass
from jinja2 import Environment, PackageLoader, select_autoescape


env = Environment(
    loader=PackageLoader("godot"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


from pathlib import Path
from bs4 import BeautifulSoup
import css_inline

from scanner import HtmlScanner

from node_parser import Parser

from godot import NodeGodot, SceneGodot, GDScriptResource


@dataclass
class SceneWriter:
    scene: SceneGodot
    output_dir: str
    out_fname: Path = Path("test.tscn")

    def render_scene(self) -> str:
        nodes = self.scene.flat_nodes()
        template = env.get_template("scene.tscn.j2")
        return template.render(
            fd=self.scene.fd,
            ext_resource=self.scene.ext_resources,
            nodes=nodes,
        )
    
    def render_script_resource(self, script) -> str:
        script_template = env.get_template("gdscript.gd.j2")
        return script_template.render(script=script)

    def write_out_scene(self) -> None:
        rendered = self.render_scene()

        outdir = Path(self.output_dir)
        outdir.mkdir(exist_ok=True)

        print(f"Write it out to {self.out_fname}")
        outfile_with_extension = Path(f"{self.out_fname}.tscn")
        with open(outdir / outfile_with_extension, "w", encoding="utf-8") as f:
            f.write(rendered)
            f.write("\n")

    def write_out_resources(self):
        outdir = Path(self.output_dir)
        outdir.mkdir(exist_ok=True)

        for resource in self.scene.ext_resources:
            match resource.resource:
                case GDScriptResource() as script:
                    renderable = self.render_script_resource(script)
                    outfile = Path(f"{resource.path}.gd")
                    with open(outdir / outfile, "w", encoding="utf-8") as f:
                        f.write(renderable)
                    print(f"Write it out to {Path(outdir / outfile)}")
                case _:
                    print("we dont write to file", resource.resource)


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

    parser = Parser(tokens, root_node=root_node)
    nodes = parser.parse()

    for child in nodes:
        root_node.add_child(child)

    # resources.extend(scripts)

    scene = SceneGodot(root_node)

    outfile = Path("page-90")
    base_dir = Path("godot_output")

    writer = SceneWriter(scene, base_dir, outfile)
    writer.write_out_scene()
    writer.write_out_resources()
