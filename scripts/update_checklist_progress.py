#!/usr/bin/env python3
"""
Script to update the progress bar in checklist.md based on checked items.
"""

import re
import os

def update_checklist_progress():
    checklist_path = os.path.join(os.path.dirname(__file__), '..', '.selfhost_outputs', 'checklist.md')
    if not os.path.exists(checklist_path):
        print(f"Checklist file not found: {checklist_path}")
        return

    with open(checklist_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    total_tasks = 0
    checked_tasks = 0

    for line in lines:
        if re.match(r'^\s*-\s*\[.\]', line):
            total_tasks += 1
            if '[x]' in line:
                checked_tasks += 1

    if total_tasks == 0:
        percent = 0
    else:
        percent = int((checked_tasks / total_tasks) * 100)

    # Update the width in CSS
    content = re.sub(r'(\.progress-bar\s*\{[^}]*width:\s*)\d+(%[^}]*\})', rf'\g<1>{percent}\g<2>', content)

    # Update the text in the div
    content = re.sub(r'(<div class="progress-bar">)\d+(% Complete</div>)', rf'\g<1>{percent}\g<2>', content)

    with open(checklist_path, 'w') as f:
        f.write(content)

    print(f"Updated progress: {checked_tasks}/{total_tasks} tasks checked ({percent}%)")

if __name__ == '__main__':
    update_checklist_progress()