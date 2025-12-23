#!/usr/bin/env python3
"""
ShieldCraft Engine - Code Generation Script
React Native Framework Template Generator

This script generates a complete React Native application from specifications.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import chevron  # Mustache template engine for Python
from datetime import datetime

class ReactNativeGenerator:
    """React Native application generator using Mustache templates"""

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

    def map_field_type_react(self, field_type: str) -> str:
        """Map specification field types to React Native/TypeScript types"""
        type_mapping = {
            'string': 'string',
            'integer': 'number',
            'number': 'number',
            'boolean': 'boolean',
            'date': 'Date',
            'array': 'any[]',
            'object': 'any'
        }
        return type_mapping.get(field_type.lower(), 'any')

    def map_field_type_formik(self, field_type: str) -> str:
        """Map specification field types to Formik input types"""
        type_mapping = {
            'string': 'text',
            'integer': 'number',
            'number': 'number',
            'boolean': 'checkbox',
            'date': 'date',
            'array': 'text',  # Handle as JSON string
            'object': 'text'  # Handle as JSON string
        }
        return type_mapping.get(field_type.lower(), 'text')

    def process_entities(self) -> Dict[str, Any]:
        """Process entities from specification"""
        entities = []
        for entity in self.spec.get('entities', []):
            processed_entity = {
                'name': entity['name'],
                'name_lower': entity['name'].lower(),
                'name_plural': entity['name'].lower() + 's',
                'fields': []
            }

            for field in entity.get('fields', []):
                processed_field = {
                    'name': field['name'],
                    'type': self.map_field_type_react(field['type']),
                    'formik_type': self.map_field_type_formik(field['type']),
                    'required': field.get('required', True),
                    'nullable': not field.get('required', True)
                }
                processed_entity['fields'].append(processed_field)

            entities.append(processed_entity)

        return {
            'entities': entities,
            'app_name': self.spec.get('name', 'ShieldCraftApp'),
            'app_description': self.spec.get('description', 'Generated React Native App')
        }

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a Mustache template with context"""
        with open(template_path, 'r') as f:
            template = f.read()
        return chevron.render(template, context)

    def generate_file(self, template_name: str, output_path: str, context: Dict[str, Any]):
        """Generate a file from template"""
        template_path = self.template_dir / template_name
        if template_path.exists():
            content = self.render_template(template_path, context)
            output_file = self.output_dir / output_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"Generated: {output_path}")

    def generate_entity_screens(self, context: Dict[str, Any]):
        """Generate entity-specific screen files"""
        for entity in context['entities']:
            entity_context = {**context, **entity}
            
            # Generate list screen
            self.generate_file(
                "src/screens/EntityListScreen.tsx.mustache",
                f"src/screens/{entity['name']}ListScreen.tsx",
                entity_context
            )
            
            # Generate detail screen
            self.generate_file(
                "src/screens/EntityDetailScreen.tsx.mustache",
                f"src/screens/{entity['name']}DetailScreen.tsx",
                entity_context
            )
            
            # Generate form screen
            self.generate_file(
                "src/screens/EntityFormScreen.tsx.mustache",
                f"src/screens/{entity['name']}FormScreen.tsx",
                entity_context
            )

    def generate(self):
        """Generate the complete React Native application"""
        context = self.process_entities()

        # Generate files based on template config
        for file_config in self.config.get('files', []):
            self.generate_file(
                file_config['template'],
                file_config['output'],
                context
            )

        # Generate entity-specific screens
        self.generate_entity_screens(context)

        print(f"React Native application generated successfully in {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate React Native application from specification')
    parser.add_argument('--template-dir', required=True, help='Template directory path')
    parser.add_argument('--output-dir', required=True, help='Output directory path')
    parser.add_argument('--spec-file', required=True, help='Specification file path')

    args = parser.parse_args()

    generator = ReactNativeGenerator(args.template_dir, args.output_dir, args.spec_file)
    generator.generate()


if __name__ == '__main__':
    main()