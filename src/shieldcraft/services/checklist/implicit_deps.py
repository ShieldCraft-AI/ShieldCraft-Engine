"""
Implicit dependency extractor.
"""

import re


def extract_implicit_deps(spec):
    """
    Extract implicit dependencies from spec values.
    
    Detects patterns like:
    - "depends_on": "some_id"
    - "requires": ["id1", "id2"]
    - References in text fields
    
    Args:
        spec: Raw spec dict
    
    Returns:
        List of implicit dependency dicts
    """
    implicit_deps = []
    
    def scan_value(value, path="/"):
        """Recursively scan values for dependency patterns."""
        if isinstance(value, dict):
            # Check for explicit dependency fields
            if "depends_on" in value:
                dep_value = value["depends_on"]
                if isinstance(dep_value, str):
                    implicit_deps.append({
                        "source": path,
                        "target": dep_value,
                        "type": "depends_on"
                    })
                elif isinstance(dep_value, list):
                    for dep in dep_value:
                        if isinstance(dep, str):
                            implicit_deps.append({
                                "source": path,
                                "target": dep,
                                "type": "depends_on"
                            })
            
            if "requires" in value:
                req_value = value["requires"]
                if isinstance(req_value, str):
                    implicit_deps.append({
                        "source": path,
                        "target": req_value,
                        "type": "requires"
                    })
                elif isinstance(req_value, list):
                    for req in req_value:
                        if isinstance(req, str):
                            implicit_deps.append({
                                "source": path,
                                "target": req,
                                "type": "requires"
                            })
            
            # Recurse into nested dicts
            for key, val in value.items():
                scan_value(val, f"{path}/{key}")
        
        elif isinstance(value, list):
            for i, item in enumerate(value):
                scan_value(item, f"{path}/{i}")
        
        elif isinstance(value, str):
            # Look for reference patterns in text
            # Pattern: @ref:some_id or {{some_id}}
            ref_patterns = [
                r'@ref:(\w+)',
                r'\{\{(\w+)\}\}'
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, value)
                for match in matches:
                    implicit_deps.append({
                        "source": path,
                        "target": match,
                        "type": "text_reference"
                    })
    
    # Scan entire spec
    scan_value(spec)
    
    # Sort for determinism
    implicit_deps = sorted(implicit_deps, key=lambda x: (x["source"], x["target"]))
    
    return implicit_deps
