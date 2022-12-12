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

Описание API с тремя путями создания заказа.

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
#### Order path 1: by salon
1) 
   1) get nearest salons
   ```
   type: GET 
   path: /nearest  
   query params: lat:float, lon:float
   ```

   2) get all salons
   ```
   type: GET
   path: /salons
   ```
2) get services by salon
   ```
   type: GET
   path: /services
   query params: salon_id:int
   ```
3) get providers for salon
   ```
   type: GET
   path: /salon/<salon_id:int>/providers
   ```
4) get available appointments at this salon for this provider

   ```type: GET
   path: /salon/<salon_id:int>/available_appointments
   query params: provider_id:int
   optional params: n_days:int - the default lookup window for appointments is 14 days ahead, customize it with this param
   ```
   

#### Order path 2: by service
1) get all services
   ```
   type: GET
   path: /services
   ```
2) get salons for service
   ```
   type: GET
   path: /salons
   query params: service_id:int
   ```
3) get providers for salon
   ```
   type: GET
   path: /salon/<salon_id:int>/providers
   query params: service_id:int
   ```
5) get available appointments at this salon for this provider
   ```
   type: GET
   path: /salon/<salon_id:int>/available_appointments
   query params: provider_id:int
   optional params: n_days:int - the default lookup window for appointments is 14 days ahead, customize it with this param 
   ```
   
#### Order path 3: by provider
1) get all providers
   ```
   type: GET
   path: /providers
   ```
2) get services for this provider
   ```
   type: GET
   path: /services
   query params: provider_id:int
   ```
3) get salons
   ```
   type: GET
   path: /salons
   query params: provider_id:int
   ```
4) get appointments for salon
   ```
   type: GET
   path: /salon/<salon_id:int>/available_appointments
   query params: provider_id:int
   optional params: n_days:int - the default lookup window for appointments is 14 days ahead, customize it with this param 
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


## Как пользоваться

### Салонам

### Клиентам

## Цель проекта
