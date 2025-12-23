#!/usr/bin/env python3
"""
Flask Generator for ShieldCraft Engine

Generates a complete Flask application from specification files.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import chevron


class FlaskGenerator:
    """Generator for Flask applications"""

    def __init__(self, template_dir: str, output_dir: str, spec_file: str):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.spec_file = Path(spec_file)
        self.config = self.load_config()
        self.spec = self.load_spec()

    def load_config(self) -> Dict[str, Any]:
        """Load template configuration"""
        config_file = self.template_dir / "template.json"
        with open(config_file, 'r') as f:
            return json.load(f)

    def load_spec(self) -> Dict[str, Any]:
        """Load specification file"""
        with open(self.spec_file, 'r') as f:
            return json.load(f)

    def map_field_type_sql(self, field_type: str) -> str:
        """Map specification field types to SQLAlchemy types"""
        type_mapping = {
            'string': 'db.String(255)',
            'integer': 'db.Integer',
            'number': 'db.Float',
            'boolean': 'db.Boolean',
            'date': 'db.DateTime',
            'array': 'db.Text',  # Store as JSON string
            'object': 'db.Text'  # Store as JSON string
        }
        return type_mapping.get(field_type.lower(), 'db.String(255)')

    def map_field_type_marshmallow(self, field_type: str) -> str:
        """Map specification field types to Marshmallow types"""
        type_mapping = {
            'string': 'Str',
            'integer': 'Int',
            'number': 'Float',
            'boolean': 'Bool',
            'date': 'DateTime',
            'array': 'List(fields.Raw)',
            'object': 'Raw'
        }
        return type_mapping.get(field_type.lower(), 'Str')

    def get_field_type_display(self, field_type: str) -> str:
        """Get human-readable field type for documentation"""
        type_mapping = {
            'string': 'String',
            'integer': 'Integer',
            'number': 'Float',
            'boolean': 'Boolean',
            'date': 'DateTime',
            'array': 'Array',
            'object': 'Object'
        }
        return type_mapping.get(field_type.lower(), 'String')

    def process_entities(self) -> Dict[str, Any]:
        """Process entities from specification"""
        entities = []

        if 'entities' in self.spec:
            for entity in self.spec['entities']:
                entity_data = {
                    'name': entity['name'],
                    'name_lower': entity['name'].lower(),
                    'description': entity.get('description', f'Manage {entity["name"]} records'),
                    'fields': []
                }

                # Process fields
                for field in entity.get('fields', []):
                    field_data = {
                        'field_name': field['name'],
                        'field_type_sql': self.map_field_type_sql(field.get('type', 'string')),
                        'field_type_marshmallow': self.map_field_type_marshmallow(field.get('type', 'string')),
                        'field_type_display': self.get_field_type_display(field.get('type', 'string')),
                        'required': field.get('required', False),
                        'nullable': not field.get('required', False),
                        'description': field.get('description', ''),
                        'primary': False
                    }

                    # Mark first string field as primary for search
                    if field.get('type', 'string') == 'string' and not any(f.get('primary', False) for f in entity_data['fields']):
                        field_data['primary'] = True

                    entity_data['fields'].append(field_data)

                entities.append(entity_data)

        entity_schema_names = []
        for entity in entities:
            entity_schema_names.extend([
                f"{entity['name_lower']}_schema",
                f"{entity['name_lower']}s_schema", 
                f"{entity['name_lower']}_create_schema",
                f"{entity['name_lower']}_update_schema"
            ])
        
        return {
            'entities': entities,
            'entity_names': ', '.join([e['name'] for e in entities]),
            'entity_schema_names': ', '.join(entity_schema_names)
        }

    def generate_context(self) -> Dict[str, Any]:
        """Generate template context"""
        app_name = self.spec.get('name', 'shieldcraft-flask-app').lower().replace(' ', '-')
        app_title = self.spec.get('name', 'ShieldCraft Flask App')
        app_description = self.spec.get('description', 'Generated Flask application from ShieldCraft Engine')

        context = {
            'app_name': app_name,
            'app_title': app_title,
            'app_description': app_description,
            **self.process_entities()
        }

        return context

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a Mustache template with context"""
        with open(template_path, 'r') as f:
            template = f.read()

        rendered = chevron.render(template, context)
        # Unescape HTML entities that shouldn't be escaped in code
        rendered = rendered.replace('&quot;', '"')
        rendered = rendered.replace('&amp;', '&')
        return rendered

    def generate_file(self, template_file: str, output_file: str, context: Dict[str, Any]):
        """Generate a single file from template"""
        template_path = self.template_dir / template_file
        output_path = self.output_dir / output_file

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render template
        content = self.render_template(template_path, context)

        # Write to output file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"Generated: {output_file}")

    def generate(self):
        """Generate the complete Flask application"""
        print(f"Generating Flask application: {self.spec.get('name', 'shieldcraft-flask-app')}")

        # Generate context
        context = self.generate_context()

        # Generate files from template configuration
        for file_config in self.config.get('files', []):
            self.generate_file(
                file_config['source'],
                file_config['destination'],
                context
            )

        print(f"Flask application generated successfully in {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate Flask application from specification')
    parser.add_argument('--template-dir', required=True, help='Template directory path')
    parser.add_argument('--output-dir', required=True, help='Output directory path')
    parser.add_argument('--spec-file', required=True, help='Specification file path')

    args = parser.parse_args()

    generator = FlaskGenerator(args.template_dir, args.output_dir, args.spec_file)
    generator.generate()


if __name__ == '__main__':
    main()