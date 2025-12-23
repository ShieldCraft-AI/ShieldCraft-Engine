#!/usr/bin/env python3
"""
Next.js Generator for ShieldCraft Engine

Generates a complete Next.js application from specification files.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import chevron


class NextJsGenerator:
    """Generator for Next.js applications"""

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

    def map_field_type_ts(self, field_type: str) -> str:
        """Map specification field types to TypeScript types"""
        type_mapping = {
            'string': 'string',
            'integer': 'number',
            'number': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'array': 'string[]',
            'object': 'Record<string, any>'
        }
        return type_mapping.get(field_type.lower(), 'any')

    def process_entities(self) -> Dict[str, Any]:
        """Process entities from specification"""
        entities = []
        entities_count = 0

        if 'entities' in self.spec:
            entities_count = len(self.spec['entities'])
            for entity in self.spec['entities']:
                entity_data = {
                    'name': entity['name'],
                    'name_lower': entity['name'].lower(),
                    'description': entity.get('description', f'Manage {entity["name"]} records'),
                    'fields': []
                }

                # Process fields
                primary_field = None
                for field in entity.get('fields', []):
                    field_data = {
                        'field_name': field['name'],
                        'field_name_human': field['name'].replace('_', ' ').title(),
                        'field_type_ts': self.map_field_type_ts(field.get('type', 'string')),
                        'required': field.get('required', False),
                        'primary': False
                    }

                    # Mark string fields as primary if no primary field set
                    if field.get('type', 'string') == 'string' and not primary_field:
                        field_data['primary'] = True
                        primary_field = field['name']

                    # Add type-specific flags for template rendering
                    field_type = field.get('type', 'string').lower()
                    field_data[f'type_{field_type}'] = True

                    entity_data['fields'].append(field_data)

                entities.append(entity_data)

        return {
            'entities': entities,
            'entities_count': entities_count
        }

    def generate_context(self) -> Dict[str, Any]:
        """Generate template context"""
        app_name = self.spec.get('name', 'shieldcraft-app').lower().replace(' ', '-')
        app_title = self.spec.get('name', 'ShieldCraft App')
        app_description = self.spec.get('description', 'Generated application from ShieldCraft Engine')

        context = {
            'app_name': app_name,
            'app_title': app_title,
            'app_description': app_description,
            'api_base_url': 'http://localhost:8000',
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

    def generate_dynamic_pages(self, context: Dict[str, Any]):
        """Generate dynamic pages for each entity"""
        entities = context.get('entities', [])

        for entity in entities:
            # Create entity directory
            entity_dir = self.output_dir / 'app' / entity['name_lower']
            entity_dir.mkdir(parents=True, exist_ok=True)

            # Generate entity list page
            list_page = f"""import EntityList from '@/components/EntityList'

export default function {entity['name']}Page() {{
  return <EntityList entityName="{entity['name']}" entityNamePlural="{entity['name']}s" />
}}
"""
            list_file = entity_dir / 'page.tsx'
            with open(list_file, 'w') as f:
                f.write(list_page)
            print(f"Generated: app/{entity['name_lower']}/page.tsx")

            # Generate new entity page
            new_page = f"""import EntityForm from '@/components/EntityForm'

export default function New{entity['name']}Page() {{
  return <EntityForm entityName="{entity['name']}" />
}}
"""
            new_dir = entity_dir / 'new'
            new_dir.mkdir(exist_ok=True)
            new_file = new_dir / 'page.tsx'
            with open(new_file, 'w') as f:
                f.write(new_page)
            print(f"Generated: app/{entity['name_lower']}/new/page.tsx")

            # Generate edit entity page
            edit_page = f"""import EntityForm from '@/components/EntityForm'

interface Edit{entity['name']}PageProps {{
  params: {{
    id: string
  }}
}}

export default function Edit{entity['name']}Page({{ params }}: Edit{entity['name']}PageProps) {{
  return <EntityForm entityName="{entity['name']}" entityId={{params.id}} />
}}
"""
            edit_dir = entity_dir / '[id]' / 'edit'
            edit_dir.mkdir(parents=True, exist_ok=True)
            edit_file = edit_dir / 'page.tsx'
            with open(edit_file, 'w') as f:
                f.write(edit_page)
            print(f"Generated: app/{entity['name_lower']}/[id]/edit/page.tsx")

    def generate(self):
        """Generate the complete Next.js application"""
        print(f"Generating Next.js application: {self.spec.get('name', 'shieldcraft-app')}")

        # Generate context
        context = self.generate_context()

        # Generate files from template configuration
        for file_config in self.config.get('files', []):
            self.generate_file(
                file_config['source'],
                file_config['destination'],
                context
            )

        # Generate dynamic pages for entities
        self.generate_dynamic_pages(context)

        print(f"Next.js application generated successfully in {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate Next.js application from specification')
    parser.add_argument('--template-dir', required=True, help='Template directory path')
    parser.add_argument('--output-dir', required=True, help='Output directory path')
    parser.add_argument('--spec-file', required=True, help='Specification file path')

    args = parser.parse_args()

    generator = NextJsGenerator(args.template_dir, args.output_dir, args.spec_file)
    generator.generate()


if __name__ == '__main__':
    main()