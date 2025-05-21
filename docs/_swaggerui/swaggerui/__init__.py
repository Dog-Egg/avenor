import importlib
import json
import os
import posixpath
import shutil
import uuid
from pathlib import Path
from urllib.parse import quote

import docutils
import docutils.nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from .validate_oas import validate_openapi30


def _import_string(dotpath: str):
    module, obj = dotpath.rsplit(".", 1)
    return getattr(importlib.import_module(module), obj)


def _config_required(argument):
    if argument is None:
        raise ValueError("argument required but none supplied")
    else:
        return json.loads(argument)


class SwaggerUI(SphinxDirective):
    required_arguments = 1
    option_spec = {"config": _config_required}

    def run(self):
        openapi = _import_string(self.arguments[0].strip())
        validate_openapi30(openapi)
        config = {"spec": openapi}
        if "config" in self.options:
            config.update(self.options["config"])

        iframe_id = "id_" + uuid.uuid4().hex
        iframe = f"""
        <div style="border: 1px solid #eeebee;">
            <iframe src="{posixpath.join(self.config.html_baseurl or "/", "swagger-ui.html?config=" + quote(json.dumps(config)))}" id={iframe_id} loading="lazy" frameborder="0" style="min-width: 100%; display: block;"></iframe>
            <script>
                window.onload = function() {{
                    iFrameResize({{checkOrigin: false}}, '#{iframe_id}')
                }}
            </script>
        </div>
        """

        return [docutils.nodes.raw(text=iframe, format="html")]


def setup(app: Sphinx):
    app.add_directive("swaggerui", SwaggerUI)

    static_path = Path(__file__).parent / "static"
    app.config.html_static_path.append(static_path.as_posix())
    app.add_js_file("iframeResizer.min.js")

    os.makedirs(app.outdir, exist_ok=True)
    shutil.copy(
        os.path.join(os.path.dirname(__file__), "swagger-ui.html"),
        os.path.join(app.outdir, "swagger-ui.html"),
    )

    return {}
