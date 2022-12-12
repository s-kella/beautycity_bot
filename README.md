# beautycity

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
TG_BOT_TOKEN=''
```
Создайте телеграм-бота с помощью BotFather и вставьте токен, который он вам пришлёт
.
#### Paзработчикам
5. Загрузите тестовые объекты в БД:
   ```commandline
   python manage.py migrate && python manage.py loaddata data/test_data.json
   ```
6. Запустите development server
   ```commandline
   python manage.py runserver
   ```


## API endpoints

Пример запроса для development server:
```python
# Getting available appointments for provider 1 at salon 1
salon_id = 1
url = f'http://127.0.0.1:8000/salon/{salon_id}/available_appointments'
params = {
   'provider_id': 1
}
response = requests.get(url, params)
```

### Choosing salon and datetime for appointment: 

#### Show salons
```
type: GET
path: /salons

params for nearest salons:
   lat: float
   lon: float
   
optional params for filtering:
   provider_id: int
   service_id: int
```

#### Show providers
```
type: GET
path: /providers

optional params for filtering:
   salon_id: int
   service_id: int
```

#### Show services
```
type: GET
path: /services

optional params for filtering:
   salon_id: int
   provider_id: int
```

#### Show available appointments at a salon
```
type: GET
path: /salon/<salon_id:int>/available_appointments

optional params: 
   provider_id: int
   n_days: int    the default lookup window for appointments is 14 days ahead, 
                  customize it with this param
```


### Registering a customer
```
type: POST
path: /register_customer
post data:
   name: str
   telegram_id: int|str
   phone_numer: str
```

### Making an appointment
```
type: POST
path: /make_appointment
post data:
   hour: int
   date: str YYYY:MM:DD
   customer_id: int
   provider_id: int
   service_id: int
```

### Past and future appointments for customer
```
/customer/<int:customer_id>/past
/customer/<int:customer_id>/future
```


## Как пользоваться

### Салонам

### Клиентам

## Цель проекта
