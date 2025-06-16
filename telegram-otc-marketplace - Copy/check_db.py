"""
Проверка структуры существующей базы данных
"""
import sqlite3
import os

def check_database_structure():
    """Проверяет структуру существующей базы данных"""
    db_path = "./marketplace.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("🔍 Анализ существующей базы данных:")
        print("="*60)
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Таблица: {table_name}")
            
            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("   Колонки:")
            for column in columns:
                col_id, col_name, col_type, not_null, default, pk = column
                pk_mark = " (PK)" if pk else ""
                null_mark = " NOT NULL" if not_null else ""
                default_mark = f" DEFAULT {default}" if default else ""
                print(f"     🔸 {col_name}: {col_type}{pk_mark}{null_mark}{default_mark}")
            
            # Получаем количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"   📊 Записей: {count}")
            
            # Если это таблица users, покажем первые записи
            if table_name == 'users' and count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                records = cursor.fetchall()
                print("   🔍 Примеры записей:")
                for i, record in enumerate(records, 1):
                    print(f"     {i}. {record}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при анализе базы данных: {e}")

if __name__ == "__main__":
    check_database_structure()