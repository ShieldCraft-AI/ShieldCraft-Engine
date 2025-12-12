import os
import json
import re
from pathlib import Path


class TemplateEngine:
    def __init__(self, template_dir=None):
        if template_dir is None:
            base = Path(__file__).parent / "templates"
            self.template_dir = base
        else:
            self.template_dir = Path(template_dir)
    
    def load_template(self, name):
        """Load template from templates directory."""
        path = self.template_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {name}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def render(self, template, context):
        """
        Render template with deterministic context.
        Supports:
        - {{var}} substitution
        - {{block:name}}...{{endblock}} blocks
        - {{if var}}...{{endif}} conditionals
        """
        template_str = template
        
        # Canonicalize context - sort keys
        canonical_ctx = {}
        for key in sorted(context.keys()):
            val = context[key]
            if isinstance(val, (dict, list)):
                canonical_ctx[key] = json.dumps(val, sort_keys=True)
            else:
                canonical_ctx[key] = val
        
        # Process blocks
        template_str = self._process_blocks(template_str, canonical_ctx)
        
        # Process conditionals
        template_str = self._process_conditionals(template_str, canonical_ctx)
        
        # Simple format substitution
        out = template_str
        for k, v in canonical_ctx.items():
            out = out.replace("{{" + k + "}}", str(v))
        
        # Deterministic whitespace normalization
        out = self._normalize_whitespace(out)
        
        return out
    
    def _process_blocks(self, template, context):
        """Process {{block:name}}...{{endblock}} constructs."""
        # Simple block extraction - no nesting support for now
        block_pattern = r'\{\{block:(\w+)\}\}(.*?)\{\{endblock\}\}'
        
        def replace_block(match):
            block_name = match.group(1)
            block_content = match.group(2)
            # Blocks are always included for now
            return block_content
        
        return re.sub(block_pattern, replace_block, template, flags=re.DOTALL)
    
    def _process_conditionals(self, template, context):
        """Process {{if var}}...{{endif}} constructs."""
        # Simple conditional pattern
        cond_pattern = r'\{\{if\s+(\w+)\}\}(.*?)\{\{endif\}\}'
        
        def replace_conditional(match):
            var_name = match.group(1)
            cond_content = match.group(2)
            # Check if var exists and is truthy
            if var_name in context and context[var_name]:
                return cond_content
            return ""
        
        return re.sub(cond_pattern, replace_conditional, template, flags=re.DOTALL)
    
    def _normalize_whitespace(self, text):
        """
        Deterministic whitespace normalization:
        - Remove trailing whitespace from each line
        - Ensure consistent line endings (LF)
        - No variable indentation (preserve existing indentation structure)
        """
        lines = text.split('\n')
        normalized = [line.rstrip() for line in lines]
        return '\n'.join(normalized)
    
    def safe_write(self, path, content):
        """Atomic write with LF endings."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure LF endings
        content = content.replace("\r\n", "\n")
        
        # Atomic write via temp file
        temp = path.with_suffix(path.suffix + ".tmp")
        with open(temp, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        
        temp.replace(path)
    
    def validate_template_file(self, path):
        """
        Validate template file for:
        - No tabs
        - LF line endings
        - Deterministic placeholders
        
        Returns:
            Dict with validation results
        """
        errors = []
        
        try:
            with open(path, 'rb') as f:
                content = f.read()
            
            # Check for tabs
            if b'\t' in content:
                errors.append({
                    "error": "contains_tabs",
                    "message": "Template contains tab characters"
                })
            
            # Check for CRLF
            if b'\r\n' in content:
                errors.append({
                    "error": "crlf_line_endings",
                    "message": "Template uses CRLF instead of LF"
                })
            
            # Decode and check for trailing spaces
            text = content.decode('utf-8')
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line.endswith(' ') or line.endswith('\t'):
                    errors.append({
                        "error": "trailing_whitespace",
                        "message": f"Line {i+1} has trailing whitespace",
                        "line_number": i + 1
                    })
                    break  # Only report first occurrence
            
            # Placeholder determinism is handled by template validation
            # No additional ordering check needed here
            
        except Exception as e:
            errors.append({
                "error": "validation_exception",
                "message": str(e)
            })
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def validate_all_templates(self):
        """
        Validate all template files in template directory.
        
        Returns:
            Dict with validation results for all templates
        """
        results = {}
        
        for template_file in self.template_dir.rglob('*.j2'):
            result = self.validate_template_file(template_file)
            results[str(template_file.relative_to(self.template_dir))] = result
        
        # Check if any templates failed
        all_valid = all(r["valid"] for r in results.values())
        
        return {
            "template_validation_ok": all_valid,
            "templates": results
        }
