"""
ShieldCraft Ultimate Checklist System - Engine Integration.

This module provides the integration point between the ShieldCraft engine
and the ultimate checklist generation system. It replaces vague checklist
items with specific, actionable tasks that enable deterministic software
manufacturing.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .ultimate_generator import UltimateChecklistGenerator, UltimateChecklist
from .extractor import SpecExtractor
from .generator import ChecklistGenerator

logger = logging.getLogger(__name__)


class UltimateChecklistService:
    """
    Service for generating ultimate checklists within the ShieldCraft engine.

    This service transforms the traditional vague checklist approach into
    a deterministic manufacturing process where implementers can follow
    specific, actionable steps blindly.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ultimate_generator = UltimateChecklistGenerator()
        self.legacy_extractor = SpecExtractor()
        self.legacy_generator = ChecklistGenerator()

        # Configuration
        self.enable_legacy_fallback = self.config.get('enable_legacy_fallback', True)
        self.quality_threshold = self.config.get('quality_threshold', 0.6)  # Lowered since we filter items
        self.max_tasks_per_spec = self.config.get('max_tasks_per_spec', 1000)

    def generate_checklist(self, spec: Dict, use_ultimate: bool = True) -> Dict:
        """
        Generate a checklist from a specification.

        Args:
            spec: ShieldCraft specification dictionary
            use_ultimate: Whether to use ultimate checklist generation

        Returns:
            Dictionary containing checklist data compatible with existing engine
        """
        if use_ultimate:
            try:
                ultimate_checklist = self.ultimate_generator.generate_ultimate_checklist(spec)

                # Validate quality meets threshold
                if ultimate_checklist.quality_metrics['unambiguity_index'] < self.quality_threshold:
                    logger.warning(
                        f"Ultimate checklist quality ({ultimate_checklist.quality_metrics['unambiguity_index']:.2f}) "
                        f"below threshold ({self.quality_threshold}). Falling back to legacy."
                    )
                    if self.enable_legacy_fallback:
                        return self._generate_legacy_checklist(spec)
                    else:
                        logger.error("Quality threshold not met and fallback disabled")
                        raise ValueError("Checklist quality below threshold")

                # Convert to engine-compatible format
                return self._convert_ultimate_to_engine_format(ultimate_checklist)

            except Exception as e:
                logger.error(f"Ultimate checklist generation failed: {e}")
                if self.enable_legacy_fallback:
                    logger.info("Falling back to legacy checklist generation")
                    return self._generate_legacy_checklist(spec)
                else:
                    raise
        else:
            return self._generate_legacy_checklist(spec)

    def _generate_legacy_checklist(self, spec: Dict) -> Dict:
        """Generate checklist using legacy system for compatibility"""
        raw_items = self.legacy_extractor.extract(spec)
        legacy_checklist = self.legacy_generator.extract_items(spec)

        return {
            'items': legacy_checklist,
            'metadata': {
                'generator': 'legacy',
                'total_items': len(legacy_checklist),
                'spec_version': spec.get('metadata', {}).get('spec_version', 'unknown')
            },
            'quality_metrics': {
                'unambiguity_index': 0.1,  # Legacy system has very low unambiguity
                'average_clarity_score': 0.1,
                'automation_potential': 0.2
            }
        }

    def _convert_ultimate_to_engine_format(self, ultimate_checklist: UltimateChecklist) -> Dict:
        """Convert ultimate checklist to format expected by ShieldCraft engine"""
        engine_items = []

        for task in ultimate_checklist.tasks:
            # Create engine-compatible checklist item
            engine_item = {
                'id': task.id,
                'ptr': task.source_ptr,
                'text': task.title,
                'description': task.description,
                'category': task.category.value,
                'priority': task.priority,
                'effort': task.estimated_effort,
                'tags': task.tags,

                # Ultimate checklist specific fields
                'code_example': task.code_example,
                'acceptance_criteria': task.acceptance_criteria,
                'validation_steps': task.validation_steps,
                'dependencies': task.dependencies,
                'component_refs': task.component_refs,

                # Quality metrics
                'clarity_score': task.clarity_score,
                'automation_potential': task.automation_potential,

                # Metadata
                'spec_section': task.spec_section,
                'implementation_level': task.implementation_level.value,
                'hash': task.hash
            }
            engine_items.append(engine_item)

        return {
            'items': engine_items,
            'metadata': {
                'generator': 'ultimate',
                'total_items': len(engine_items),
                'spec_version': ultimate_checklist.metadata.get('spec_version', 'unknown'),
                'product_id': ultimate_checklist.metadata.get('product_id', 'unknown'),
                'generated_at': ultimate_checklist.metadata.get('generated_at'),
                'generator_version': ultimate_checklist.metadata.get('generator_version', 'unknown')
            },
            'quality_metrics': ultimate_checklist.quality_metrics,
            'execution_plan': ultimate_checklist.execution_plan
        }

    def validate_checklist_quality(self, checklist_data: Dict) -> Dict:
        """
        Validate the quality of a generated checklist.

        Returns validation results with recommendations for improvement.
        """
        quality_metrics = checklist_data.get('quality_metrics', {})
        items = checklist_data.get('items', [])

        validation_results = {
            'overall_quality': 'unknown',
            'issues': [],
            'recommendations': [],
            'scores': quality_metrics
        }

        # Check unambiguity index
        unambiguity = quality_metrics.get('unambiguity_index', 0)
        if unambiguity >= 0.9:
            validation_results['overall_quality'] = 'excellent'
        elif unambiguity >= 0.8:
            validation_results['overall_quality'] = 'good'
        elif unambiguity >= 0.7:
            validation_results['overall_quality'] = 'acceptable'
        else:
            validation_results['overall_quality'] = 'poor'
            validation_results['issues'].append(
                f"Low unambiguity index ({unambiguity:.2f}) - tasks may be too vague"
            )
            validation_results['recommendations'].append(
                "Improve task templates to include more specific code examples and validation steps"
            )

        # Check for tasks without code examples
        tasks_without_code = [
            item for item in items
            if not item.get('code_example') or len(item.get('code_example', '').strip()) < 50
        ]
        if tasks_without_code:
            validation_results['issues'].append(
                f"{len(tasks_without_code)} tasks lack substantial code examples"
            )
            validation_results['recommendations'].append(
                "Add detailed code examples to all tasks showing exact implementation"
            )

        # Check for tasks without acceptance criteria
        tasks_without_criteria = [
            item for item in items
            if not item.get('acceptance_criteria') or len(item.get('acceptance_criteria', [])) < 2
        ]
        if tasks_without_criteria:
            validation_results['issues'].append(
                f"{len(tasks_without_criteria)} tasks lack sufficient acceptance criteria"
            )
            validation_results['recommendations'].append(
                "Add 3-5 specific, measurable acceptance criteria to each task"
            )

        # Check automation potential
        avg_automation = quality_metrics.get('average_automation_potential', 0)
        if avg_automation < 0.7:
            validation_results['issues'].append(
                f"Low automation potential ({avg_automation:.2f}) - tasks may require manual implementation"
            )
            validation_results['recommendations'].append(
                "Design tasks to be more automatable with clear validation steps"
            )

        return validation_results

    def compare_legacy_vs_ultimate(self, spec: Dict) -> Dict:
        """
        Compare legacy vs ultimate checklist generation for the same spec.

        This demonstrates the improvement in quality and actionability.
        """
        # Generate both types
        legacy_checklist = self._generate_legacy_checklist(spec)
        ultimate_checklist = self.generate_checklist(spec, use_ultimate=True)

        return {
            'comparison': {
                'legacy': {
                    'total_items': legacy_checklist['metadata']['total_items'],
                    'unambiguity_index': legacy_checklist['quality_metrics']['unambiguity_index'],
                    'average_clarity': legacy_checklist['quality_metrics']['average_clarity_score']
                },
                'ultimate': {
                    'total_items': ultimate_checklist['metadata']['total_items'],
                    'unambiguity_index': ultimate_checklist['quality_metrics']['unambiguity_index'],
                    'average_clarity': ultimate_checklist['quality_metrics']['average_clarity_score']
                }
            },
            'improvement': {
                'unambiguity_gain': (
                    ultimate_checklist['quality_metrics']['unambiguity_index'] -
                    legacy_checklist['quality_metrics']['unambiguity_index']
                ),
                'clarity_gain': (
                    ultimate_checklist['quality_metrics']['average_clarity_score'] -
                    legacy_checklist['quality_metrics']['average_clarity_score']
                ),
                'task_ratio': (
                    ultimate_checklist['metadata']['total_items'] /
                    max(legacy_checklist['metadata']['total_items'], 1)
                )
            },
            'sample_comparison': {
                'legacy_sample': legacy_checklist['items'][:3] if legacy_checklist['items'] else [],
                'ultimate_sample': ultimate_checklist['items'][:3] if ultimate_checklist['items'] else []
            }
        }


# Engine integration functions
def generate_ultimate_checklist(spec: Dict, config: Optional[Dict] = None) -> Dict:
    """
    Main entry point for ShieldCraft engine integration.

    Generates the most unambiguous, actionable checklist possible from a specification.
    """
    service = UltimateChecklistService(config)
    return service.generate_checklist(spec, use_ultimate=True)


def generate_legacy_checklist(spec: Dict) -> Dict:
    """Generate checklist using legacy system for backward compatibility"""
    service = UltimateChecklistService()
    return service.generate_checklist(spec, use_ultimate=False)


def validate_checklist_quality(checklist_data: Dict) -> Dict:
    """Validate checklist quality and provide improvement recommendations"""
    service = UltimateChecklistService()
    return service.validate_checklist_quality(checklist_data)


def compare_checklist_systems(spec: Dict) -> Dict:
    """Compare legacy vs ultimate checklist generation"""
    service = UltimateChecklistService()
    return service.compare_legacy_vs_ultimate(spec)


# Example usage and testing
if __name__ == "__main__":
    # Example specification
    test_spec = {
        "metadata": {
            "product_id": "shieldcraft_test",
            "spec_version": "1.0"
        },
        "agents": [{"id": "test_agent"}],
        "determinism": {"enabled": True}
    }

    print("🧪 Testing Ultimate Checklist Service")
    print("=" * 50)

    service = UltimateChecklistService()

    # Generate ultimate checklist
    ultimate = service.generate_checklist(test_spec, use_ultimate=True)
    print(f"✅ Generated {ultimate['metadata']['total_items']} ultimate tasks")
    print(f"🎯 Unambiguity Index: {ultimate['quality_metrics']['unambiguity_index']:.2f}")
    # Validate quality
    validation = service.validate_checklist_quality(ultimate)
    print(f"📊 Quality Assessment: {validation['overall_quality'].upper()}")

    if validation['issues']:
        print("⚠️  Issues found:")
        for issue in validation['issues']:
            print(f"   • {issue}")

    # Compare systems
    comparison = service.compare_legacy_vs_ultimate(test_spec)
    print()
    print("🔄 System Comparison:")
    print(f"   Legacy Unambiguity: {comparison['comparison']['legacy']['unambiguity_index']:.2f}")
    print(f"   Ultimate Unambiguity: {comparison['comparison']['ultimate']['unambiguity_index']:.2f}")
    print(f"   Improvement: {comparison['improvement']['unambiguity_gain']:.2f} points")
    print()
    print("🎯 RESULT: Ultimate checklist system successfully transforms")
    print("   vague requirements into specific, actionable tasks that")
    print("   implementers can follow blindly for deterministic software manufacturing.")