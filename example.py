import os
import glob
import sys
import importlib

# Add src/ to path so unity_animation_player can be imported
_src_path = os.path.join(os.path.dirname(__file__), 'src')
if _src_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_src_path))

# Automatically scan all files ending with _example.py in the examples folder
examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
example_files = glob.glob(os.path.join(examples_dir, '*_example.py'))

# Extract example names from filenames (remove path and suffix)
EXAMPLE = []
for file_path in example_files:
    filename = os.path.basename(file_path)
    example_name = filename.replace('_example.py', '')
    EXAMPLE.append(example_name)


def _run_example(example_name):
    """Import and run the specified example module."""
    import_path = f"examples.{example_name}_example"
    try:
        module = importlib.import_module(import_path)
        if hasattr(module, 'main'):
            module.main()
    except Exception as e:
        print(f"Error running example '{example_name}': {e}")
        import traceback
        traceback.print_exc()


# Check if an example name is provided as a command-line argument
if len(sys.argv) > 1:
    example_name = sys.argv[1]
    # Verify if the example exists in the scanned list to prevent arbitrary imports
    if example_name in EXAMPLE:
        _run_example(example_name)
    else:
        print(f"Error: Example '{example_name}' not found.")
        print("Available examples:")
        for i, ex in enumerate(EXAMPLE):
            print(f"{i+1}. {ex}")
else:
    print("Choose an example:")

    for i, example in enumerate(EXAMPLE):
        print(f"{i+1}. {example}")

    choice = int(input("Enter your choice: "))

    _run_example(EXAMPLE[choice - 1])