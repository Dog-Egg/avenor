import importlib
import os
import sys

sys.path.append(os.path.dirname(__file__))

project = "Avenor"

extensions = [
    "sphinx_swaggerui",
]


def process_swaggerui_config(app, config):
    pyobj: str = config["pyobj"]
    modulename, attrname = pyobj.rsplit(".")
    module = importlib.import_module(modulename)
    spec = getattr(module, attrname)
    return {
        "spec": spec,
    }


suppress_warnings = [
    "config.cache",
]
