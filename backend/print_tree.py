import os

# Список папок, которые нужно игнорировать
IGNORED_FOLDERS = {'docs', '.git', '__pycache__'}

def print_tree(start_path, indent=""):
    try:
        entries = sorted(os.listdir(start_path))
    except PermissionError:
        # Если прав недостаточно для доступа к папке – пропускаем её
        return

    entries_count = len(entries)
    
    for index, entry in enumerate(entries):
        full_path = os.path.join(start_path, entry)
        
        # Пропускаем, если это папка и она указана для игнорирования
        if os.path.isdir(full_path) and entry in IGNORED_FOLDERS:
            continue
        
        connector = "└── " if index == entries_count - 1 else "├── "
        print(indent + connector + entry)
        
        if os.path.isdir(full_path):
            extension = "    " if index == entries_count - 1 else "│   "
            print_tree(full_path, indent + extension)

if __name__ == "__main__":
    # Укажите путь к корневой директории вашего проекта.
    project_root = "."  # Текущая директория
    print(project_root)
    print_tree(project_root)
