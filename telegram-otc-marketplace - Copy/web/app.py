from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_migrate import Migrate
import os
import json
import hashlib
import hmac
import time
from urllib.parse import unquote
from datetime import datetime
from dotenv import load_dotenv

# Импорт моделей
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import db, User, Listing, Message, Category

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///marketplace.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db.init_app(app)
migrate = Migrate(app, db)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []

def verify_telegram_auth(init_data):
    """Проверка авторизации через Telegram WebApp"""
    try:
        if not init_data:
            return None
            
        parsed_data = {}
        for item in init_data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                parsed_data[key] = unquote(value)
        
        if 'hash' not in parsed_data or 'auth_date' not in parsed_data:
            return None
            
        received_hash = parsed_data.pop('hash', '')
        auth_date = int(parsed_data.get('auth_date', '0'))
        
        # Проверяем время (24 часа)
        current_time = int(time.time())
        if current_time - auth_date > 86400:
            return None
            
        # Создаем строку для проверки
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
        
        # Проверяем подпись
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == received_hash:
            user_data = json.loads(parsed_data.get('user', '{}'))
            return user_data
        
        return None
        
    except Exception as e:
        print(f"Ошибка авторизации: {e}")
        return None

def init_db():
    """Инициализация базы данных с тестовыми данными"""
    with app.app_context():
        db.create_all()
        
        # Создаем категории, если их нет
        if Category.query.count() == 0:
            categories = [
                Category(name='channel', display_name='Telegram каналы', icon='📢'),
                Category(name='account', display_name='Аккаунты соцсетей', icon='👤'),
                Category(name='other', display_name='Другое', icon='🎁')
            ]
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
            print("✅ Категории созданы")
        
        # Создаем тестового пользователя и объявления
        if User.query.count() == 0:
            # Тестовый пользователь RomBerbeatz
            test_user1 = User(
                id=123456789,
                username='RomBerbeatz',
                first_name='RomBerbeatz',
                is_admin=True
            )
            db.session.add(test_user1)
            
            # Второй тестовый пользователь
            test_user2 = User(
                id=987654321,
                username='testuser',
                first_name='TestUser'
            )
            db.session.add(test_user2)
            
            db.session.commit()
            
            for listing in listings:
                db.session.add(listing)
            
            db.session.commit()
            print("✅ Тестовые данные созданы")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    init_data = request.args.get('init_data', '')
    
    if init_data:
        user_data = verify_telegram_auth(init_data)
        if user_data:
            # Ищем или создаем пользователя
            user = User.query.get(user_data['id'])
            if not user:
                user = User(
                    id=user_data['id'],
                    username=user_data.get('username'),
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name'),
                    is_admin=user_data['id'] in ADMIN_IDS
                )
                db.session.add(user)
            else:
                # Обновляем данные при входе
                user.username = user_data.get('username')
                user.first_name = user_data.get('first_name', '')
                user.last_name = user_data.get('last_name')
                user.last_login = datetime.utcnow()
            
            db.session.commit()
            
            # Сохраняем в сессии
            session['user'] = user_data
            session['user_id'] = user_data['id']
            session['username'] = user_data.get('username', '')
            session['first_name'] = user_data.get('first_name', '')
            session['auth_time'] = datetime.utcnow().isoformat()
            
            return jsonify({'success': True, 'redirect': '/'})
    
    return jsonify({'success': False, 'error': 'Invalid auth data'})

@app.route('/create')
def create_listing():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('create_listing.html', user=session['user'])

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    user_listings = Listing.query.filter_by(seller_id=session['user_id']).order_by(Listing.created_at.desc()).all()
    user_messages = Message.query.filter_by(recipient_id=session['user_id']).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                         user=session['user'],
                         listings=[l.to_dict() for l in user_listings],
                         messages=[m.to_dict() for m in user_messages])

# API эндпоинты
@app.route('/api/user')
def api_user():
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 200
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'authenticated': False}), 200
    
    return jsonify({
        'user': session['user'],
        'user_data': user.to_dict(),
        'authenticated': True,
        'is_admin': user.is_admin,
        'auth_time': session.get('auth_time', '')
    })

@app.route('/api/stats')
def api_stats():
    total_listings = Listing.query.filter_by(status='active').count()
    total_users = User.query.filter_by(is_active=True).count()
    
    # Подсчет статистики
    total_views = db.session.query(db.func.sum(Listing.views)).scalar() or 0
    total_favorites = db.session.query(db.func.sum(Listing.favorites)).scalar() or 0
    avg_price = db.session.query(db.func.avg(Listing.price)).scalar() or 0
    
    # Статистика по категориям
    categories_stats = {}
    for category in Category.query.all():
        count = Listing.query.filter_by(category=category.name, status='active').count()
        categories_stats[category.name] = count
    
    return jsonify({
        'total_listings': total_listings,
        'total_users': total_users,
        'active_listings': total_listings,
        'avg_price': float(avg_price) if avg_price else 0,  # ИСПРАВЛЕНО: без деления на 100
        'total_views': total_views,
        'total_favorites': total_favorites,
        'categories': categories_stats,
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/listings')
def api_listings():
    category = request.args.get('category', '')
    search = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Базовый запрос
    query = Listing.query.filter_by(status='active')
    
    # Фильтрация
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            db.or_(
                Listing.title.ilike(f'%{search}%'),
                Listing.description.ilike(f'%{search}%')
            )
        )
    
    # Сортировка и пагинация
    query = query.order_by(Listing.created_at.desc())
    listings = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'listings': [listing.to_dict() for listing in listings.items],
        'total': listings.total,
        'pages': listings.pages,
        'current_page': page,
        'has_next': listings.has_next,
        'has_prev': listings.has_prev,
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/listings', methods=['POST'])
def api_create_listing():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        
        # Валидация
        required_fields = ['title', 'description', 'price', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Field {field} is required'}), 400
        
        # ИСПРАВЛЕНО: Новые требования валидации
        title = data['title'].strip()
        description = data['description'].strip()
        
        if len(title) < 5:
            return jsonify({'error': 'Title must be at least 5 characters'}), 400
        
        if len(description) < 10:
            return jsonify({'error': 'Description must be at least 10 characters'}), 400
        
        # ИСПРАВЛЕНО: Обработка цены как float без конвертации
        try:
            price = float(data['price'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price format'}), 400
        
        if price < 1.0 or price > 1000000.0:
            return jsonify({'error': 'Price must be between $1.0 and $1,000,000.0'}), 400
        
        # Валидация категории
        valid_categories = ['channel', 'account', 'other']
        if data['category'] not in valid_categories:
            return jsonify({'error': 'Invalid category'}), 400
        
        # Валидация подписчиков для каналов
        subscribers_count = 0
        if data['category'] == 'channel':
            try:
                subscribers_count = int(data.get('subscribers_count', 0))
                if subscribers_count <= 0:
                    return jsonify({'error': 'Subscribers count is required for channels'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid subscribers count'}), 400
        
        # ИСПРАВЛЕНО: Создаем объявление с ценой как есть
        new_listing = Listing(
            title=title,
            description=description,
            price=price,  # Сохраняем как есть: 1.3 остается 1.3
            currency=data.get('currency', 'USD'),
            category=data['category'],
            subscribers_count=subscribers_count,
            seller_id=session['user_id']
        )
        
        db.session.add(new_listing)
        db.session.commit()
        
        print(f"✅ Создано объявление: {new_listing.title} (ID: {new_listing.id}) цена: ${new_listing.price} от пользователя {session['first_name']}")
        
        return jsonify({
            'success': True,
            'listing': new_listing.to_dict(),
            'message': 'Объявление успешно создано!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка создания объявления: {e}")
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/api/listings/<int:listing_id>', methods=['DELETE'])
def api_delete_listing(listing_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    listing = Listing.query.get_or_404(listing_id)
    
    # Проверяем права доступа
    user = User.query.get(session['user_id'])
    if listing.seller_id != session['user_id'] and not user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    db.session.delete(listing)
    db.session.commit()
    
    print(f"🗑️ Удалено объявление: {listing.title} (ID: {listing_id})")
    
    return jsonify({'success': True, 'message': 'Объявление успешно удалено'})

@app.route('/api/listings/<int:listing_id>/view', methods=['POST'])
def api_view_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    listing.views += 1
    db.session.commit()
    
    return jsonify({'success': True, 'views': listing.views})

@app.route('/api/contact', methods=['POST'])
def api_contact_seller():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        listing_id = data.get('listing_id')
        message_text = data.get('message', '').strip()
        
        if not listing_id or not message_text:
            return jsonify({'error': 'Missing required fields'}), 400
        
        listing = Listing.query.get_or_404(listing_id)
        
        if listing.seller_id == session['user_id']:
            return jsonify({'error': 'Cannot contact yourself'}), 400
        
        # Создаем сообщение
        new_message = Message(
            sender_id=session['user_id'],
            recipient_id=listing.seller_id,
            listing_id=listing_id,
            message=message_text
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        print(f"💬 Сообщение от {session['first_name']} к {listing.seller.first_name} по объявлению #{listing_id}")
        
        return jsonify({
            'success': True,
            'message': 'Сообщение отправлено продавцу!',
            'message_id': new_message.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка отправки сообщения: {e}")
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/api/categories')
def api_categories():
    categories = Category.query.filter_by(is_active=True).all()
    return jsonify({
        'categories': [cat.to_dict() for cat in categories]
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Инициализируем БД при первом запуске
    init_db()
    
    print("🌐 Запуск OTC Marketplace с исправленной обработкой цен...")
    print(f"👤 Администратор: RomBerbeatz")
    print(f"📍 Локальный адрес: http://localhost:5000")
    print(f"💾 База данных: SQLAlchemy + SQLite")
    print(f"🔐 Автоматическая авторизация: Включена")
    
    with app.app_context():
        listings_count = Listing.query.count()
        users_count = User.query.count()
        print(f"📊 Объявлений в БД: {listings_count}")
        print(f"👥 Пользователей в БД: {users_count}")
        
        # Проверяем цены в БД
        test_listing = Listing.query.filter(Listing.title.like('%1.3%')).first()
        if test_listing:
            print(f"💰 Тестовая цена $1.3 в БД: {test_listing.price}")
    
    print("🚀 Сервер готов к работе!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)