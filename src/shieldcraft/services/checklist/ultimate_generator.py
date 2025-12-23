"""
Ultimate Checklist Generation System for ShieldCraft Engine.

Transforms vague specification requirements into unambiguous, actionable checklist items
that implementers can follow blindly to build complete systems.

This system addresses the core problem: checklist items like "Implement object at /metadata"
are too vague for deterministic software manufacturing. Instead, we generate specific,
step-by-step instructions with code examples, validation criteria, and success metrics.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Union
from pathlib import Path
from enum import Enum

from shieldcraft.services.checklist.extractor import SpecExtractor
from shieldcraft.services.checklist.generator import ChecklistGenerator


class TaskCategory(Enum):
    """Categories of checklist tasks with priority ordering"""
    STRUCTURAL = "structural"      # Basic data structure implementation
    VALIDATION = "validation"      # Input validation and constraints
    BUSINESS_LOGIC = "business"    # Core business rules and logic
    INTEGRATION = "integration"    # API and service integration
    SECURITY = "security"          # Security requirements
    PERFORMANCE = "performance"    # Performance and optimization
    TESTING = "testing"           # Test implementation and validation
    DOCUMENTATION = "docs"         # Documentation and metadata


class ImplementationLevel(Enum):
    """Levels of implementation detail"""
    SKELETON = "skeleton"          # Basic structure only
    FUNCTIONAL = "functional"      # Working implementation
    ROBUST = "robust"             # Error handling and edge cases
    OPTIMIZED = "optimized"        # Performance optimized
    PRODUCTION = "production"      # Production-ready with monitoring


@dataclass
class ActionableTask:
    """A highly specific, actionable checklist task"""
    id: str
    title: str
    description: str
    category: TaskCategory
    implementation_level: ImplementationLevel
    priority: int  # 1-10, higher = more critical

    # Implementation details
    code_example: str
    acceptance_criteria: List[str]
    validation_steps: List[str]
    dependencies: List[str]  # IDs of prerequisite tasks
    estimated_effort: str   # "XS", "S", "M", "L", "XL"

    # Metadata
    source_ptr: str
    spec_section: str
    component_refs: List[str]
    tags: List[str]

    # Quality metrics
    clarity_score: float    # 0-1, how unambiguous the task is
    automation_potential: float  # 0-1, how automatable this task is

    # Execution tracking
    hash: str  # For change detection


@dataclass
class UltimateChecklist:
    """Complete checklist with execution planning"""
    tasks: List[ActionableTask]
    execution_plan: Dict[str, Any]
    quality_metrics: Dict[str, float]
    metadata: Dict[str, Any]


class UltimateChecklistGenerator:
    """
    Generates the most unambiguous, actionable checklists possible from specifications.

    Key innovations:
    1. Atomic, specific tasks instead of vague requirements
    2. Code examples for every task
    3. Acceptance criteria with validation steps
    4. Dependency mapping and execution ordering
    5. Quality metrics for continuous improvement
    """

    def __init__(self):
        self.extractor = SpecExtractor()
        self.legacy_generator = ChecklistGenerator()

        # Task templates for different specification patterns
        self.task_templates = self._load_task_templates()

    def _load_task_templates(self) -> Dict[str, Dict]:
        """Load task generation templates for different spec patterns"""
        return {
            "metadata_object": {
                "title": "Implement {key} metadata object with validation",
                "description": "Create a properly typed metadata object with input validation and schema enforcement",
                "code_example": """
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import re

class {Key}Metadata(BaseModel):
    \"\"\"{Key} metadata with validation\"\"\"

    # Required fields
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    version: str = Field(..., description="Version string")

    # Optional fields with defaults
    description: Optional[str] = Field(None, description="Detailed description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)

    # Validation
    @validator('version')
    def validate_version(cls, v):
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Version must be in format x.y.z')
        return v

    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
""",
                "acceptance_criteria": [
                    "Object validates all required fields",
                    "Input validation rejects invalid data",
                    "JSON serialization/deserialization works",
                    "Type hints are complete and accurate"
                ],
                "validation_steps": [
                    "Create instance with valid data - should succeed",
                    "Create instance with missing required field - should fail",
                    "Create instance with invalid version format - should fail",
                    "Serialize to JSON and deserialize back - should preserve data"
                ]
            },

            "boolean_flag": {
                "title": "Implement {key} boolean configuration flag",
                "description": "Add boolean configuration flag with proper defaults and validation",
                "code_example": """
from typing import Optional, Union

class Configuration:
    \"\"\"Application configuration with validation\"\"\"

    def __init__(self):
        self.{key}: bool = {default_value}

    @property
    def {key}(self) -> bool:
        \"\"\"Get {key} setting\"\"\"
        return self._{key}

    @{key}.setter
    def {key}(self, value: Union[bool, str]) -> None:
        \"\"\"Set {key} setting with validation\"\"\"
        if isinstance(value, str):
            # Handle string representations
            normalized = value.lower().strip()
            if normalized in ('true', '1', 'yes', 'on'):
                self._{key} = True
            elif normalized in ('false', '0', 'no', 'off'):
                self._{key} = False
            else:
                raise ValueError(f"Invalid boolean value: {value}")
        elif isinstance(value, bool):
            self._{key} = value
        else:
            raise TypeError(f"Expected bool or str, got {type(value)}")
""",
                "acceptance_criteria": [
                    "Boolean flag accepts True/False values",
                    "String representations ('true', 'false', etc.) are accepted",
                    "Invalid inputs raise appropriate errors",
                    "Default value is correctly set"
                ],
                "validation_steps": [
                    "Set flag to True - should work",
                    "Set flag to 'true' string - should work",
                    "Set flag to 'invalid' string - should fail",
                    "Check default value matches specification"
                ]
            },

            "list_implementation": {
                "title": "Implement {key} collection with item validation",
                "description": "Create a validated collection that ensures all items meet requirements",
                "code_example": """
from typing import List, Any, Union
from pydantic import BaseModel, Field, validator

class {Key}Collection(BaseModel):
    \"\"\"Validated collection of {key} items\"\"\"

    items: List[Any] = Field(default_factory=list, description="List of items")

    @validator('items', each_item=True)
    def validate_item(cls, v):
        \"\"\"Validate each item in the collection\"\"\"
        # Add specific validation logic here based on requirements
        if v is None:
            raise ValueError("Item cannot be None")
        return v

    def add_item(self, item: Any) -> None:
        \"\"\"Add item to collection with validation\"\"\"
        # Create temporary instance to validate
        temp_collection = self.__class__(items=self.items + [item])
        self.items = temp_collection.items

    def remove_item(self, index: int) -> Any:
        \"\"\"Remove item at index\"\"\"
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        raise IndexError(f"Index {index} out of range")

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Any:
        return self.items[index]
""",
                "acceptance_criteria": [
                    "Collection accepts valid items",
                    "Invalid items are rejected with clear errors",
                    "Items can be added and removed",
                    "Length and indexing work correctly"
                ],
                "validation_steps": [
                    "Add valid item - should succeed",
                    "Add invalid item - should fail with clear error",
                    "Remove existing item - should work",
                    "Access item by index - should work",
                    "Access invalid index - should fail appropriately"
                ]
            }
        }

    def generate_ultimate_checklist(self, spec: Dict) -> UltimateChecklist:
        """
        Generate the ultimate unambiguous checklist from a specification.

        This transforms vague requirements into specific, actionable tasks
        that can be followed blindly by implementers.
        """
        # Extract raw items using existing extractor
        raw_items = self.extractor.extract(spec)

        # Filter and deduplicate items to focus on meaningful structural elements
        meaningful_items = self._filter_meaningful_items(raw_items)

        # Transform each meaningful item into actionable tasks
        actionable_tasks = []
        for item in meaningful_items:
            tasks = self._transform_item_to_tasks(item, spec)
            actionable_tasks.extend(tasks)

        # Build dependency graph and execution plan
        execution_plan = self._build_execution_plan(actionable_tasks)

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(actionable_tasks)

        # Create metadata
        metadata = self._generate_metadata(spec, actionable_tasks)

        return UltimateChecklist(
            tasks=actionable_tasks,
            execution_plan=execution_plan,
            quality_metrics=quality_metrics,
            metadata=metadata
        )

    def _filter_meaningful_items(self, raw_items: List[Dict]) -> List[Dict]:
        """Filter items to focus on meaningful structural elements"""
        # Remove duplicates
        seen = set()
        deduplicated = []
        for item in raw_items:
            key = (item['ptr'], item['key'], str(item['value'])[:100])  # Include value preview for uniqueness
            if key not in seen:
                seen.add(key)
                deduplicated.append(item)

        # Filter for meaningful items
        meaningful = []
        for item in deduplicated:
            ptr = item['ptr']
            value = item['value']

            # Skip metadata and low-level items
            if any(skip in ptr.lower() for skip in ['$schema', 'canonical_spec_hash', 'hash']):
                continue

            # Skip primitive values that are just configuration
            if isinstance(value, (str, int, bool)) and len(ptr.split('/')) > 3:
                continue

            # Keep structural elements: objects, arrays, and top-level primitives
            if isinstance(value, (dict, list)) or len(ptr.split('/')) <= 3:
                meaningful.append(item)

        return meaningful

    def _transform_item_to_tasks(self, item: Dict, spec: Dict) -> List[ActionableTask]:
        """Transform a raw spec item into specific actionable tasks"""
        ptr = item["ptr"]
        key = item["key"]
        value = item["value"]

        # Determine task category and template
        template_key = self._classify_item(value)
        template = self.task_templates.get(template_key, self._get_fallback_template())

        # Generate task ID deterministically
        task_id = self._generate_task_id(ptr, key)

        # Customize template with actual values
        customized = self._customize_template(template, item, spec)

        # Create the actionable task
        task = ActionableTask(
            id=task_id,
            title=customized["title"],
            description=customized["description"],
            category=self._determine_category(ptr, value),
            implementation_level=ImplementationLevel.FUNCTIONAL,
            priority=self._calculate_priority(ptr, value),

            code_example=customized["code_example"],
            acceptance_criteria=customized["acceptance_criteria"],
            validation_steps=customized["validation_steps"],
            dependencies=[],  # Will be populated by dependency analysis
            estimated_effort=self._estimate_effort(value),

            source_ptr=ptr,
            spec_section=self._extract_section(ptr),
            component_refs=self._extract_component_refs(ptr, spec),
            tags=self._generate_tags(item),

            clarity_score=self._calculate_clarity_score(customized),
            automation_potential=self._calculate_automation_potential(customized),

            hash=self._calculate_task_hash(customized)
        )

        return [task]  # Could return multiple tasks for complex items

    def _classify_item(self, value: Any) -> str:
        """Classify item type for template selection"""
        if isinstance(value, dict):
            return "metadata_object"
        elif isinstance(value, list):
            return "list_implementation"
        elif isinstance(value, bool):
            return "boolean_flag"
        else:
            return "generic_value"

    def _get_fallback_template(self) -> Dict:
        """Fallback template for unrecognized item types"""
        return {
            "title": "Implement {key} value",
            "description": "Implement the {key} value according to specification requirements",
            "code_example": "# TODO: Implement {key}\n{key} = {value!r}",
            "acceptance_criteria": ["Value is implemented correctly"],
            "validation_steps": ["Verify value matches specification"]
        }

    def _customize_template(self, template: Dict, item: Dict, spec: Dict) -> Dict:
        """Customize template with actual item values"""
        customized = template.copy()

        # Replace placeholders
        replacements = {
            "{key}": item["key"],
            "{Key}": item["key"].title(),
            "{value}": repr(item["value"]),
            "{ptr}": item["ptr"]
        }

        for key, value in customized.items():
            if isinstance(value, str):
                for placeholder, replacement in replacements.items():
                    customized[key] = customized[key].replace(placeholder, replacement)
            elif isinstance(value, list):
                # Replace placeholders in each list item
                customized_list = []
                for list_item in value:
                    customized_item = list_item
                    for placeholder, replacement in replacements.items():
                        customized_item = customized_item.replace(placeholder, replacement)
                    customized_list.append(customized_item)
                customized[key] = customized_list

        return customized

    def _generate_task_id(self, ptr: str, key: str) -> str:
        """Generate deterministic task ID"""
        content = f"{ptr}:{key}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _determine_category(self, ptr: str, value: Any) -> TaskCategory:
        """Determine task category based on pointer and value"""
        if "security" in ptr.lower():
            return TaskCategory.SECURITY
        elif "test" in ptr.lower() or "validation" in ptr.lower():
            return TaskCategory.TESTING
        elif "performance" in ptr.lower():
            return TaskCategory.PERFORMANCE
        elif "metadata" in ptr.lower():
            return TaskCategory.STRUCTURAL
        elif isinstance(value, (dict, list)):
            return TaskCategory.STRUCTURAL
        else:
            return TaskCategory.BUSINESS_LOGIC

    def _calculate_priority(self, ptr: str, value: Any) -> int:
        """Calculate task priority (1-10)"""
        priority = 5  # Default medium priority

        # Boost priority for critical sections
        if any(critical in ptr.lower() for critical in ["security", "invariant", "required"]):
            priority += 3

        # Reduce priority for optional items
        if "optional" in ptr.lower() or isinstance(value, (dict, list)) and not value:
            priority -= 2

        return max(1, min(10, priority))

    def _estimate_effort(self, value: Any) -> str:
        """Estimate implementation effort"""
        if isinstance(value, dict):
            size = len(value)
            if size < 3:
                return "S"
            elif size < 10:
                return "M"
            else:
                return "L"
        elif isinstance(value, list):
            return "M"
        elif isinstance(value, bool):
            return "XS"
        else:
            return "S"

    def _extract_section(self, ptr: str) -> str:
        """Extract section name from pointer"""
        parts = ptr.strip("/").split("/")
        return parts[0] if parts else "root"

    def _extract_component_refs(self, ptr: str, spec: Dict) -> List[str]:
        """Extract component references from pointer and spec"""
        # Simple implementation - could be enhanced with deeper analysis
        refs = []
        ptr_lower = ptr.lower()

        if "agent" in ptr_lower:
            refs.append("agents")
        if "evidence" in ptr_lower:
            refs.append("evidence")
        if "artifact" in ptr_lower:
            refs.append("artifacts")

        return refs

    def _generate_tags(self, item: Dict) -> List[str]:
        """Generate tags for task categorization"""
        tags = []
        ptr = item["ptr"].lower()
        value = item["value"]

        if isinstance(value, dict):
            tags.append("object")
        elif isinstance(value, list):
            tags.append("collection")
        elif isinstance(value, bool):
            tags.append("flag")

        if "metadata" in ptr:
            tags.append("metadata")
        if "config" in ptr:
            tags.append("configuration")

        return tags

    def _calculate_clarity_score(self, customized: Dict) -> float:
        """Calculate how clear/unambiguous the task is (0-1)"""
        score = 0.5  # Base score

        # Boost for specific code examples
        if "code_example" in customized and len(customized["code_example"].strip()) > 50:
            score += 0.2

        # Boost for detailed acceptance criteria
        if "acceptance_criteria" in customized and len(customized["acceptance_criteria"]) > 2:
            score += 0.2

        # Boost for validation steps
        if "validation_steps" in customized and len(customized["validation_steps"]) > 2:
            score += 0.1

        return min(1.0, score)

    def _calculate_automation_potential(self, customized: Dict) -> float:
        """Calculate how automatable the task is (0-1)"""
        score = 0.3  # Base score

        # Tasks with clear validation steps are more automatable
        if "validation_steps" in customized and len(customized["validation_steps"]) > 0:
            score += 0.4

        # Tasks with code examples suggest automation potential
        if "code_example" in customized and "TODO" not in customized["code_example"]:
            score += 0.3

        return min(1.0, score)

    def _calculate_task_hash(self, customized: Dict) -> str:
        """Calculate hash for change detection"""
        content = json.dumps(customized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def _build_execution_plan(self, tasks: List[ActionableTask]) -> Dict[str, Any]:
        """Build execution plan with dependency ordering"""
        # Simple topological sort by priority for now
        # Could be enhanced with actual dependency analysis
        sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, t.id))

        return {
            "phases": [
                {
                    "name": "Foundation",
                    "tasks": [t.id for t in sorted_tasks if t.category == TaskCategory.STRUCTURAL]
                },
                {
                    "name": "Core Logic",
                    "tasks": [t.id for t in sorted_tasks if t.category == TaskCategory.BUSINESS_LOGIC]
                },
                {
                    "name": "Integration",
                    "tasks": [t.id for t in sorted_tasks if t.category == TaskCategory.INTEGRATION]
                },
                {
                    "name": "Quality Assurance",
                    "tasks": [t.id for t in sorted_tasks if t.category in [TaskCategory.TESTING, TaskCategory.VALIDATION]]
                }
            ],
            "total_tasks": len(tasks),
            "estimated_completion": self._estimate_completion_time(tasks)
        }

    def _calculate_quality_metrics(self, tasks: List[ActionableTask]) -> Dict[str, float]:
        """Calculate overall quality metrics for the checklist"""
        if not tasks:
            return {}

        avg_clarity = sum(t.clarity_score for t in tasks) / len(tasks)
        avg_automation = sum(t.automation_potential for t in tasks) / len(tasks)
        avg_priority = sum(t.priority for t in tasks) / len(tasks)

        return {
            "average_clarity_score": avg_clarity,
            "average_automation_potential": avg_automation,
            "average_priority": avg_priority,
            "total_actionable_tasks": len(tasks),
            "unambiguity_index": avg_clarity * 0.7 + avg_automation * 0.3
        }

    def _generate_metadata(self, spec: Dict, tasks: List[ActionableTask]) -> Dict[str, Any]:
        """Generate checklist metadata"""
        return {
            "spec_version": spec.get("metadata", {}).get("spec_version", "unknown"),
            "product_id": spec.get("metadata", {}).get("product_id", "unknown"),
            "generated_at": None,  # Would be set to current timestamp
            "generator_version": "ultimate_checklist_v1.0",
            "total_tasks": len(tasks),
            "task_categories": list(set(t.category.value for t in tasks)),
            "estimated_effort_distribution": self._calculate_effort_distribution(tasks)
        }

    def _estimate_completion_time(self, tasks: List[ActionableTask]) -> str:
        """Estimate total completion time"""
        effort_points = sum(self._effort_to_points(t.estimated_effort) for t in tasks)
        # Assume 8 points per day per developer
        days = effort_points / 8
        return f"{days:.1f} developer-days"

    def _effort_to_points(self, effort: str) -> int:
        """Convert effort estimate to story points"""
        return {"XS": 1, "S": 2, "M": 3, "L": 5, "XL": 8}.get(effort, 3)

    def _calculate_effort_distribution(self, tasks: List[ActionableTask]) -> Dict[str, int]:
        """Calculate distribution of effort estimates"""
        distribution = {}
        for task in tasks:
            distribution[task.estimated_effort] = distribution.get(task.estimated_effort, 0) + 1
        return distribution


# Integration with existing ShieldCraft engine
def generate_ultimate_checklist(spec: Dict) -> UltimateChecklist:
    """
    Main entry point for generating ultimate checklists.

    This replaces vague checklist items with specific, actionable tasks
    that implementers can follow blindly.
    """
    generator = UltimateChecklistGenerator()
    return generator.generate_ultimate_checklist(spec)


# Example usage
if __name__ == "__main__":
    # Example specification
    sample_spec = {
        "metadata": {
            "product_id": "shieldcraft_demo",
            "spec_version": "1.0",
            "name": "Demo Product"
        },
        "agents": [
            {"id": "validator", "type": "validation"}
        ],
        "determinism": {
            "enabled": True,
            "seed": 42
        }
    }

    checklist = generate_ultimate_checklist(sample_spec)

    print(f"Generated {len(checklist.tasks)} actionable tasks")
    print(f"Average clarity score: {checklist.quality_metrics['average_clarity_score']:.2f}")
    print(f"Unambiguity index: {checklist.quality_metrics['unambiguity_index']:.2f}")

    # Print first task as example
    if checklist.tasks:
        task = checklist.tasks[0]
        print(f"\nExample Task: {task.title}")
        print(f"Category: {task.category.value}")
        print(f"Priority: {task.priority}")
        print(f"Code Example:\n{task.code_example[:200]}...")