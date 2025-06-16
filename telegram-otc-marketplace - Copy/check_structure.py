import os

def explore_directory(path, level=0):
    """Рекурсивно исследует структуру директорий"""
    indent = "  " * level
    items = []
    
    try:
        for item in sorted(os.listdir(path)):
            if item.startswith('.') or item == '__pycache__' or item == 'venv':
                continue
                
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print(f"{indent}📁 {item}/")
                if level < 2:  # Ограничиваем глубину
                    explore_directory(item_path, level + 1)
            else:
                if item.endswith(('.py', '.txt', '.md', '.env', '.db')):
                    print(f"{indent}📄 {item}")
    except PermissionError:
        print(f"{indent}❌ Нет доступа к {path}")

print("🔍 Полная структура проекта:")
explore_directory(".")