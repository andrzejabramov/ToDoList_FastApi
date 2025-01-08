# Пояснение 
## к приложению To Do List на FastAPI в рамках дипломной работы студента 
## Абрамова Андрея Васильевича

Используемая литература:  
https://fastapi.qubitpi.org/tutorial/  

https://metanit.com/python/fastapi/


Итоговая структура приложения:
![project_tree](https://github.com/andrzejabramov/ToDoList_FastApi/blob/master/screens/project_tree.png)

FastAPI - один из трех фреймворков, на которых мы разработаем данное простое приложение для сравнения инструментов разработки Flask, FastAPI, Django.
Подготовим виртуальное приложение, в которое добавим помимо самого интерпретатора python12 - uvicorn, SQLAlchemy, Jinja2, alembic.  
Формируем дерево объектов проекта: файл main.py, пакет views с файлом для роутеров, данные функции обеспечивают добавление, изменение и удаление записей в БД и на веб странице.  
Кроме этого: создаем директорию templates для шаблонов HTML, директорию models для проектирования БД.  
Создаем файл config для хранения параметорв подключения к БД.  

Файл main.py содержит подключение к роутерам и типовую директиву запуска приложения:
```commandline
from fastapi import FastAPI
import uvicorn
from views.todo_items import router as todo_items_router

app = FastAPI()
app.include_router(todo_items_router)


if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```
В директории models в файле base.py объвляется класс Base от родителя DeclarativeBase из пакета sqlalchemy.orm 
В файле db.py объявляется переменная соединения с БД и функция - генератор сессий:
```commandline
engine = create_engine(config.SQLITE_DB_URI)

def get_session() -> Session:
    with Session(engine) as session:
        yield session
```
В файле todo_items.py - создается в виде класса TodoItem(Base) от родителя Base таблица todo_items:  
c тремя полями:   
id (ключевое, int),   
text (str) - текст записи задания,  
done (bool) - состояние задания (выполнено или нет), по умолчанию False
Магические методы добавлены для удобства отображения в консоли при отладке.  

Разбираем роутеры:
Так как у нас в роутерах на изменение и удаление проверяется id записи, есть смысл для оптимизации кода создать функцию проверки (зависимость):
```commandline
def todo_dependency(todo_id: int,
                    session: Session = Depends(get_session)
                    ) -> TodoItem:
    todo: TodoItem | None = session.get(TodoItem, todo_id)
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo {todo_id} not found"
        )
    return todo
```
если сессия вернула корректный id записи, то возвращается сама запись, если запись не найдена - ошибка.  

Задаем переменную router как экземпляр класса APIRouter.  
1. Первый роут возвращает список записей из БД в шаблон на веб страницу:
```commandline
@router.get("/", name="todo-list")
def list_todos(
        request: Request,
        session: Session = Depends(get_session)
):
    return templates.TemplateResponse(
        "index.html",
        context={
            "request": request,
            "todos": session.query(TodoItem).order_by(TodoItem.id).all(),
        },
    )
```
Get роут по корневому адресу, функция принимает на вход запрос, сессию, возвращает шаблон с контекстом запроса и списка заданий
2. Роутер для добавления записи:
```commandline
@router.post("/", name="add-todo")
def add_todo(
        request: Request,
        todo_text: str = Form(..., alias="todo-text"),
        session: Session = Depends(get_session),
):
    todo_item = TodoItem(text=todo_text)
    session.add(todo_item)
    session.commit()
    return RedirectResponse(
        url=request.url_for("todo-list"),
        status_code=status.HTTP_302_FOUND,
    )
```
Post роут по корневому адресу с имеием add-todo принимает на вход request, alias формы шаблона, сессию.
Записывает в БД введенное в форму шаборна значение, возвращает обновленную страницу с новой записью.
3. Роут для удаления записи. Сначала проверяется есть ли запись с таким id:
```commandline
@router.post("/{todo_id}/delete/", name="delete-todo")
def delete_todo(
        request: Request,
        session: Session = Depends(get_session),
        todo: TodoItem = Depends(todo_dependency),
):
    session.delete(todo)
    session.commit()
    return RedirectResponse(
        url=request.url_for("todo-list"),
        status_code=status.HTTP_302_FOUND,
    )
```
По адресу /id/delete, имя для шаблона delete-todo, принимает на вход request, сессию, проверяет есть ли запись, вызывая функцию todo_dependency(), производжит удаление из БД и с веб-страницы.  
4. Роут на изменение статуса задачи (выполнена/не выполнена) так же с проверкой наличия записи:  
```commandline
@router.post("/{todo_id}/toggle", name="toggle-todo")
def toggle_todo(
        request: Request,
        session: Session = Depends(get_session),
        todo: TodoItem = Depends(todo_dependency),
):
    todo.done = not todo.done
    session.commit()
    return RedirectResponse(
        url=request.url_for("todo-list"),
        status_code=status.HTTP_302_FOUND,
    )
```
По адресу id/toggle (имя для шаблона toggle-todo) post звпрос с входными параметрами request, сессия и проверка есть ли данная запись в БД.
Если да, то меняется булево значение на противоположное и возвращается на веб-страницу (начальная страница) измененный вид.

Описание файла веб-шаблона на Jinja2 (разбираем блок body):
Все помещено в один контейнер <div>, внутри которого:
1. блок для добавления нового задания с тегом <h3>: Add new todo:
```commandline
<h3>Add new todo</h3>
    <div>
        <form method="post" enctype="application/x-www-form-urlencoded">
        <label for="todo-text-id">New todo:</label>
        <input
                id="todo-text-id"
                name="todo-text"
                type="text"
                required="required"
        >
            <button type="submit">ADD</button>
        </form>
    </div>
```
2. Блок, с тегом <h3>: Todos, состоящий из списка <ul>, сформированный при помощи цикла по записям <li>:
- первая форма задает действие для кнопки ▶️и вызывает роутер toggle-todo, при этом на странице эмодзи ✅ и 🔘сменяют друг друга.
- вторая форма отвечает за удаление записи при нажатии на эмодзи ❌.

Приложение: 
![project.tree.png](https://github.com/andrzejabramov/ToDoList_FastApi/blob/master/screens/project_tree.png)

