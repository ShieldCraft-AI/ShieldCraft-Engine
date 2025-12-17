#!/usr/bin/env python3
"""
Repository sync and audit script.
Generates repo_state_sync.json, dsl_field_usage.json, shieldcraft_progress.json.
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def compute_sha256(path: Path) -> str:
    """Compute SHA256 hash of file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path: Path) -> int:
    """Count lines in file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0


def extract_imports(path: Path) -> Set[str]:
    """Extract imported module names from Python file."""
    imports = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except:
        pass
    return imports


def extract_all_exports(path: Path) -> List[str]:
    """Extract __all__ exports from Python module."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            return [elt.s for elt in node.value.elts if isinstance(elt, ast.Constant)]
    except:
        pass
    return []


def count_tests_in_file(path: Path) -> int:
    """Count test functions in test file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return len(re.findall(r'^\s*def\s+test_\w+', content, re.MULTILINE))
    except:
        return 0


def detect_stubs(path: Path) -> bool:
    """Detect if file contains stub/placeholder markers."""
    markers = ['PLACEHOLDER', 'STUB', 'TODO', 'raise NotImplementedError']
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return any(marker in content for marker in markers)
    except:
        return False


def find_json_pointers(content: str) -> Set[str]:
    """Find JSON pointer-like strings in content."""
    pointers = set()
    # Match strings like "/foo/bar" or "/foo/0/bar"
    pattern = r'["\']/([\w/\d]+)["\']'
    for match in re.finditer(pattern, content):
        pointer = '/' + match.group(1)
        if len(pointer) > 1 and '/' in pointer[1:]:
            pointers.add(pointer)
    return pointers


def extract_field_accesses(content: str) -> Set[str]:
    """Extract field access patterns from code."""
    fields = set()
    # Match .get('field'), ['field'], spec['field']
    patterns = [
        r"\.get\(['\"](\w+)['\"]\)",
        r"\[['\"](\w+)['\"]\]",
        r"resolve_pointer\(['\"]/([\w/]+)['\"]\)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            fields.add(match.group(1))
    return fields


def walk_repo(repo_root: Path) -> Dict[str, Any]:
    """Walk repository and collect all file information."""
    files = []
    directories = set()
    modules = []
    test_files = []
    import_graph = defaultdict(set)
    stubs = []
    all_py_files = []
    
    # Extensions to hash
    hash_exts = {'.py', '.json', '.yml', '.yaml', '.j2'}
    
    for root, dirs, filenames in os.walk(repo_root):
        # Skip hidden and common ignore dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', 'venv', '.venv'}]
        
        root_path = Path(root)
        rel_root = root_path.relative_to(repo_root)
        directories.add(str(rel_root))
        
        for filename in filenames:
            if filename.startswith('.'):
                continue
                
            file_path = root_path / filename
            rel_path = file_path.relative_to(repo_root)
            
            size = file_path.stat().st_size
            lines = count_lines(file_path)
            
            file_info = {
                'path': str(rel_path),
                'size_bytes': size,
                'line_count': lines,
            }
            
            # Compute hash for tracked extensions
            if file_path.suffix in hash_exts:
                file_info['sha256'] = compute_sha256(file_path)
            
            files.append(file_info)
            
            # Process Python files
            if file_path.suffix == '.py':
                all_py_files.append(rel_path)
                
                # Check for stubs
                if detect_stubs(file_path):
                    stubs.append(str(rel_path))
                
                # Build import graph
                imports = extract_imports(file_path)
                import_graph[str(rel_path)] = imports
                
                # Modules under src/
                if 'src' in root_path.parts:
                    exports = extract_all_exports(file_path)
                    modules.append({
                        'path': str(rel_path),
                        'exports': exports,
                        'imports': list(imports),
                    })
                
                # Test files under tests/
                if 'tests' in root_path.parts and filename.startswith('test_'):
                    test_count = count_tests_in_file(file_path)
                    test_files.append({
                        'path': str(rel_path),
                        'test_count': test_count,
                        'imports': list(imports),
                    })
    
    return {
        'files': files,
        'directories': sorted(directories),
        'modules': modules,
        'test_files': test_files,
        'import_graph': {k: list(v) for k, v in import_graph.items()},
        'stubs': stubs,
        'all_py_files': [str(p) for p in all_py_files],
    }


def detect_orphans(repo_data: Dict[str, Any]) -> List[str]:
    """Detect orphaned files not referenced in imports or tests."""
    import_graph = repo_data['import_graph']
    test_files = {t['path'] for t in repo_data['test_files']}
    
    # Files referenced in any import
    referenced = set()
    for imports in import_graph.values():
        referenced.update(imports)
    
    # Check which files are never imported and not test files
    orphans = []
    for py_file in repo_data['all_py_files']:
        if py_file not in test_files:
            # Extract module name from path
            module_name = py_file.replace('/', '.').replace('.py', '')
            if not any(module_name.startswith(ref) or ref in module_name for ref in referenced):
                orphans.append(py_file)
    
    return orphans


def detect_unused_modules(repo_data: Dict[str, Any]) -> List[str]:
    """Detect modules imported 0 times by other modules."""
    import_graph = repo_data['import_graph']
    test_imports = set()
    
    # Collect all imports from tests
    for test_file in repo_data['test_files']:
        test_imports.update(test_file['imports'])
    
    # Count imports per module
    import_counts = defaultdict(int)
    for source, imports in import_graph.items():
        if 'tests/' not in source:  # Only count non-test imports
            for imp in imports:
                import_counts[imp] += 1
    
    # Find modules with 0 imports but referenced in tests
    unused = []
    for module in repo_data['modules']:
        module_name = module['path'].replace('/', '.').replace('.py', '')
        if import_counts.get(module_name, 0) == 0:
            # Keep if referenced in tests
            if any(module_name in imp for imp in test_imports):
                continue
            unused.append(module['path'])
    
    return unused


def analyze_ast_spec_consistency(repo_root: Path, repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze AST builder and spec consistency."""
    ast_files = []
    ast_fields = set()
    spec_pointers = set()
    
    # Find AST builder files
    for file_info in repo_data['files']:
        path = Path(file_info['path'])
        if '/ast/' in str(path) or 'ast' in path.stem.lower():
            if path.suffix == '.py':
                ast_files.append(str(path))
                # Extract field accesses
                try:
                    with open(repo_root / path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    ast_fields.update(extract_field_accesses(content))
                    ast_fields.update(find_json_pointers(content))
                except:
                    pass
    
    # Parse spec examples
    spec_dirs = [repo_root / 'spec', repo_root / 'examples']
    for spec_dir in spec_dirs:
        if spec_dir.exists():
            for spec_file in spec_dir.rglob('*.json'):
                try:
                    with open(spec_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    spec_pointers.update(find_json_pointers(content))
                except:
                    pass
    
    # Find pointers not referenced in AST code
    missing_pointers = spec_pointers - ast_fields
    
    return {
        'ast_builder_files': ast_files,
        'ast_referenced_fields': sorted(ast_fields),
        'spec_pointers': sorted(spec_pointers),
        'missing_in_ast': sorted(missing_pointers),
    }


def analyze_checklist_consistency(repo_root: Path, repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze checklist and spec consistency."""
    checklist_files = []
    checklist_fields = set()
    schema_fields = set()
    
    # Find checklist files
    for file_info in repo_data['files']:
        path = Path(file_info['path'])
        if '/checklist/' in str(path) and path.suffix == '.py':
            checklist_files.append(str(path))
            try:
                with open(repo_root / path, 'r', encoding='utf-8') as f:
                    content = f.read()
                checklist_fields.update(extract_field_accesses(content))
                checklist_fields.update(find_json_pointers(content))
            except:
                pass
    
    # Parse schema files
    schema_dirs = [repo_root / 'spec' / 'schemas', repo_root / 'src']
    for schema_dir in schema_dirs:
        if schema_dir.exists():
            for schema_file in schema_dir.rglob('*schema*.json'):
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                    if 'properties' in schema:
                        schema_fields.update(schema['properties'].keys())
                    if 'definitions' in schema:
                        for def_name, def_schema in schema['definitions'].items():
                            if 'properties' in def_schema:
                                schema_fields.update(def_schema['properties'].keys())
                except:
                    pass
    
    # Find fields used by checklist but not in schema
    missing_in_schema = checklist_fields - schema_fields
    
    return {
        'checklist_files': checklist_files,
        'checklist_referenced_fields': sorted(checklist_fields),
        'schema_fields': sorted(schema_fields),
        'missing_in_schema': sorted(missing_in_schema),
    }


def compute_repo_fingerprint(files: List[Dict[str, Any]]) -> str:
    """Compute deterministic repo fingerprint."""
    h = hashlib.sha256()
    
    # Sort by path
    sorted_files = sorted(files, key=lambda f: f['path'])
    
    for file_info in sorted_files:
        path = file_info['path']
        file_hash = file_info.get('sha256', '')
        h.update(f"{path}:{file_hash}".encode('utf-8'))
    
    return h.hexdigest()


def compute_dsl_version(repo_root: Path) -> Tuple[str, Dict[str, str]]:
    """Compute DSL version and schema hashes."""
    schema_hashes = {}
    
    schema_dir = repo_root / 'spec' / 'schemas'
    if schema_dir.exists():
        for schema_file in schema_dir.glob('*.json'):
            schema_hashes[schema_file.name] = compute_sha256(schema_file)
    
    # Check for canonical marker
    template_file = repo_root / 'spec' / 'se_dsl_v1.template.json'
    schema_file = repo_root / 'spec' / 'schemas' / 'se_dsl_v1.schema.json'
    
    if template_file.exists() and schema_file.exists():
        try:
            with open(template_file) as f:
                template = json.load(f)
            with open(schema_file) as f:
                schema = json.load(f)
            
            # Simple heuristic: same top-level keys
            if set(template.keys()) == set(schema.get('properties', {}).keys()):
                return 'canonical', schema_hashes
        except:
            pass
    
    return 'legacy', schema_hashes


def generate_sync_files(repo_root: Path, write: bool = False) -> Dict[str, Any]:
    """Main sync generation logic."""
    results = {}
    
    try:
        # Walk repository
        repo_data = walk_repo(repo_root)
        
        # Detect orphans and unused modules
        orphans = detect_orphans(repo_data)
        unused_modules = detect_unused_modules(repo_data)
        
        # Analyze AST consistency
        ast_analysis = analyze_ast_spec_consistency(repo_root, repo_data)
        
        # Analyze checklist consistency
        checklist_analysis = analyze_checklist_consistency(repo_root, repo_data)
        
        # Compute repo fingerprint
        repo_fingerprint = compute_repo_fingerprint(repo_data['files'])
        
        # Compute DSL version
        dsl_version, schema_hashes = compute_dsl_version(repo_root)
        
        # Test summary
        total_tests = sum(t['test_count'] for t in repo_data['test_files'])
        tests_per_file = {t['path']: t['test_count'] for t in repo_data['test_files']}
        
        # Build repo_state_sync.json
        repo_state = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'repo_fingerprint': repo_fingerprint,
            'files': repo_data['files'],
            'modules': repo_data['modules'],
            'stubs': repo_data['stubs'],
            'orphaned_files': orphans,
            'unused_modules_candidates': unused_modules,
            'test_summary': {
                'total_tests': total_tests,
                'test_files': len(repo_data['test_files']),
                'tests_per_file': tests_per_file,
            },
        }
        results['repo_state_sync.json'] = repo_state
        
        # Build dsl_field_usage.json
        all_pointers = set(ast_analysis['spec_pointers'])
        covered_pointers = all_pointers - set(ast_analysis['missing_in_ast'])
        pointer_coverage = (len(covered_pointers) / len(all_pointers) * 100) if all_pointers else 0
        
        dsl_field_usage = {
            'ast_referenced_fields': ast_analysis['ast_referenced_fields'],
            'checklist_referenced_fields': checklist_analysis['checklist_referenced_fields'],
            'raw_access_patterns': [],  # Placeholder for runtime tracking
            'schema_fields': checklist_analysis['schema_fields'],
            'pointer_coverage': round(pointer_coverage, 2),
        }
        results['dsl_field_usage.json'] = dsl_field_usage
        
        # Build shieldcraft_progress.json
        # Try to load existing to preserve phase_number
        progress_file = repo_root / 'shieldcraft_progress.json'
        phase_number = 0
        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    existing = json.load(f)
                phase_number = existing.get('phase_number', 0)
            except:
                pass
        
        # Detect completed subsystems (heuristic: modules with no stubs, no orphans)
        completed_subsystems = []
        pending_subsystems = []
        for module in repo_data['modules']:
            if module['path'] not in repo_data['stubs'] and module['path'] not in orphans:
                completed_subsystems.append(module['path'])
            else:
                pending_subsystems.append(module['path'])
        
        # Open drift items
        drift_items = []
        drift_items.extend([{'type': 'stub', 'file': s} for s in repo_data['stubs'][:10]])
        drift_items.extend([{'type': 'orphan', 'file': o} for o in orphans[:10]])
        drift_items.extend([{'type': 'pointer_missing', 'pointer': p} for p in ast_analysis['missing_in_ast'][:10]])
        
        shieldcraft_progress = {
            'phase_number': phase_number,
            'last_sync': datetime.now(timezone.utc).isoformat(),
            'completed_subsystems': completed_subsystems[:20],
            'pending_subsystems': pending_subsystems[:20],
            'open_drift_items': drift_items,
            'dsl_version': dsl_version,
            'repo_fingerprint': repo_fingerprint,
        }
        # Augment progress with any generated files discovered in self-host manifests
        generated_files = []
        candidate_manifests = [repo_root / '.selfhost_outputs' / 'selfhost_preview.json', repo_root / '.selfhost_outputs' / 'manifest.json', repo_root / 'artifacts' / 'selfhost_preview.json']
        for mf in candidate_manifests:
            try:
                if mf.exists():
                    data = json.load(open(mf))
                    outs = data.get('outputs') or data.get('generated') or []
                    for o in outs:
                        p = o.get('path') if isinstance(o, dict) else None
                        if p:
                            generated_files.append(p)
            except Exception:
                # Non-fatal: ignore malformed manifests
                pass

        if generated_files:
            shieldcraft_progress['generated_files_from_manifests'] = sorted(set(generated_files))

        results['shieldcraft_progress.json'] = shieldcraft_progress
        
        # Build sync_report.json
        sync_report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_files': len(repo_data['files']),
                'total_modules': len(repo_data['modules']),
                'total_tests': total_tests,
                'stubs': len(repo_data['stubs']),
                'orphans': len(orphans),
                'unused_modules': len(unused_modules),
                'pointer_coverage': round(pointer_coverage, 2),
            },
            'inconsistencies': {
                'stubs': repo_data['stubs'][:10],
                'orphaned_files': orphans[:10],
                'unused_modules': unused_modules[:10],
                'pointers_missing_in_ast': ast_analysis['missing_in_ast'][:10],
                'fields_missing_in_schema': checklist_analysis['missing_in_schema'][:10],
            },
        }
        results['sync_report.json'] = sync_report
        
        # Write files if requested
        if write:
            # Ensure output directory exists
            selfhost_dir = repo_root / '.selfhost_outputs'
            selfhost_dir.mkdir(exist_ok=True)
            
            # Write main outputs
            for filename in ['repo_state_sync.json', 'dsl_field_usage.json', 'shieldcraft_progress.json']:
                output_path = repo_root / filename
                # Backup if exists
                if output_path.exists():
                    backup_path = output_path.with_suffix('.json.bak')
                    output_path.rename(backup_path)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results[filename], f, indent=2, sort_keys=True, ensure_ascii=False)
            
            # Write sync report
            sync_report_path = selfhost_dir / 'sync_report.json'
            with open(sync_report_path, 'w', encoding='utf-8') as f:
                json.dump(results['sync_report.json'], f, indent=2, sort_keys=True, ensure_ascii=False)
            
            # Generate sync_actions.json if drift items exist
            if drift_items:
                actions = []
                for item in drift_items[:20]:
                    action = {
                        'file': item.get('file', item.get('pointer', 'unknown')),
                        'category': item['type'],
                        'suggested_fix': f"Review and address {item['type']} issue",
                    }
                    actions.append(action)
                
                actions_path = selfhost_dir / 'sync_actions.json'
                with open(actions_path, 'w', encoding='utf-8') as f:
                    json.dump(actions, f, indent=2, sort_keys=True, ensure_ascii=False)
            
            # Copy to products/shieldcraft_engine/checklist/
            checklist_dir = repo_root / 'products' / 'shieldcraft_engine' / 'checklist'
            if checklist_dir.exists():
                for filename in ['repo_state_sync.json', 'dsl_field_usage.json', 'shieldcraft_progress.json']:
                    source = repo_root / filename
                    dest = checklist_dir / filename
                    if source.exists():
                        with open(source) as f:
                            content = f.read()
                        with open(dest, 'w', encoding='utf-8') as f:
                            f.write(content)
            
            # Validate generated files
            for filename in ['repo_state_sync.json', 'dsl_field_usage.json', 'shieldcraft_progress.json']:
                path = repo_root / filename
                with open(path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validate parseable
        
        return results
        
    except Exception as e:
        return {'error': str(e), 'file': '', 'exit_code': 1}


def main():
    parser = argparse.ArgumentParser(description='Generate repository sync and audit files')
    parser.add_argument('--write', action='store_true', help='Write output files')
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent.parent
    results = generate_sync_files(repo_root, write=args.write)
    
    if 'error' in results:
        print(json.dumps(results, indent=2))
        sys.exit(results['exit_code'])
    
    sys.exit(0)


if __name__ == '__main__':
    main()
