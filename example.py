import os
import glob

# Automatically scan all files ending with _example.py in the examples folder
examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
example_files = glob.glob(os.path.join(examples_dir, '*_example.py'))

# Extract example names from filenames (remove path and suffix)
EXAMPLE = []
for file_path in example_files:
    filename = os.path.basename(file_path)
    example_name = filename.replace('_example.py', '')
    EXAMPLE.append(example_name)

print("Choose an example:")

for i, example in enumerate(EXAMPLE):
    print(f"{i+1}.{example}")

choice = int(input("Enter your choice: "))

import_path = f"examples.{EXAMPLE[choice-1]}_example"

__import__(import_path)