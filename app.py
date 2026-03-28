# Записали ячейку в app.py для запуска из консоли
import pandas as pd
import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Request, Response
from scalar_doc import ScalarConfiguration, ScalarDoc
import xml.etree.ElementTree as ET
import nest_asyncio
import re
nest_asyncio.apply()

# Инициализируем начальные данные для добавления в файл `app.py`
df = pd.DataFrame([
    ['Антифриз EURO G11 (-45°С) зеленый, силикатный 5кг', 1025, 329, 11, 'c', 'антифриз', datetime.datetime(2026, 10, 16, 12, 36, 22)],
    ['Антифриз готовый фиолетовый Синтек MULTIFREEZE 5кг', 250, 315, 38, 'b', 'антифриз', datetime.datetime(2025, 12, 11, 8, 25, 31)],
    ['Антифриз G11 зеленый', 120, 329, 61, 'b', 'антифриз', datetime.datetime(2025, 6, 15, 15, 36, 30)],
    ['Антифриз Antifreeze OEM China OAT red -40 5кг', 390, 504, 65, 'c', 'антифриз', datetime.datetime(2025, 11, 30, 4, 12, 39)],
    ['Антифриз G11 зеленый', 135, 407, 93, 'b', 'антифриз', datetime.datetime(2026, 8, 25, 3, 24, 1)],
])

df.columns = ['Наименование товара', 'Цена, руб.', 'cpm', 'Скидка', 'tp', 'Категория', 'dt']
df['Год'] = df['dt'].dt.year
df=df.drop(['cpm',  'tp', 'dt'],axis=1)

# Преобразовываю pd.DataFrame в словарь id: items
items_db = {str(k): v for k, v in df.to_dict(orient="index").items()}

# Преобразовываю словарь в словарь id: {id + **items}
for id, item in items_db.items():
    items_db[id] = dict(id = id, **item)

# Инициализирую следующий id товара
next_id = len(items_db)

# Для добавления нового элемента в базу по соответствующему ключу
class ItemCreate(BaseModel):
    НаименованиеТовара: str = Field(..., alias="Наименование товара")
    ЦенаРуб: float = Field(..., alias="Цена, руб.")
    Скидка: int
    Категория: str
    Год: int

    # Для добавления нового элемента в базу как по имени, так и по алиасу
    class Config:
        populate_by_name = True

# Для вывода из базы элемента как по алиасу, так и по имени элемента
class ItemResponse(BaseModel):
    НаименованиеТовара: str = Field(..., alias="Наименование товара")
    ЦенаРуб: float = Field(..., alias="Цена, руб.")
    Скидка: int
    Категория: str
    Год: int

    class Config:
        populate_by_name = True

# Вспомогательные функции для XML
def clean_xml_key(key: str) -> str:
    # Для преобразования ключей словаря в безопасные, чтоб ничего не крашнулось
    return re.sub(r'[^a-zA-Z0-9а-яА-Я_-]', '_', key)

def dict_to_xml(item: dict, root_tag: str = "item") -> str:
    # Преобразует `items_db` словарь в XML вид
    root = ET.Element(root_tag)
    for key, value in item.items():
        safe_key = clean_xml_key(key)
        elem = ET.SubElement(root, safe_key)
        elem.text = str(value)
    return ET.tostring(root, encoding='unicode')

def items_to_xml(items: list[dict]) -> str:
    # Преобразует элемент/позицию в словаре `items_db` в XML вид
    root = ET.Element("items")
    for item in items:
        root.append(ET.fromstring(dict_to_xml(item, "item")))
    return ET.tostring(root, encoding='unicode', xml_declaration=True)

# Описание FastAPI приложения
DESCRIPTION = """
# API управления товарами (постами)

Данный сервис предоставляет REST API для управления товарами (или постами).  
Поддерживаются форматы **JSON** и **XML** в зависимости от заголовка `Accept`.

## Основные возможности

- **Получение списка всех товаров**  
  `GET /items`  
  Возвращает массив товаров.  
  *Пример:* `Accept: application/json` → JSON, `Accept: application/xml` → XML.

- **Получение одного товара по ID**  
  `GET /items/{id}`  
  Возвращает товар с указанным строковым идентификатором.

- **Создание нового товара**  
  `POST /items`  
  Принимает JSON с полями:
  - `Наименование товара` (строка)
  - `Цена, руб.` (число)
  - `Скидка` (целое)
  - `Категория` (строка)
  - `Год` (целое)

  Возвращает созданный объект (без поля `id`).

## Форматы ответов

- **JSON** — возвращается по умолчанию или при `Accept: application/json`.
- **XML** — возвращается при `Accept: application/xml`.  
  В XML все недопустимые символы в именах тегов заменяются на подчёркивания для корректного отображения.

## Документация

- `/docs` — интерактивная документация (Scalar).
- `/docs2` — альтернативная документация (Scalar).

## Примеры

**Создание товара:**
```json
POST /items
{
  "Наименование товара": "Антифриз G12 красный",
  "Цена, руб.": 750,
  "Скидка": 15,
  "Категория": "антифриз",
  "Год": 2026
  "id": 2
}
```

**Получение в XML:**
``` Bash
curl -H "Accept: application/xml" http://localhost:8000/items
```

"""

app = FastAPI(title="Test", description=DESCRIPTION, docs_url=None, redoc_url=None)
docs = ScalarDoc.from_spec(spec=app.openapi_url, mode="url")

@app.post("/foo")
def post_foo(a: str):
    return a + " - ok"

@app.get("/items")
def get_items(request: Request):
    accept = request.headers.get("Accept", "")
    items_list = list(items_db.values())
    if "application/xml" in accept:
        # Проверяем хэдэр и преобазуем в XML если есть такой параметр
        return Response(content=items_to_xml(items_list), media_type="application/xml")
    return items_list

@app.get("/items/{item_id}")
def get_item(item_id: str, request: Request):
    item = items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    accept = request.headers.get("Accept", "")
    # Проверяем хэдэр и преобазуем в XML если есть такой параметр
    if "application/xml" in accept:
        return Response(content=dict_to_xml(item, "item"), media_type="application/xml")
    return item

@app.post("/items", status_code=201)
def post_item(item: ItemCreate, request: Request):
    global next_id
    # Определим next_id как максимальный существующий ключ + 1,
    # поскольку порядок ключей может быть произвольным, а не только лишь по длине базы
    new_id = str(next_id)
    data = dict(id = new_id, **item.dict(by_alias=True))
    items_db[new_id] = data
    next_id += 1
    return data

@app.get("/docs", include_in_schema=False)
def get_docs():
    # Эндпоинт документации 
    docs_html = docs.to_html()
    return Response(content=docs_html, media_type="text/html")

@app.get("/docs2", include_in_schema=False)
def get_docs2():
    # Эндпоинт документации 2
    docs = ScalarDoc.from_spec("http://localhost/openapi.json", mode="url")
    docs.set_title("Автодокументация")
    docs.set_configuration(ScalarConfiguration())
    docs_html = docs.to_html()
    return Response(docs_html, media_type="text/html")
