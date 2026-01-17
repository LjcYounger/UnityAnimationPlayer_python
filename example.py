EXAMPLE = ['pygame', 'pyside']

print("Choose an example:")

for i, example in enumerate(EXAMPLE):
    print(f"{i+1}.{example}")

choice = int(input("Enter your choice: "))

import_path = f"examples.{EXAMPLE[choice-1]}_example"

__import__(import_path)