# FastAPI LDAP/Active Directory Management

Полнофункциональное REST API для управления Active Directory через LDAP: пользователи, группы, организационные единицы (OU).

## Возможности

### 👥 Управление пользователями
- ✅ CRUD операции (создание, чтение, обновление, удаление)
- ✅ Сброс пароля через PATCH
- ✅ Обновление всех атрибутов (имя, фамилия, email, телефон, должность, отдел и т.д.)
- ✅ Перемещение между OU через PATCH
- ✅ Поиск по имени/username/email

### 👪 Управление группами
- ✅ CRUD операции для групп
- ✅ Добавление/удаление участников через PATCH
- ✅ Перемещение групп между OU через PATCH
- ✅ Поиск групп

### 🗂️ Управление подразделениями (OU)
- ✅ CRUD операции
- ✅ Перемещение OU через PATCH
- ✅ Обновление атрибутов

## Структура проекта

- [app/main.py](app/main.py): точка входа FastAPI, роутинг
- [app/api/v1/users.py](app/api/v1/users.py): API для управления пользователями
- [app/api/v1/groups.py](app/api/v1/groups.py): API для управления группами
- [app/api/v1/ous.py](app/api/v1/ous.py): API для управления OU
- [app/services/ldap_service.py](app/services/ldap_service.py): сервисный слой для LDAP операций
- [app/core/config.py](app/core/config.py): конфигурация (LDAP, app settings)
- [app/core/logging.py](app/core/logging.py): настройка логирования
- [app/models/](app/models/): Pydantic схемы (user, group, ou)
- [tests/](tests/): тесты

## Быстрый старт

### 1. Настройка окружения

Создать и активировать виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Установить зависимости:

```powershell
pip install -r requirements.txt
```

### 2. Конфигурация LDAP

Скопировать [.env.example](.env.example) в `.env` и настроить подключение к LDAP/AD:

```env
LDAP_SERVER=your-dc.example.com
LDAP_PORT=389
LDAP_USE_SSL=false
LDAP_BIND_DN=CN=ServiceAccount,CN=Users,DC=example,DC=com
LDAP_BIND_PASSWORD=your_secure_password
LDAP_BASE_DN=DC=example,DC=com
```

**Важно:** Для сброса паролей требуется SSL/TLS (порт 636) и учётная запись с соответствующими правами.

### 3. Запуск приложения

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Откройте Swagger UI: http://localhost:8000/docs

### 4. Запуск тестов

```powershell
pytest -v
```

## API Endpoints

### Пользователи (`/users`)
- `GET /users` - список всех пользователей с пагинацией (query params: `search`, `skip`, `limit`)
- `GET /users/{username}` - получить пользователя по username с групами в `memberOf`
- `POST /users` - создать нового пользователя
- `PATCH /users/{username}` - обновить атрибуты, сбросить пароль (поле `password`) или переместить (поле `parent_dn`)
- `DELETE /users/{username}` - удалить пользователя
- `POST /users/{username}/groups/{group_name}` - добавить пользователя в группу
- `DELETE /users/{username}/groups/{group_name}` - удалить пользователя из группы

### Группы (`/groups`)
- `GET /groups` - список всех групп с пагинацией (query params: `search`, `skip`, `limit`)
- `GET /groups/{group_name}` - получить группу по имени
- `POST /groups` - создать новую группу
- `PATCH /groups/{group_name}` - обновить группу или переместить (поле `parent_dn`)
- `DELETE /groups/{group_name}` - удалить группу
- `POST /groups/{group_name}/members/{username}` - добавить пользователя в группу
- `DELETE /groups/{group_name}/members/{username}` - удалить пользователя из группы

### Подразделения (`/ous`)
- `GET /ous` - список всех подразделений с пагинацией (query params: `search`, `skip`, `limit`)
- `GET /ous/{ou_name}` - получить подразделение (query param: `parent_dn`)
- `POST /ous` - создать новое подразделение
- `PATCH /ous/{ou_name}` - обновить подразделение или переместить его
- `DELETE /ous/{ou_name}` - удалить подразделение (должно быть пустым)

### Система
- `GET /health` - проверка здоровья сервиса

## Примеры использования

### Создать пользователя

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "cn": "Jane Smith",
    "sAMAccountName": "jsmith",
    "givenName": "Jane",
    "sn": "Smith",
    "mail": "jsmith@example.com",
    "password": "SecurePass123!",
    "ou": "OU=IT,DC=example,DC=com"
  }'
```

### Обновить пользователя и сбросить пароль (в одном запросе)

```bash
curl -X PATCH "http://localhost:8000/users/jsmith" \
  -H "Content-Type: application/json" \
  -d '{
    "mail": "jane.smith@example.com",
    "title": "Senior Developer",
    "password": "NewSecurePass456!"
  }'
```

### Переместить пользователя в другое подразделение

```bash
curl -X PATCH "http://localhost:8000/users/jsmith" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_dn": "OU=Developers,OU=IT,DC=example,DC=com"
  }'
```

### Добавить пользователя в группу (через роут пользователя)

```bash
curl -X POST "http://localhost:8000/users/jsmith/groups/DevTeam" \
  -H "Content-Type: application/json"
```

### Удалить пользователя из группы (через роут пользователя)

```bash
curl -X DELETE "http://localhost:8000/users/jsmith/groups/DevTeam"
```

### Получить информацию о пользователе с группами

```bash
curl "http://localhost:8000/users/jsmith"
```

Ответ включит поле `memberOf` со списком групп пользователя:
```json
{
  "dn": "CN=Jane Smith,OU=Users,DC=example,DC=com",
  "sAMAccountName": "jsmith",
  "cn": "Jane Smith",
  "mail": "jane.smith@example.com",
  "memberOf": [
    "CN=DevTeam,OU=Groups,DC=example,DC=com",
    "CN=IT Staff,OU=Groups,DC=example,DC=com"
  ]
}
```

### Создать группу

```bash
curl -X POST "http://localhost:8000/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "cn": "DevTeam",
    "description": "Development team group",
    "ou": "OU=IT,DC=example,DC=com"
  }'
```

### Добавить пользователя в группу (через роут группы)

```bash
curl -X POST "http://localhost:8000/groups/DevTeam/members/jsmith" \
  -H "Content-Type: application/json"
```

### Удалить пользователя из группы (через роут группы)

```bash
curl -X DELETE "http://localhost:8000/groups/DevTeam/members/jsmith"
```

### Переместить группу в другое подразделение

```bash
curl -X PATCH "http://localhost:8000/groups/DevTeam" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_dn": "OU=NewOU,DC=example,DC=com"
  }'
```

### Добавить и удалить участников группы через PATCH (старый способ, не рекомендуется)

```bash
curl -X PATCH "http://localhost:8000/groups/DevTeam" \
  -H "Content-Type: application/json" \
  -d '{
    "add_members": [
      "CN=Jane Smith,OU=Developers,OU=IT,DC=example,DC=com",
      "CN=John Doe,OU=IT,DC=example,DC=com"
    ],
    "remove_members": [
      "CN=Old User,OU=IT,DC=example,DC=com"
    ]
  }'
```

### Создать подразделение

```bash
curl -X POST "http://localhost:8000/ous" \
  -H "Content-Type: application/json" \
  -d '{
    "ou": "Developers",
    "description": "Development team",
    "parent_dn": "OU=IT,DC=example,DC=com"
  }'
```

### Переместить подразделение

```bash
curl -X PATCH "http://localhost:8000/ous/Developers" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_dn": "OU=Engineering,DC=example,DC=com"
  }'
```

### Получить список пользователей с пагинацией

```bash
# Первая страница (10 элементов по умолчанию)
curl -X GET "http://localhost:8000/users?skip=0&limit=10"

# Вторая страница (элементы 10-19)
curl -X GET "http://localhost:8000/users?skip=10&limit=10"

# С поиском и пагинацией
curl -X GET "http://localhost:8000/users?search=john&skip=0&limit=10"

# Пользовательский размер страницы (максимум 100)
curl -X GET "http://localhost:8000/users?skip=0&limit=50"
```

**Ответ с пагинацией:**

```json
{
  "items": [
    {
      "dn": "CN=John Doe,OU=Users,DC=example,DC=com",
      "sAMAccountName": "jdoe",
      "cn": "John Doe",
      "givenName": "John",
      "sn": "Doe",
      "mail": "jdoe@example.com",
      "title": "Software Engineer",
      "department": "IT",
      "telephoneNumber": "+1-555-0100",
      "description": "Senior Developer"
    }
  ],
  "total": 245,
  "skip": 0,
  "limit": 10,
  "pages": 25
}
```

**Параметры пагинации:**
- `skip` (по умолчанию `0`) - количество элементов, которые нужно пропустить
- `limit` (по умолчанию `10`, максимум `100`) - количество элементов на странице
- `total` - общее количество элементов в базе
- `pages` - общее количество страниц
- `items` - массив элементов текущей страницы

Аналогичная пагинация доступна для endpoints `/groups` и `/ous`.

## Технологии

- **FastAPI** - современный веб-фреймворк
- **ldap3** - Python LDAP клиент
- **Pydantic** - валидация данных
- **Uvicorn** - ASGI сервер
- **Pytest** - тестирование

## Безопасность

### SSL/TLS для паролей
Сброс паролей в Active Directory требует защищённого соединения:

```env
LDAP_USE_SSL=true
LDAP_PORT=636
```

### Аутентификация API
В production окружении добавьте:
- JWT/OAuth2 авторизацию
- Rate limiting
- CORS настройки
- HTTPS

## Переменные окружения

Скопируйте [.env.example](.env.example) в `.env` и настройте:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `APP_NAME` | Имя приложения | `fastapi-ldap-ad` |
| `ENVIRONMENT` | Окружение | `development` / `production` |
| `DEBUG` | Режим отладки | `true` / `false` |
| `LDAP_SERVER` | LDAP сервер | `dc.example.com` |
| `LDAP_PORT` | Порт LDAP | `389` (LDAP) / `636` (LDAPS) |
| `LDAP_USE_SSL` | Использовать SSL | `true` / `false` |
| `LDAP_BIND_DN` | DN служебной учётной записи | `CN=Service,DC=example,DC=com` |
| `LDAP_BIND_PASSWORD` | Пароль | `your_password` |
| `LDAP_BASE_DN` | Base DN для поиска | `DC=example,DC=com` |

## Лицензия

MIT

## Дальнейшее развитие

- [ ] JWT аутентификация для API
- [ ] Batch операции (массовое создание/изменение)
- [ ] Аудит логирование операций
- [ ] Docker контейнеризация
- [ ] CI/CD pipeline
- [ ] Расширенные фильтры поиска
- [ ] Управление компьютерами (computer objects)
- [ ] Export/Import пользователей (CSV, JSON)
- [ ] WebSocket для real-time уведомлений

