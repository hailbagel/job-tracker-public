import os

# ========================================
# CONFIG
# ========================================

ROOT_DIR = "."
IGNORE_FOLDERS = {
    ".venv",
    "__pycache__",
    ".git"
}

# ========================================
# TREE FUNCTION
# ========================================

def print_tree(directory, prefix=""):

    try:
        items = sorted(os.listdir(directory))
    except PermissionError:
        return

    for index, item in enumerate(items):

        path = os.path.join(directory, item)

        # Ignorieren
        if item in IGNORE_FOLDERS:
            continue

        connector = "└── " if index == len(items) - 1 else "├── "

        print(prefix + connector + item)

        if os.path.isdir(path):

            extension = "    " if index == len(items) - 1 else "│   "

            print_tree(path, prefix + extension)


# ========================================
# START
# ========================================

print("\n========================================")
print("PROJEKT STRUKTUR")
print("========================================\n")

print(ROOT_DIR)
print_tree(ROOT_DIR)

print("\n========================================")
print("FERTIG")
print("========================================")