
import sqlite3

DB_NAME = "virus_memory.db"


def create_database():
    connection = sqlite3.connect(DB_NAME)

    connection.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        information TEXT NOT NULL,
        category TEXT DEFAULT 'general'
    )
""")

    columns = [
        row[1] for row in connection.execute(
            "PRAGMA table_info(memories)"
        )
    ]

    if "category" not in columns:
        connection.execute(
            "ALTER TABLE memories ADD COLUMN category TEXT DEFAULT 'general'"
        )

    connection.commit()
    connection.close()

def save_memory(information, category="general"):
    information = information.strip()
    category = category.strip().lower()

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        "SELECT id FROM memories WHERE LOWER(TRIM(information)) = LOWER(?)",
        (information,)
    )

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return "This memory already exists!"

    connection.execute(
        "INSERT INTO memories (information, category) VALUES (?, ?)",
        (information, category)
    )

    connection.commit()
    connection.close()

    return "Memory saved successfully!"


def get_memories():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        "SELECT id, information FROM memories ORDER BY id"
    )

    memories = cursor.fetchall()
    connection.close()

    return memories


def get_memories_with_categories():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        "SELECT id, information, category FROM memories ORDER BY id"
    )

    memories = cursor.fetchall()
    connection.close()

    return memories


def get_memories_by_category(category):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        "SELECT id, information, category FROM memories WHERE LOWER(category) = LOWER(?) ORDER BY id",
        (category,)
    )

    memories = cursor.fetchall()
    connection.close()

    return memories
def update_memory(memory_id, information, category="general"):
    information = information.strip()
    category = category.strip().lower()

    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        """
        UPDATE memories
        SET information = ?, category = ?
        WHERE id = ?
        """,
        (information, category, memory_id)
    )

    connection.commit()
    updated = cursor.rowcount
    connection.close()

    return updated > 0


def get_memory_stats():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute("""
        SELECT category, COUNT(*)
        FROM memories
        GROUP BY category
        ORDER BY category
    """)

    stats = cursor.fetchall()
    connection.close()

    return stats


def delete_memory(memory_id):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.execute(
        "DELETE FROM memories WHERE id = ?",
        (memory_id,)
    )

    connection.commit()
    deleted = cursor.rowcount
    connection.close()

    return deleted > 0


if __name__ == "__main__":
    create_database()
    print("Offline Helper memory database is ready!")
