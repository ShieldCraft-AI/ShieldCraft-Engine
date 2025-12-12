import json, os, importlib
from inspect import getmembers, isclass, isfunction

SCHEMA_PATH = 'spec/schemas/se_dsl_v1.schema.json'
OUTPUT = 'artifacts/dsl_field_inventory.json'

# Load DSL schema
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    schema = json.load(f)

schema_fields = set()

def walk_schema(node, prefix=''):
    if isinstance(node, dict):
        for k, v in node.items():
            # Property key
            if k == 'properties' and isinstance(v, dict):
                for field in v.keys():
                    schema_fields.add(field)
            walk_schema(v, prefix)
    elif isinstance(node, list):
        for item in node:
            walk_schema(item, prefix)

walk_schema(schema)

# Runtime structural extraction
runtime_fields = set()

# Candidate modules to inspect
MODULE_ROOTS = [
    'shieldcraft.services',
    'shieldcraft.engine',
    'shieldcraft.dsl',
    'shieldcraft',
]

def collect_from_object(obj):
    # Look for attribute access patterns
    for name in dir(obj):
        if name.startswith('_'):
            continue
        # If it's a potential DSL field
        if name.islower() and len(name) > 1:
            runtime_fields.add(name)


def load_and_reflect():
    for root in MODULE_ROOTS:
        try:
            module = importlib.import_module(root)
        except Exception:
            continue

        for name, member in getmembers(module):
            try:
                if isclass(member):
                    collect_from_object(member)
                elif isfunction(member):
                    collect_from_object(member)
            except Exception:
                pass

load_and_reflect()

# Compare schema fields and runtime fields
missing_from_runtime = sorted(schema_fields - runtime_fields)
missing_from_schema = sorted(runtime_fields - schema_fields)

result = {
    'schema_fields': sorted(schema_fields),
    'runtime_fields': sorted(runtime_fields),
    'missing_from_runtime': missing_from_runtime,
    'missing_from_schema': missing_from_schema
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print('dsl_runtime_reflection_complete')
