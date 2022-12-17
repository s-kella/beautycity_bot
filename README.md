# beautycity
Чат-бот для записи в салоны красоты через Telegram.

## Как установить

Рекомендуемая версия питона: 3.10

1. Клонируйте репозиторий 
2. В терминале перейдите в корневую папку проекта
3. Скопируйте и запустите следующие команды:
    ```commandline
    python -m venv venv && venv/bin/pip install -U -r requirements.txt
    ```
4. Создайте .env файл с содержимым:
   
   ```
   TG_BOT_TOKEN=
   ```
   Создайте телеграм-бота с помощью BotFather и вставьте токен, который он вам пришлёт.
#### Paзработчикам и тестировщикам
5. Загрузите тестовые объекты в БД:
   ```commandline
   python manage.py migrate && python manage.py loaddata data/test_data.json
   ```
#### Всем
6. Разверните сервер для разработки или производственный веб-сервер согласно его документации.
Для производственного сервера понадобятся переменные в .env:
   ```
   DB_USER=
   DB_PASS=
   DB_PORT=
   DJANGO_SECRET_KEY=
   PROD=1
   ```

## Как пользоваться: салонам
1. Создайте аккаунт для админ-сайта Django 
[(документация)](https://docs.djangoproject.com/en/4.1/topics/auth/default/#managing-users-in-the-admin).
2. Информацию о салонах, мастерах и их расписаниях, а также доступных услугах можно занести в админке.
3. Отправьте клиентам ссылку на вашего бота.
4. Новые записи также будут появляться в админке.



## Разработчикам: точки доступа API

### Выбор салона, мастера, услуги: 

#### Доступные салоны
```
type: GET
path: /salons/

params for nearest salons:
   lat: float
   lon: float
   
optional params for filtering:
   provider_id: int | str
   service_id: int | str
```

#### Доступные мастера
```
type: GET
path: /providers/

optional params for filtering:
   salon_id: int | str
   service_id: int | str
```

#### Доступные услуги
```
type: GET
path: /services/

optional params for filtering:
   salon_id: int | str
   provider_id: int | str
```

#### Доступные записи в выбранном салоне
```
type: GET
path: /salon/<salon_id:int>/available_appointments/

optional params: 
   provider_id: int | str
   n_days: int    the default lookup window for appointments is 14 days ahead, 
                  customize it with this param
```

### Регистрация
```
type: POST
path: /register_customer/
post data:
   name: str
   telegram_id: int | str
   phone_numer: str
```

### Создание записи
```
type: POST
path: /make_appointment/
post data:
   hour: int | str
   date: str "YYYY:MM:DD"
   customer_id: int | str
   provider_id: int | str
   service_id: int | str
```
### Информация о клиенте
```
type: GET
path: /customer/
query params:
   telegram_id: int | str - find a registered customer by telegram id
```
### Прошлые и текущие записи клиента
```
/customer/<int:customer_id>/past/
/customer/<int:customer_id>/future/
```

### Пример запроса:
```python
# Getting available appointments for provider 1 at salon 1
salon_id = 1
url = urljoin(BASE_URL, f'/salon/{salon_id}/available_appointments/')
params = {
   'provider_id': 1
}
response = requests.get(url, params)
```

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).