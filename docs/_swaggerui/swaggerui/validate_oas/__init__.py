import json
import os

from jsonschema import validate

with open(os.path.join(os.path.dirname(__file__), "2024-10-18")) as fp:
    openapi30_schema = json.loads(fp.read())


def validate_openapi30(instance):
    validate(instance, schema=openapi30_schema)
