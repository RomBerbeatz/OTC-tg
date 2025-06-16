// Telegram WebApp инициализация
let tg = window.Telegram.WebApp;
tg.expand();

// Глобальные переменные
let currentListing = null;
let currentUser = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Получаем данные пользователя из Telegram
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        currentUser = tg.initDataUnsafe.user;
        console.log('Пользователь Telegram:', currentUser);
    }
    
    // Настраиваем поиск
    setupSearch();
    
    // Настраиваем фильтры
    setupFilters();
});

// Настройка поиска
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 500);
    });
    
    categoryFilter.addEventListener('change', performSearch);
}

// Выполнение поиска
function performSearch() {
    const search = document.getElementById('searchInput').value;
    const category = document.getElementById('categoryFilter').value;
    
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    
    fetch(`/api/listings?${params}`)
        .then(response => response.json())
        .then(data => {
            displayListings(data.listings);
        })
        .catch(error => {
            console.error('Ошибка поиска:', error);
            showNotification('Ошибка при поиске объявлений', 'error');
        });
}

// Отображение объявлений
function displayListings(listings) {
    // Очищаем текущие объявления
    document.querySelectorAll('.category-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Группируем по категориям
    const groupedListings = {};
    listings.forEach(listing => {
        if (!groupedListings[listing.category]) {
            groupedListings[listing.category] = [];
        }
        groupedListings[listing.category].push(listing);
    });
    
    // Отображаем результаты
    Object.keys(groupedListings).forEach(category => {
        displayCategoryListings(category, groupedListings[category]);
    });
}

// Просмотр объявления
function viewListing(listingId) {
    fetch(`/api/listings/${listingId}`)
        .then(response => response.json())
        .then(listing => {
            currentListing = listing;
            displayListingModal(listing);
        })
        .catch(error => {
            console.error('Ошибка загрузки объявления:', error);
            showNotification('Ошибка при загрузке объявления', 'error');
        });
}

// Отображение модального окна с объявлением
function displayListingModal(listing) {
    const modal = document.getElementById('listingModal');
    const title = document.getElementById('listingTitle');
    const content = document.getElementById('listingContent');
    
    title.textContent = listing.title;
    
    content.innerHTML = `
        <div class="seller-info">
            <h6>👤 Продавец</h6>
            <div class="d-flex justify-content-between">
                <span>${listing.seller.first_name} ${listing.seller.username ? '@' + listing.seller.username : ''}</span>
                <span class="rating">⭐ ${listing.seller.rating.toFixed(1)}</span>
            </div>
        </div>
        
        <div class="mb-3">
            <h6>📝 Описание</h6>
            <p>${listing.description}</p>
        </div>
        
        <div class="mb-3">
            <h6>💰 Цена</h6>
            <span class="price">${listing.price} ${listing.currency}</span>
        </div>
        
        ${listing.additional_info ? `
        <div class="mb-3">
            <h6>ℹ️ Дополнительная информация</h6>
            <p>${listing.additional_info}</p>
        </div>
        ` : ''}
        
        <div class="mb-3">
            <h6>📅 Дата создания</h6>
            <small class="text-muted">${new Date(listing.created_at).toLocaleDateString('ru-RU')}</small>
        </div>
    `;
    
    // Показываем модальное окно
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

// Связаться с продавцом
function contactSeller() {
    if (!currentListing || !currentUser) {
        showNotification('Ошибка: недостаточно данных', 'error');
        return;
    }
    
    // Создаем форму для сообщения
    const content = document.getElementById('listingContent');
    const contactForm = document.createElement('div');
    contactForm.className = 'contact-form';
    contactForm.innerHTML = `
        <h6>💬 Написать продавцу</h6>
        <div class="mb-3">
            <textarea class="form-control" id="messageText" rows="3" 
                placeholder="Введите ваше сообщение..."></textarea>
        </div>
        <button class="btn btn-primary" onclick="sendMessage()">Отправить</button>
        <button class="btn btn-secondary ms-2" onclick="cancelMessage()">Отмена</button>
    `;
    
    content.appendChild(contactForm);
    
    // Скрываем кнопку "Связаться с продавцом"
    document.querySelector('.modal-footer .btn-primary').style.display = 'none';
}

// Отправка сообщения
function sendMessage() {
    const messageText = document.getElementById('messageText').value.trim();
    
    if (!messageText) {
        showNotification('Введите сообщение', 'warning');
        return;
    }
    
    const data = {
        listing_id: currentListing.id,
        message: messageText,
        user_id: currentUser.id
    };
    
    fetch('/api/contact_seller', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showNotification('Сообщение отправлено!', 'success');
            
            // Уведомляем Telegram о действии
            tg.showAlert('Сообщение отправлено продавцу!');
            
            // Закрываем модальное окно
            bootstrap.Modal.getInstance(document.getElementById('listingModal')).hide();
        } else {
            showNotification('Ошибка при отправке сообщения', 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при отправке сообщения', 'error');
    });
}

// Отмена отправки сообщения
function cancelMessage() {
    document.querySelector('.contact-form').remove();
    document.querySelector('.modal-footer .btn-primary').style.display = 'block';
}

// Показ уведомлений
function showNotification(message, type = 'info') {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Настройка фильтров
function setupFilters() {
    // Добавляем обработчики для карточек объявлений
    document.querySelectorAll('.listing-card').forEach(card => {
        card.addEventListener('click', function() {
            const listingId = this.dataset.listingId;
            viewListing(listingId);
        });
    });
}