#!/usr/bin/env python3
import os


def fix_blank_lines(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    blank_count = 0
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                new_lines.append(line)
        else:
            blank_count = 0
            new_lines.append(line)

    with open(file_path, 'w') as f:
        f.writelines(new_lines)


def main():
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                fix_blank_lines(os.path.join(root, file))


if __name__ == '__main__':
    main()
