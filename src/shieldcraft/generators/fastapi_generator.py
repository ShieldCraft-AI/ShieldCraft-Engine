#!/usr/bin/env python3
"""
ShieldCraft Engine - Code Generation Script
FastAPI Framework Template Generator

This script generates a complete FastAPI application from specifications.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import chevron  # Mustache template engine for Python
from datetime import datetime

class FastAPIGenerator:
    """FastAPI application generator using Mustache templates"""

    def __init__(self, template_dir: str, output_dir: str):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load template configuration"""
        config_file = self.template_dir / "template.json"
        with open(config_file, 'r') as f:
            return json.load(f)

    def generate_entity_models(self, entities: List[Dict[str, Any]]) -> str:
        """Generate Pydantic models for entities"""
        model_templates = []

        for entity in entities:
            fields = []
            for field in entity.get('fields', []):
                field_type = self.map_field_type(field['type'])
                field_def = f"    {field['name']}: {field_type}"
                if not field.get('required', True):
                    field_def += " = None"
                fields.append(field_def)

            model_template = f"""
class {entity['name']}(BaseEntity):
{chr(10).join(fields)}
"""
            model_templates.append(model_template)

        return "\n".join(model_templates)

    def generate_entity_routes(self, entities: List[Dict[str, Any]]) -> str:
        """Generate API routes for entities"""
        route_templates = []

        for entity in entities:
            entity_name = entity['name'].lower()
            entity_class = entity['name']

            route_template = f"""
# {entity_class} routes
@router.get("/{entity_name}/", response_model=PaginatedResponse)
async def get_{entity_name}s(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    service = {entity_class}Service(db)
    return service.get_all(skip=(page-1)*limit, limit=limit)

@router.post("/{entity_name}/")
async def create_{entity_name}(
    {entity_name}_data: {entity_class}Create,
    db: Session = Depends(get_db)
):
    service = {entity_class}Service(db)
    return service.create({entity_name}_data.dict())

@router.get("/{entity_name}/{{{entity_name}_id}}")
async def get_{entity_name}(
    {entity_name}_id: int,
    db: Session = Depends(get_db)
):
    service = {entity_class}Service(db)
    result = service.get_by_id({entity_name}_id)
    if not result:
        raise HTTPException(status_code=404, detail="{entity_class} not found")
    return result

@router.put("/{entity_name}/{{{entity_name}_id}}")
async def update_{entity_name}(
    {entity_name}_id: int,
    {entity_name}_data: {entity_class}Update,
    db: Session = Depends(get_db)
):
    service = {entity_class}Service(db)
    result = service.update({entity_name}_id, {entity_name}_data.dict())
    if not result:
        raise HTTPException(status_code=404, detail="{entity_class} not found")
    return result

@router.delete("/{entity_name}/{{{entity_name}_id}}")
async def delete_{entity_name}(
    {entity_name}_id: int,
    db: Session = Depends(get_db)
):
    service = {entity_class}Service(db)
    success = service.delete({entity_name}_id)
    if not success:
        raise HTTPException(status_code=404, detail="{entity_class} not found")
    return {{"message": "{entity_class} deleted successfully"}}
"""
            route_templates.append(route_template)

        return "\n".join(route_templates)

    def map_field_type(self, field_type: str) -> str:
        """Map specification field types to Python/Pydantic types"""
        type_mapping = {
            'string': 'str',
            'integer': 'int',
            'number': 'float',
            'boolean': 'bool',
            'date': 'datetime',
            'array': 'List[str]',
            'object': 'Dict[str, Any]'
        }
        return type_mapping.get(field_type.lower(), 'str')

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a Mustache template with context"""
        with open(template_path, 'r') as f:
            template = f.read()

        rendered = chevron.render(template, context)
        # Unescape HTML entities that shouldn't be escaped in code
        rendered = rendered.replace('&quot;', '"')
        rendered = rendered.replace('&amp;', '&')
        rendered = rendered.replace('&lt;', '<')
        rendered = rendered.replace('&gt;', '>')
        return rendered

    def generate(self, spec: Dict[str, Any]) -> None:
        """Generate the complete FastAPI application"""
        print(f"Generating FastAPI application: {spec.get('app_name', 'My App')}")

        # Prepare context
        context = spec.copy()
        context.update({
            'generated_at': datetime.now().isoformat(),
            'generator_version': '1.0.0'
        })

        # Generate entity-specific content
        entities = spec.get('entities', [])
        context['entity_models'] = self.generate_entity_models(entities)
        context['entity_routes'] = self.generate_entity_routes(entities)
        context['entity_services'] = self.generate_entity_services(entities)
        context['entity_tests'] = self.generate_entity_tests(entities)
        context['api_endpoints'] = self.generate_api_endpoints(entities)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate each file
        for file_config in self.config['files']:
            template_path = self.template_dir / file_config['template']
            output_path = self.output_dir / file_config['output']

            if template_path.exists():
                # Create subdirectories if needed
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Render and write
                content = self.render_template(str(template_path), context)
                with open(output_path, 'w') as f:
                    f.write(content)

                print(f"Generated: {output_path}")
            else:
                print(f"Warning: Template not found: {template_path}")

        print(f"FastAPI application generated successfully in {self.output_dir}")

    def generate_entity_services(self, entities: List[Dict[str, Any]]) -> str:
        """Generate service classes for entities"""
        service_templates = []

        for entity in entities:
            entity_class = entity['name']
            service_template = f"""
class {entity_class}Service(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)

    # Add custom methods here as needed
"""
            service_templates.append(service_template)

        return "\n".join(service_templates)

    def generate_entity_tests(self, entities: List[Dict[str, Any]]) -> str:
        """Generate test functions for entities"""
        test_templates = []

        for entity in entities:
            entity_name = entity['name'].lower()
            test_template = f"""
def test_{entity_name}_crud(test_client):
    # Test CRUD operations for {entity['name']}
    pass
"""
            test_templates.append(test_template)

        return "\n".join(test_templates)

    def generate_api_endpoints(self, entities: List[Dict[str, Any]]) -> str:
        """Generate API endpoint documentation"""
        endpoint_docs = []

        for entity in entities:
            entity_name = entity['name'].lower()
            docs = f"""### {entity['name']}
- `GET /{entity_name}/` - List {entity_name}s
- `POST /{entity_name}/` - Create {entity_name}
- `GET /{entity_name}/{{id}}` - Get {entity_name} by ID
- `PUT /{entity_name}/{{id}}` - Update {entity_name}
- `DELETE /{entity_name}/{{id}}` - Delete {entity_name}"""
            endpoint_docs.append(docs)

        return "\n\n".join(endpoint_docs)

def main():
    parser = argparse.ArgumentParser(description='Generate FastAPI application')
    parser.add_argument('--template-dir', required=True, help='Template directory')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--spec-file', required=True, help='Specification JSON file')

    args = parser.parse_args()

    # Load specification
    with open(args.spec_file, 'r') as f:
        spec = json.load(f)

    # Generate application
    generator = FastAPIGenerator(args.template_dir, args.output_dir)
    generator.generate(spec)

if __name__ == "__main__":
    main()