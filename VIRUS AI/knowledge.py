import os
import sqlite3
from pypdf import PdfReader
KNOWLEDGE_BASE = {
    "what is science": (
        "Science is the systematic study of the natural world "
        "through observation and experiments."
    ),

    "what is computer": (
        "A computer is an electronic device that processes "
        "data and produces information."
    ),

    "what is internet": (
        "The internet is a worldwide network that connects "
        "computers and devices."
    ),

    "what is artificial intelligence": (
        "Artificial Intelligence (AI) is technology that "
        "allows computer systems to perform tasks that "
        "normally require human intelligence."
    ),

    "what is python": (
        "Python is a popular programming language used "
        "for software development, automation, data science and AI."
    ),

    "what is history": (
        "History is the study of past events, people and civilizations."
    ),

    "what is geography": (
        "Geography is the study of Earth, its environment, "
        "places and people."
    ),

    "what is solar system": (
        "The Solar System consists of the Sun and the objects "
        "that orbit it, including eight planets."
    ),

    "what is water": (
        "Water is a chemical compound with the formula H2O. "
        "It is essential for life."
    ),

    "what is electricity": (
        "Electricity is a form of energy associated with "
        "electric charges."
    ),
        "what is biology": "Biology is the scientific study of living organisms.",
    "what is physics": "Physics studies matter, energy, motion and forces.",
    "what is chemistry": "Chemistry studies substances, their properties and reactions.",
    "what is mathematics": "Mathematics is the study of numbers, quantities, patterns and shapes.",
    "what is astronomy": "Astronomy is the scientific study of stars, planets, galaxies and the universe.",
    "what is environment": "The environment includes all living and non-living things surrounding us.",
    "what is climate change": "Climate change refers to long-term changes in Earth's temperatures and weather patterns.",
    "what is artificial neural network": "An artificial neural network is a computing system inspired by how biological brains process information.",
    "what is machine learning": "Machine learning is a branch of AI that enables computers to learn patterns from data.",
    "what is deep learning": "Deep learning is a type of machine learning that uses multiple layers of artificial neural networks.",
    "what is cybersecurity": "Cybersecurity is the practice of protecting computers, networks, applications and data from digital threats.",
    "what is ethical hacking": "Ethical hacking involves authorized security testing to identify and help fix vulnerabilities.",
    "what is operating system": "An operating system manages computer hardware, software and system resources.",
    "what is linux": "Linux is an open-source operating system kernel used in many distributions, servers and devices.",
    "what is database": "A database is an organized collection of information that can be stored, managed and retrieved.",
    "what is networking": "Computer networking connects devices so they can communicate and share information.",
    "what is cloud computing": "Cloud computing provides computing services such as storage and servers over the internet.",
    "what is internet of things": "The Internet of Things connects physical devices that collect and exchange data.",
    "what is algorithm": "An algorithm is a sequence of steps designed to solve a problem or complete a task.",
    "what is data science": "Data science uses statistics, programming and scientific methods to understand data.",
    "what is blockchain": "Blockchain is a distributed digital ledger that records information in linked blocks.",
    "what is robotics": "Robotics is the field of designing, building and programming robots.",
    "what is democracy": "Democracy is a system of government in which people participate in choosing their leaders.",
    "what is geography": "Geography studies Earth's places, environments, people and physical features.",
    "what is economics": "Economics studies how people and societies use limited resources.",
    "what is psychology": "Psychology is the scientific study of the mind and human behaviour.",
    "what is philosophy": "Philosophy explores fundamental questions about knowledge, existence, reason and values.",
    "what is communication": "Communication is the process of sharing information, ideas and feelings.",
    "what is electricity": "Electricity is associated with electric charges and their movement or interaction.",
    "what is renewable energy": "Renewable energy comes from naturally replenished sources such as sunlight, wind and flowing water."
}


def search_knowledge(question):
    question = question.lower().strip()

    for keyword, answer in KNOWLEDGE_BASE.items():
        if keyword in question:
            return answer

    return None
# ==============================
# OFFLINE HELPER KNOWLEDGE DATABASE
# ==============================

DB_NAME = "knowledge.db"


def create_knowledge_database():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learned_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_knowledge(title, content, source):
    if not content or not content.strip():
        return False

    title = title.strip()
    content = content.strip()
    source = source.strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check whether this information already exists
    cursor.execute("""
        SELECT id FROM learned_knowledge
        WHERE title = ? AND content = ? AND source = ?
        LIMIT 1
    """, (title, content, source))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        print("Knowledge already exists. Skipping duplicate.")
        return False

    cursor.execute("""
        INSERT INTO learned_knowledge (title, content, source)
        VALUES (?, ?, ?)
    """, (title, content, source))

    conn.commit()
    conn.close()

    print("Knowledge saved successfully:", title)
    return True


def read_document(file_path):
    if not os.path.exists(file_path):
        return None

    extension = os.path.splitext(file_path)[1].lower()

    try:
        if extension == ".txt":
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()

        elif extension == ".pdf":
            reader = PdfReader(file_path)

            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")

            return "\n".join(pages)

        else:
            return None

    except Exception as error:
        print("Document reading error:", error)
        return None
def learn_from_document(file_path):
    content = read_document(file_path)

    if not content:
        return False

    title = os.path.basename(file_path)

    return save_knowledge(
        title=title,
        content=content,
        source=file_path
    )


def search_learned_knowledge(question):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, content, source
        FROM learned_knowledge
        WHERE title LIKE ? OR content LIKE ?
        LIMIT 5
    """, (
        f"%{question}%",
        f"%{question}%"
    ))

    results = cursor.fetchall()
    conn.close()

    return results
# Initialize knowledge database
create_knowledge_database()