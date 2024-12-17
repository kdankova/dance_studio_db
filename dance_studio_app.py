import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )


# Функция для выполнения SQL-запросов
def run_query(query, params=None, fetch=True):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            if fetch and query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            conn.commit()

# Получение справочников
def get_reference_data():
    return {
        "Instructors": "SELECT id, fullName, experienceYears, hourlyRate, TO_CHAR(birthDate, 'DD.MM.YYYY') as birthDate FROM Instructor",
        "Classes": "SELECT id, name, style, instructorId, durationMinutes, price FROM Class"
    }

# Основной интерфейс
st.title("Dance Studio Management")
st.sidebar.title("Выбор справочника")

# Выбор справочника
reference_data = get_reference_data()
selected_ref = st.sidebar.selectbox("Выберите справочник", list(reference_data.keys()))

st.sidebar.write("# Данькова Екатерина Григорьевна \n 3 курс 11 группа")

# Получение данных
query = reference_data[selected_ref]
data = pd.DataFrame(run_query(query))

# Отображение данных справочника
if not data.empty:
    st.write("### Данные справочника:")
    if "id" in data.columns:
        data_display = data.drop(columns=["id"])  # Скрываем ID для пользователя
    else:
        data_display = data
    st.dataframe(data_display)

# Управление данными
st.write("### Управление данными")

if selected_ref == "Instructors":
    # Поля для добавления и редактирования
    full_name = st.text_input("Полное имя", "")
    experience = st.number_input("Опыт работы (лет)", min_value=0, step=1)
    rate = st.number_input("Почасовая ставка", min_value=0.0, step=0.5)
    birth_date = st.date_input("Дата рождения", max_value=datetime.now())

    # Добавление записи
    if st.button("Добавить инструктора"):
        run_query(
            "INSERT INTO Instructor (fullName, experienceYears, hourlyRate, birthDate) VALUES (%s, %s, %s, %s)",
            (full_name, experience, rate, birth_date),
            fetch=False
        )
        st.success("Инструктор добавлен!")

elif selected_ref == "Classes":
    name = st.text_input("Название занятия", "")
    style = st.text_input("Стиль", "")

    # Получаем список инструкторов и проверяем структуру
    instructors = run_query("SELECT id, fullName FROM Instructor")

    if instructors:
        first_row = instructors[0]
        key_name = 'fullName' if 'fullName' in first_row else list(first_row.keys())[1]  # Берем вторую колонку

        # Создаем словарь для отображения
        instructor_map = {f"{row[key_name]} ({row['id']})": row['id'] for row in instructors}
        instructor = st.selectbox("Инструктор", list(instructor_map.keys()))
    else:
        st.error("Ошибка: Таблица инструкторов пуста или некорректна.")
        st.stop()

    duration = st.number_input("Длительность (минуты)", min_value=1, step=1)
    price = st.number_input("Цена занятия", min_value=0.0, step=0.5)

    if st.button("Добавить занятие"):
        run_query(
            "INSERT INTO Class (name, style, instructorId, durationMinutes, price) VALUES (%s, %s, %s, %s, %s)",
            (name, style, instructor_map[instructor], duration, price),
            fetch=False
        )
        st.success("Занятие добавлено!")


# Редактирование и удаление записей
st.write("### Удаление записей")

if not data.empty:

    # Автоматический выбор первой текстовой колонки для отображения
    text_columns = data.select_dtypes(include=['object']).columns  # Все текстовые колонки
    if len(text_columns) > 0:
        display_column = text_columns[0]  # Берем первую текстовую колонку
    else:
        st.error("Ошибка: В данных нет текстовых колонок для отображения.")
        st.stop()

    # Создаем словарь: отображаемый текст -> ID
    options = {f"{row[display_column]}": row['id'] for _, row in data.iterrows()}

    # Выпадающий список для выбора записи
    selected_option = st.selectbox("Выберите запись для удаления", list(options.keys()))
    record_id = options[selected_option]

    # Удаление записи
    if st.button("Удалить запись"):
        table = "Instructor" if selected_ref == "Instructors" else "Class"
        run_query(f"DELETE FROM {table} WHERE id = %s", (record_id,), fetch=False)
        st.success("Запись удалена!")
else:
    st.warning("В справочнике нет данных.")

