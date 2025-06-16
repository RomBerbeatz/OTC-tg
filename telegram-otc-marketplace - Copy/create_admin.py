"""
Простой скрипт создания администратора
"""
import sqlite3
import hashlib
import os
from datetime import datetime

def simple_hash(password):
    """Простое хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_simple_admin():
    """Создает администратора максимально просто"""
    
    print("🚀 Простое создание администратора")
    print("=" * 40)
    
    db_path = "./marketplace.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных marketplace.db не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Смотрим что есть в таблице users
        print("🔍 Анализ таблицы users...")
        cursor.execute("PRAGMA table_info(users);")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Доступные колонки: {columns}")
        
        # Показываем существующих пользователей
        cursor.execute("SELECT * FROM users LIMIT 3;")
        existing = cursor.fetchall()
        print(f"👥 Существующих пользователей: {len(existing)}")
        for user in existing:
            print(f"   {user}")
        
        # Данные для администратора
        username = "admin"
        password = "password123"
        
        print(f"\n📝 Создаем пользователя:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        
        # Проверяем существование
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        if cursor.fetchone()[0] > 0:
            print(f"⚠️ Пользователь {username} уже существует!")
            
            # Обновляем существующего
            update_query = "UPDATE users SET "
            update_values = []
            
            if 'password' in columns:
                update_query += "password = ?"
                update_values.append(simple_hash(password))
            elif 'password_hash' in columns:
                update_query += "password_hash = ?"
                update_values.append(simple_hash(password))
            
            if 'role' in columns:
                if update_values:
                    update_query += ", "
                update_query += "role = ?"
                update_values.append('admin')
            
            update_query += " WHERE username = ?"
            update_values.append(username)
            
            if update_values:
                cursor.execute(update_query, update_values)
                print("✅ Пользователь обновлен до администратора")
        else:
            # Создаем нового пользователя
            insert_fields = ['username']
            insert_values = [username]
            
            # Добавляем пароль в любом доступном формате
            password_added = False
            for pwd_field in ['password', 'password_hash', 'hashed_password']:
                if pwd_field in columns and not password_added:
                    insert_fields.append(pwd_field)
                    insert_values.append(simple_hash(password))
                    password_added = True
                    break
            
            # Добавляем роль если есть
            if 'role' in columns:
                insert_fields.append('role')
                insert_values.append('admin')
            
            # Добавляем активность если есть
            if 'is_active' in columns:
                insert_fields.append('is_active')
                insert_values.append(1)
            
            if 'is_admin' in columns:
                insert_fields.append('is_admin')
                insert_values.append(1)
            
            # Дата создания
            if 'created_at' in columns:
                insert_fields.append('created_at')
                insert_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # Выполняем вставку
            placeholders = ', '.join(['?' for _ in insert_values])
            fields_str = ', '.join(insert_fields)
            
            query = f"INSERT INTO users ({fields_str}) VALUES ({placeholders})"
            print(f"🔧 SQL: {query}")
            print(f"📊 Значения: {insert_fields}")
            
            cursor.execute(query, insert_values)
            print("✅ Новый администратор создан")
        
        conn.commit()
        
        # Проверяем результат
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        admin_user = cursor.fetchone()
        
        print("\n🎉 Результат:")
        print("=" * 40)
        print(f"📋 Данные администратора: {admin_user}")
        print(f"👤 Username: {username}")
        print(f"🔐 Password: {password}")
        print("=" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_simple_admin()