
import sqlite3
from datetime import datetime

DB_NAME = "virus_memory.db"


def create_history_table():
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            assistant_reply TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

def create_study_history_table():
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS study_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            lesson TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()


def save_study_lesson(topic, lesson):
    connection = sqlite3.connect(DB_NAME)

    connection.execute(
        """
        INSERT INTO study_history
        (topic, lesson, created_at)
        VALUES (?, ?, ?)
        """,
        (
            topic,
            lesson,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    connection.commit()
    connection.close()

    return "Study lesson saved successfully!"


def get_study_history():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        """
        SELECT id, topic, lesson, created_at
        FROM study_history
        ORDER BY id DESC
        """
    )

    study_history = cursor.fetchall()
    connection.close()

    return study_history


def save_chat(user_message, assistant_reply):
    connection = sqlite3.connect(DB_NAME)

    connection.execute(
        """
        INSERT INTO chat_history
        (user_message, assistant_reply, created_at)
        VALUES (?, ?, ?)
        """,
        (
            user_message,
            assistant_reply,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    connection.commit()
    connection.close()

    return "Conversation saved successfully!"


def get_chat_history():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        """
        SELECT id, user_message, assistant_reply, created_at
        FROM chat_history
        ORDER BY id
        """
    )

    history = cursor.fetchall()
    connection.close()

    return history


if __name__ == "__main__":
    create_history_table()
    print("Offline Helper conversation history is ready!")
