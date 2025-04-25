Документация описывает структуру и назначение таблиц проекта, реализованного с использованием SQLAlchemy.

---

## 1. Таблица `users`  
**Назначение:**  
Хранит общую информацию о пользователях Telegram, как фрилансерах, так и заказчиках.

**Поля:**  
• `id` (INTEGER PRIMARY KEY): уникальный идентификатор пользователя  
• `telegram_id` (BIGINT UNIQUE): Telegram ID пользователя  
• `username` (TEXT): username пользователя, если есть  
• `first_name` (TEXT): имя из Telegram, если есть  
• `last_name` (TEXT): фамилия из Telegram, если есть  
• `url` (TEXT): публичная ссылка на профиль  
• `role` (ENUM: 'freelancer', 'customer'): текущая роль пользователя  
• `created_at` (DATETIME): дата регистрации

---

## 2. Таблица `freelancer_profiles`  
**Назначение:**  
Дополнительные данные профиля фрилансера (1 к 1 к users), включая верификацию и статистику.

**Поля:**  
• `user_id` (INTEGER PRIMARY KEY): внешний ключ на `users.id`  
• `github_url` (TEXT): ссылка на GitHub профиль  
• `gitlab_url` (TEXT): ссылка на GitLab профиль  
• `personal_url` (TEXT): личная ссылка  
• `is_verified` (BOOLEAN DEFAULT FALSE): прошёл ли верификацию  
• `completed_orders` (INTEGER DEFAULT 0): количество завершённых заказов

---

## 3. Таблица `customer_profiles`  
**Назначение:**  
Дополнительные метаданные по заказчику (1 к 1 к users), включая показатели надёжности.

**Поля:**  
• `user_id` (INTEGER PRIMARY KEY): внешний ключ на `users.id`  
• `total_orders` (INTEGER DEFAULT 0): общее число размещённых заказов  
• `accepted_responses_ratio` (INTEGER): % принятых откликов от всех  

---

## 4. Таблица `orders`  
**Назначение:**  
Хранит данные о заказах, созданных заказчиками, включая статус, верификацию и исполнителя.

**Поля:**  
• `id` (INTEGER PRIMARY KEY): уникальный ID заказа  
• `description` (TEXT): подробное описание заказа  
• `created_by_user_id` (INTEGER): внешний ключ на `users.id` (создатель заказа)  
• `status` (ENUM): текущий статус (`draft`, `moderation`, `published`, `taken`, `completed`, `rejected`, `cancelled`)  
• `published_at` (DATETIME): дата публикации  
• `closed_at` (DATETIME): дата закрытия  
• `rejected_reason` (TEXT): причина отклонения, если заказ не прошёл модерацию  
• `taken_by_user_id` (INTEGER): внешний ключ на `users.id` — выбранный исполнитель  

---

## 5. Таблица `applications`  
**Назначение:**  
Регистрирует отклики фрилансеров на заказы, включая комментарии и выбор.

**Поля:**  
• `id` (INTEGER PRIMARY KEY): уникальный ID отклика  
• `order_id` (INTEGER): внешний ключ на `orders.id`  
• `user_id` (INTEGER): внешний ключ на `users.id` (фрилансер)  
• `message` (TEXT): сопроводительное сообщение фрилансера  
• `created_at` (DATETIME DEFAULT now()): время отклика  
• `is_chosen` (BOOLEAN DEFAULT FALSE): был ли фрилансер выбран исполнителем