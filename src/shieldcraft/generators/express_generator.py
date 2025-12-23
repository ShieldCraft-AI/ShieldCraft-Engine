#!/usr/bin/env python3
"""
ShieldCraft Engine - Express.js Code Generation Script
Express.js Framework Template Generator

This script generates a complete Express.js application from specifications.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List
import chevron  # Mustache template engine for Python
from datetime import datetime

class ExpressGenerator:
    """Express.js application generator using Mustache templates"""

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
        """Generate Mongoose models for entities"""
        model_templates = []

        for entity in entities:
            fields = []
            for field in entity.get('fields', []):
                field_type = self.map_field_type(field['type'])
                if field.get('required', True):
                    field_def = f"    {field['name']}: {{ type: {field_type}, required: true }}"
                else:
                    field_def = f"    {field['name']}: {{ type: {field_type} }}"
                fields.append(field_def)
            
            # Join fields with comma and newline, but don't add comma to first field
            if fields:
                fields_str = fields[0] + ''.join(',' + chr(10) + field for field in fields[1:])
            else:
                fields_str = ''

            model_template = f"""
const {entity['name']}Schema = new mongoose.Schema({{
{fields_str}
}}, baseOptions);

const {entity['name']} = mongoose.model('{entity['name']}', {entity['name']}Schema);
"""
            model_templates.append(model_template)

        # Add exports
        exports = [f"  {entity['name']}" for entity in entities]
        exports_str = f"\nmodule.exports = {{ {', '.join(exports)} }};"

        return "\n".join(model_templates) + exports_str

    def generate_entity_routes(self, entities: List[Dict[str, Any]]) -> str:
        """Generate API routes for entities"""
        route_templates = []

        for entity in entities:
            entity_name = entity['name'].lower()
            entity_class = entity['name']

            route_template = f"""
// {entity_class} routes
router.get('/{entity_name}',
  async (req, res) => {{
    try {{
      const {{ page = 1, limit = 10, search }} = req.query;
      const result = await {entity_name}Service.get{entity_class}s({{ page, limit, search }});
      sendResponse(res, 200, true, '{entity_class}s retrieved successfully', result);
    }} catch (error) {{
      console.error('Error fetching {entity_name}s:', error);
      sendResponse(res, 500, false, 'Failed to fetch {entity_name}s');
    }}
  }}
);

router.post('/{entity_name}',
  async (req, res) => {{
    try {{
      const {entity_name}Data = req.body;
      const {entity_name} = await {entity_name}Service.create{entity_class}({entity_name}Data);
      sendResponse(res, 201, true, '{entity_class} created successfully', {entity_name});
    }} catch (error) {{
      console.error('Error creating {entity_name}:', error);
      sendResponse(res, 500, false, 'Failed to create {entity_name}');
    }}
  }}
);

router.get('/{entity_name}/:id',
  async (req, res) => {{
    try {{
      const {{ id }} = req.params;
      const {entity_name} = await {entity_name}Service.get{entity_class}ById(id);
      if (!{entity_name}) {{
        return sendResponse(res, 404, false, '{entity_class} not found');
      }}
      sendResponse(res, 200, true, '{entity_class} retrieved successfully', {entity_name});
    }} catch (error) {{
      console.error('Error fetching {entity_name}:', error);
      sendResponse(res, 500, false, 'Failed to fetch {entity_name}');
    }}
  }}
);

router.put('/{entity_name}/:id',
  async (req, res) => {{
    try {{
      const {{ id }} = req.params;
      const updateData = req.body;
      const {entity_name} = await {entity_name}Service.update{entity_class}(id, updateData);
      if (!{entity_name}) {{
        return sendResponse(res, 404, false, '{entity_class} not found');
      }}
      sendResponse(res, 200, true, '{entity_class} updated successfully', {entity_name});
    }} catch (error) {{
      console.error('Error updating {entity_name}:', error);
      sendResponse(res, 500, false, 'Failed to update {entity_name}');
    }}
  }}
);

router.delete('/{entity_name}/:id',
  async (req, res) => {{
    try {{
      const {{ id }} = req.params;
      const deleted = await {entity_name}Service.delete{entity_class}(id);
      if (!deleted) {{
        return sendResponse(res, 404, false, '{entity_class} not found');
      }}
      sendResponse(res, 200, true, '{entity_class} deleted successfully');
    }} catch (error) {{
      console.error('Error deleting {entity_name}:', error);
      sendResponse(res, 500, false, 'Failed to delete {entity_name}');
    }}
  }}
);
"""
            route_templates.append(route_template)

        return "\n".join(route_templates)

    def map_field_type(self, field_type: str) -> str:
        """Map specification field types to Mongoose types"""
        type_mapping = {
            'string': 'String',
            'integer': 'Number',
            'number': 'Number',
            'boolean': 'Boolean',
            'date': 'Date',
            'array': '[String]',
            'object': 'mongoose.Schema.Types.Mixed'
        }
        return type_mapping.get(field_type.lower(), 'String')

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
        """Generate the complete Express.js application"""
        print(f"Generating Express.js application: {spec.get('app_name', 'My App')}")

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

        print(f"Express.js application generated successfully in {self.output_dir}")

    def generate_entity_services(self, entities: List[Dict[str, Any]]) -> str:
        """Generate service classes for entities"""
        service_templates = []

        for entity in entities:
            entity_class = entity['name']
            service_template = f"""
// {entity_class} service
class {entity_class}Service extends BaseService {{
  constructor() {{
    super({entity_class});
  }}

  async get{entity_class}s(options = {{}}) {{
    return await this.findAll(options);
  }}

  async get{entity_class}ById(id) {{
    return await this.findById(id);
  }}

  async create{entity_class}({entity_class.lower()}Data) {{
    // Add business logic here
    return await this.create({entity_class.lower()}Data);
  }}

  async update{entity_class}(id, updateData) {{
    // Add business logic here
    return await this.update(id, updateData);
  }}

  async delete{entity_class}(id) {{
    // Add business logic here
    return await this.delete(id);
  }}
}}
"""
            service_templates.append(service_template)

        # Add exports
        exports = [f"  {entity['name']}Service" for entity in entities]
        exports_str = f"\nmodule.exports = {{\n{chr(10).join(exports)}\n}};"

        return "\n".join(service_templates) + exports_str

    def generate_entity_tests(self, entities: List[Dict[str, Any]]) -> str:
        """Generate test functions for entities"""
        test_templates = []

        for entity in entities:
            entity_name = entity['name'].lower()
            test_template = f"""
// {entity['name']} tests
describe('{entity['name']}s API', () => {{
  test('should create a new {entity_name}', async () => {{
    const response = await request(app)
      .post('/api/{entity_name}s')
      .send(test{entity['name']});

    expect(response.status).toBe(201);
    expect(response.body.success).toBe(true);
  }});

  test('should get all {entity_name}s', async () => {{
    const response = await request(app).get('/api/{entity_name}s');
    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
  }});
}});
"""
            test_templates.append(test_template)

        return "\n".join(test_templates)

    def generate_api_endpoints(self, entities: List[Dict[str, Any]]) -> str:
        """Generate API endpoint documentation"""
        endpoint_docs = []

        for entity in entities:
            entity_name = entity['name'].lower()
            docs = f"""### {entity['name']}
- `GET /api/{entity_name}s` - List {entity_name}s
- `POST /api/{entity_name}s` - Create {entity_name}
- `GET /api/{entity_name}s/{{id}}` - Get {entity_name} by ID
- `PUT /api/{entity_name}s/{{id}}` - Update {entity_name}
- `DELETE /api/{entity_name}s/{{id}}` - Delete {entity_name}"""
            endpoint_docs.append(docs)

        return "\n\n".join(endpoint_docs)

def main():
    parser = argparse.ArgumentParser(description='Generate Express.js application')
    parser.add_argument('--template-dir', required=True, help='Template directory')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--spec-file', required=True, help='Specification JSON file')

    args = parser.parse_args()

    # Load specification
    with open(args.spec_file, 'r') as f:
        spec = json.load(f)

    # Generate application
    generator = ExpressGenerator(args.template_dir, args.output_dir)
    generator.generate(spec)

if __name__ == "__main__":
    main()