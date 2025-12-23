"""
AST shape validator - validates AST structure and required fields.
"""


def validate_shape(ast):
    """
    Validate AST shape and node structure.

    Args:
        ast: AST root node

    Returns:
        Dict with shape_errors list
    """
    shape_errors = []

    # Walk all nodes
    for node in ast.walk():
        # Check required fields
        if not hasattr(node, 'type') or node.type is None:
            shape_errors.append({
                "node_ptr": getattr(node, 'ptr', 'unknown'),
                "error": "missing_type_field"
            })

        if not hasattr(node, 'ptr'):
            shape_errors.append({
                "node_ptr": "unknown",
                "error": "missing_ptr_field"
            })

        # Check node type validity
        valid_types = {
            "root", "section", "task", "metadata", "model",
            "array", "object", "string", "number", "boolean"
        }

        if hasattr(node, 'type') and node.type and node.type not in valid_types:
            shape_errors.append({
                "node_ptr": node.ptr,
                "error": "invalid_node_type",
                "node_type": node.type
            })

        # Check children structure
        if hasattr(node, 'children'):
            if not isinstance(node.children, list):
                shape_errors.append({
                    "node_ptr": node.ptr,
                    "error": "children_not_list"
                })

    return {
        "shape_ok": len(shape_errors) == 0,
        "shape_errors": sorted(shape_errors, key=lambda x: x.get("node_ptr", ""))
    }
