from dotenv import load_dotenv
from openai import OpenAI
from unicodedata import category

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Literal
import memory
import history
import knowledge
import ollama
from online_search import search_web, internet_available
import os
import json
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = (
    OpenAI(api_key=OPENAI_API_KEY)
    if OPENAI_API_KEY
    else None
)
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").lower() == "true"
app = FastAPI(
    title="Offline Helper",
    version="0.3.0"
)

memory.create_database()
history.create_history_table()
history.create_study_history_table()
def detect_memory_category(information):
    text = information.lower()

    if any(word in text for word in [
        "goal", "dream", "plan", "future", "target"
    ]):
        return "goals"

    if any(word in text for word in [
        "project", "building", "developing", "creating", "app"
    ]):
        return "projects"

    if any(word in text for word in [
        "learn", "learning", "learned",
        "study", "studying", "studies",
        "course", "education", "practice"
    ]):
        return "learning"

    if any(word in text for word in [
        "prefer", "preference", "i like", "i love", "i want"
    ]):
        return "preferences"

    return "general"
def detect_response_language(message):
    text = message.lower().strip()

    # Punjabi Gurmukhi
    if any("\u0A00" <= char <= "\u0A7F" for char in text):
        return "Punjabi (Gurmukhi)"

    # Hindi Devanagari
    if any("\u0900" <= char <= "\u097F" for char in text):
        return "Hindi (Devanagari)"

    # Clean words
    words = {
        word.strip(".,!?;:()[]{}\"'")
        for word in text.split()
    }

    # Roman Punjabi
    punjabi_words = {
        "tusi", "tuhada", "tuhadi", "tuhade",
        "tuhanu", "thonu", "mainu", "sanu",
        "kiven", "kive", "kidda", "kidan",
        "kithhe", "kithe", "dasso", "das",
        "changa", "vadia", "vadiya", "haanji",
        "aa", "assi", "tussi", "karna",
        "reha", "rahi", "rahe", "pyaar",
        "sada", "sadi", "mere"
    }

    # Roman Hindi
    hindi_words = {
        "aap", "aapka", "aapki", "aapko",
        "mujhe", "mujhko", "hum", "hain",
        "hai", "kaise", "kaisa", "kaisi",
        "kya", "kyun", "kyon", "kab",
        "kahan", "mera", "meri", "mere",
        "chahiye", "kripya", "namaste",
        "dhanyavaad", "bataiye", "bataye",
        "batao", "raha", "rahi", "rahe",
        "accha", "achha", "bahut"
    }

    punjabi_score = sum(word in punjabi_words for word in words)
    hindi_score = sum(word in hindi_words for word in words)

    # Common Punjabi phrases
    if any(phrase in text for phrase in [
        "sat sri akal", "ki haal aa",
        "tusi kive ho", "mainu dasso"
    ]):
        punjabi_score += 3

    # Common Hindi phrases
    if any(phrase in text for phrase in [
        "aap kaise hain", "mujhe batao",
        "kya haal hai", "kaise ho"
    ]):
        hindi_score += 3

    if punjabi_score > hindi_score and punjabi_score > 0:
        return "Punjabi (Gurmukhi)"

    if hindi_score > punjabi_score and hindi_score > 0:
        return "Hindi (Devanagari)"

    return "English"


class ChatRequest(BaseModel):
    message: str
    personality: str = "friendly"
    mode: Literal["auto", "online", "offline"] = "auto"
class StudyRequest(BaseModel):
    topic: str
    previous_lesson: str = ""
    difficulty: str = "intermediate"
class QuizRequest(BaseModel):
    topic: str
@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.get("/manifest.json")
def get_manifest():
    return FileResponse("frontend/manifest.json")


@app.get("/service-worker.js")
def get_service_worker():
    return FileResponse(
        "frontend/service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"}
    )
@app.get("/status")
def connection_status():
    online = internet_available()

    return {
        "online": online,
        "status": "ONLINE" if online else "OFFLINE"
    }


def select_ai_mode(requested_mode):
    online = internet_available()

    if requested_mode == "offline":
        return "offline"

    if requested_mode == "online":
        if not online:
            return "unavailable"
        return "online"

    # Automatic mode
    if online:
        return "online"

    return "offline"
@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    lower_message = message.lower()
    topic = message.rstrip("?.!।")
    selected_mode = select_ai_mode(request.mode)

    if selected_mode == "unavailable":
        return {
            "assistant": "Offline Helper",
            "mode": "online",
            "reply": (
                "Online AI is currently unavailable. "
                "Please check your internet connection and API key, "
                "or switch to Auto or Offline mode."
            )
        }

    print("Selected AI mode:", selected_mode)

    if not message:
        return {"reply": "Please enter a message."}
    suggestions = []

    if lower_message.startswith("remember:"):
        information = message[len("remember:"):].strip()

        if not information:
            return {"reply": "What should I remember?"}

        category = detect_memory_category(information)
        memory.save_memory(information, category)

        return {
            "assistant": "Offline Helper",
            "reply": "I have saved that information!"
        }

    if lower_message == "what do you remember?":
        saved_memories = memory.get_memories()

        return {
            "assistant": "Offline Helper",
            "reply": "Here is what I remember:",
            "memories": [
                {"id": memory_id, "information": information}
                for memory_id, information in saved_memories
            ]
        }
    if any(phrase in lower_message for phrase in [
        "what am i learning",
        "what are my studies",
        "tell me about my learning",
        "what courses am i studying"
    ]):
        learning_memories = memory.get_memories_by_category("learning")

        return {
            "assistant": "Offline Helper",
            "reply": "Here is what I remember about your learning:",
            "memories": [
                {
                    "id": memory_id,
                    "information": information
                }
                for memory_id, information, category in learning_memories
            ]
        }

    if any(phrase in lower_message for phrase in [
        "what are my goals",
        "what are my future plans",
        "what do i want to achieve",
        "tell me about my goals"
    ]):
        goal_memories = memory.get_memories_by_category("goals")

        return {
            "assistant": "Offline Helper",
            "reply": "Here is what I remember about your goals:",
            "memories": [
                {
                    "id": memory_id,
                    "information": information
                }
                for memory_id, information, category in goal_memories
            ]
        }
    if any(phrase in lower_message for phrase in [
        "what do you remember about my projects",
        "what are my projects",
        "tell me about my projects"
    ]):
        project_memories = memory.get_memories_by_category("projects")

        return {
            "assistant": "Offline Helper",
            "reply": "Here is what I remember about your projects:",
            "memories": [
                {
                    "id": memory_id,
                    "information": information
                }
                for memory_id, information, category in project_memories
            ]
        }
    if lower_message in ["hello", "hi", "hey"]:
        reply = "Hello! I am Offline Helper. How can I help you?"

    elif lower_message == "what is your name?":
        reply = "My name is Offline Helper."

    elif lower_message == "how are you?":
        reply = "I am working properly and ready to help you!"

    elif message.rstrip("?.!।").strip() in [
        "ਭਗਤ ਸਿੰਘ ਕੌਣ ਸਨ",
        "ਭਗਤ ਸਿੰਘ ਕੌਣ ਸੀ"
    ]:
        reply = (
            "ਭਗਤ ਸਿੰਘ ਭਾਰਤ ਦੇ ਆਜ਼ਾਦੀ ਸੰਗਰਾਮ ਦੇ ਇੱਕ ਕ੍ਰਾਂਤੀਕਾਰੀ ਸਨ। "
            "ਉਹ ਬ੍ਰਿਟਿਸ਼ ਰਾਜ ਤੋਂ ਭਾਰਤ ਨੂੰ ਆਜ਼ਾਦ ਕਰਵਾਉਣ ਲਈ ਸੰਘਰਸ਼ ਕਰਨ ਵਾਲੇ "
            "ਆਜ਼ਾਦੀ ਘੁਲਾਟੀਏ ਸਨ।"
        )
        suggestions = [
            "ਭਗਤ ਸਿੰਘ ਦੇ ਜੀਵਨ ਬਾਰੇ ਹੋਰ ਦੱਸੋ।",
            "ਭਗਤ ਸਿੰਘ ਦੀਆਂ ਮੁੱਖ ਇਤਿਹਾਸਕ ਘਟਨਾਵਾਂ ਦੱਸੋ।"
        ]

    elif lower_message == "what is my name?":
        saved_memories = memory.get_memories()
        name = None

        for memory_id, info in reversed(saved_memories):
            info = info.strip()

            if info.lower().startswith("my name is "):
                name = info[len("my name is "):].strip()

                if name.lower() != "Offline Helper":
                    break
                else:
                    name = None

        reply = f"Your name is {name}." if name else "I don't know your name yet."

    else:  # AI response and knowledge processing
        if selected_mode == "online":
            print("Internet available: ONLINE mode")

            online_results = search_web(message, 5)

            # Automatically learn from online search results
            for result in online_results:
                title = result.get("title", "").strip()
                content = result.get("snippet", "").strip()
                source = result.get("url", "").strip()

                if title and content and source and len(content) >= 40:
                    knowledge.save_knowledge(
                        title=title,
                        content=content[:2000],
                        source=source
                    )

            online_context = "\n".join(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Information: {result['snippet']}"
                for result in online_results
            )
        else:
            print("Internet unavailable: OFFLINE mode")
            online_context = ""
        saved_memories = memory.get_memories_with_categories()

        unique_memories = []
        seen = set()

        for memory_id, information, category in saved_memories:
            information = information.strip()
            key = information.casefold()

            if information and key not in seen:
                seen.add(key)
                unique_memories.append(
                    f"[{category.upper()}] {information}"
                )

        memory_context = "\n".join(
            f"- {information}"
            for information in unique_memories
        )

        # Retrieve locally learned knowledge
        learned_results = knowledge.search_learned_knowledge(message)

        learned_context = "\n".join(
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"Information: {content}"
            for title, content, source in learned_results
        )

        personalities = {
            "friendly": (
                "Use a warm, supportive, friendly tone. "
                "Be encouraging and approachable."
            ),
            "professional": (
                "Use a polite, professional and organized tone. "
                "Be clear and avoid unnecessary casual language."
            ),
            "technical": (
                "Use a technical and precise tone, especially for "
                "programming, IT and cybersecurity topics. "
                "Explain technical terms clearly."
            ),
            "casual": (
    "Talk like a normal person having a friendly conversation. "
    "Use everyday words, natural expressions, and a relaxed style. "
    "Avoid textbook-style explanations and overly formal sentences. "
    "You may use contractions like 'it's', 'you're', and 'that's'. "
    "Keep answers engaging, simple, and natural without sounding robotic."
)
        }

        personality_instruction = personalities.get(
            request.personality.lower(),
            personalities["friendly"]
        )

        response_language = detect_response_language(message)
        if False:  # OpenAI backup disabled; Qwen is the primary AI
            if openai_client is None:
                return {
                    "reply": "Online mode is not configured. Please check the API setup."
                }

            response = openai_client.responses.create(
                model="gpt-5.5",
                instructions=(
                    "You are Offline Helper, a helpful multilingual assistant. "
                    + personality_instruction
                    + f" Reply entirely in {response_language}. "
                    "Use natural Punjabi Gurmukhi, Hindi Devanagari, or English. "
                    "Be accurate, clear, friendly, and concise."
                ),
                input=message,
                max_output_tokens=300
            )

            reply = response.output_text.strip()

        else:
            response = ollama.chat(
            model="gemma3:4b",
            messages=[
                {
                    "role": "system",
                    "content": (
                      "You are Offline Helper, a multilingual assistant supporting "
"Punjabi (Gurmukhi), Hindi (Devanagari), and English. "
                        + personality_instruction
+ f" IMPORTANT: Your response language MUST be {response_language}. "
+ "Reply entirely in this language. Do not switch languages. "
+ " LANGUAGE RULES: "
                        "Identify the language of the user's message. "
                    
"Punjabi language rules: "
"Always reply in natural, fluent Punjabi using Gurmukhi script. "
"Write as an educated native Punjabi speaker would speak in everyday conversation. "
"Use simple, familiar Punjabi words and correct Punjabi grammar. "
"Prefer natural Punjabi sentence structures instead of translating English sentences word for word. "
"Keep standard technical terms such as IP address, Python, DNS, server, and computer in English when appropriate. "
"Explain the meaning of technical terms in simple Punjabi. "
"Do not invent Punjabi words or use awkward translations. "
"Do not mix Hindi, Urdu, or Devanagari into Punjabi answers. "
"Use short, complete, meaningful sentences. "
"If you are unsure about a Punjabi word, use a simpler expression that you know is correct. "
"Example: For an IP address, explain that it is a unique address used to identify a device on a network. "
"Example of natural Punjabi: 'IP address ਇੱਕ ਖਾਸ ਪਤਾ ਹੁੰਦਾ ਹੈ, ਜਿਸ ਨਾਲ ਨੈੱਟਵਰਕ ਵਿੱਚ ਕਿਸੇ ਡਿਵਾਈਸ ਦੀ ਪਛਾਣ ਹੁੰਦੀ ਹੈ।' "
"Check Punjabi spelling and grammar before responding. "

                       "HINDI RULES: "
"Reply in natural Hindi using Devanagari script. "
"Understand Roman Hindi and reply in Devanagari Hindi. "
"Write Hindi as a native Hindi speaker would naturally speak. "
"Use simple, everyday Hindi with correct grammar and spelling. "
"Avoid awkward word-for-word translations from English. "
"Keep common technical terms such as Python, DNS, server, and IP address in English when appropriate. "
"Never create unnatural or meaningless Hindi words. "
"Check that every sentence is complete and understandable before replying. "

"ENGLISH RULES: "
"When the current user message is written in English, "
"you MUST reply entirely in English. "
"Use natural, fluent English with correct grammar and spelling. "
"Explain technical topics clearly without unnecessary complicated words. "
"Avoid repetitive sentences and incomplete words. "
"Check that the final answer is complete and meaningful. "
"Do not reply in Punjabi or Hindi to an English-only message. "
"Do not let previous messages change the language of your reply. "

"MIXED LANGUAGE RULES: "
"If the user mixes Punjabi and English, reply mainly in Punjabi using Gurmukhi. "
"If the user mixes Hindi and English, reply mainly in Hindi using Devanagari. "
"If the user's language is unclear, use simple English. "
"Always preserve the user's intended meaning. "
                        "Use simple, common words and natural sentence structure. "
                        "Never mix Gurmukhi and Devanagari. "
                        "Keep answers concise, clear, useful, and conversational. "
                        "Most answers should be between 60 and 120 words. "
                        "Never repeat the same fact in different sentences. "
                        "Use short paragraphs and simple language. "
                        "Give the most important information first. "
                        "Do not add unnecessary introductions or conclusions. "
                        "If the user asks for more information or a detailed explanation, "
                        "provide a longer and more complete answer. "
                        "You can answer general knowledge, history, science, technology, "
                        "education, and everyday questions. "
                   "For historical people and events, use accurate, well-established historical facts. "
"Never invent a person's religion, profession, beliefs, or achievements. "
"Do not add personal greetings before answering factual questions. "
"For Bhagat Singh, identify him as an Indian revolutionary and freedom fighter. "
"When asked 'ਭਗਤ ਸਿੰਘ ਕੌਣ ਸਨ?', use natural Punjabi like: "
"'ਭਗਤ ਸਿੰਘ ਭਾਰਤ ਦੇ ਆਜ਼ਾਦੀ ਸੰਗਰਾਮ ਦੇ ਇੱਕ ਕ੍ਰਾਂਤੀਕਾਰੀ ਅਤੇ ਆਜ਼ਾਦੀ ਘੁਲਾਟੀਏ ਸਨ।' "
"Never invent religious identities or use meaningless Punjabi words. "
"Do not describe him as a religious preacher or invent religious beliefs. "
"Finish every sentence before stopping. "
"Never repeat the same sentence or fact twice. "
                        "When offline, answer using your built-in knowledge and saved memories. "
                        "Do not pretend to have checked live information or accessed the internet. "
                        "When online search results are provided, use them carefully. "
                        "Prioritize reliable sources and distinguish facts from uncertainty. "
                        "Never invent facts, dates, events, or sources. "
                        "If search results do not contain enough information, explain what is missing. "
                        "Do not refuse harmless educational or historical questions. "
                        "Use saved memories only when relevant. "
                        "If asked about the user's name, check saved memories. "
                        "Never claim you cannot remember information that is present in memory.\n"
                        "Saved memories:\n"
                      + (memory_context or "No saved memories yet.")
+ "\n\nLocally learned knowledge:\n"
+ (learned_context or "No matching learned documents.")
+ "\n\nOnline search results:\n"
                        + (online_context or "No online results available.")
                    )
                },
                {
                    "role": "user",
                    "content": message + "\n/no_think"
                }
            ],
            options={
    "num_predict": 1600,
    "temperature": 0.5,
    "repeat_penalty": 1.15,
    "repeat_last_n": 128
}
        )

        reply = response["message"]["content"].strip()


        parts = reply.split("Explore more:", 1)
        answer = parts[0].strip()
        reply = answer
        suggestions = []

        if len(parts) > 1:
            suggestions = [
                item.strip().lstrip("-• ").strip()
                for item in parts[1].splitlines()
                if item.strip() and item.strip() not in ["-", "•"]
            ]

        suggestions = suggestions[:2]

        if not suggestions:
            topic = message.strip().rstrip("?.!।")

            if topic.endswith("ਬਾਰੇ ਦੱਸੋ ਜੀ"):
                topic = topic[:-len("ਬਾਰੇ ਦੱਸੋ ਜੀ")].strip()
            elif topic.endswith("ਬਾਰੇ ਦੱਸੋ"):
                topic = topic[:-len("ਬਾਰੇ ਦੱਸੋ")].strip()
            for phrase in [
                "tell me about ",
                "who is ",
                "who was ",
                "what is ",
                "what was ",
                "explain ",
                "how does ",
                "how do "
            ]:
                if topic.lower().startswith(phrase):
                    topic = topic[len(phrase):].strip()
                    break

            if any("\u0A00" <= char <= "\u0A7F" for char in message):
                suggestions = [
                    f"{topic} ਬਾਰੇ ਹੋਰ ਮਹੱਤਵਪੂਰਨ ਜਾਣਕਾਰੀ ਦਿਓ।",
                    f"{topic} ਨਾਲ ਜੁੜੀਆਂ ਮੁੱਖ ਘਟਨਾਵਾਂ ਕਿਹੜੀਆਂ ਹਨ?"
                ]

            elif any("\u0900" <= char <= "\u097F" for char in message):
                suggestions = [
                    f"{topic} के बारे में और जानकारी दीजिए।",
                    f"{topic} से जुड़ी मुख्य घटनाएँ कौन-सी हैं?"
                ]

            else:
                suggestions = [
                    f"What are the important facts about {topic}?",
                    f"Can you explain more about {topic}?"
                ]

    history.save_chat(message, reply)
    print("DEBUG SUGGESTIONS:", suggestions)

    return {
    "assistant": "Offline Helper",
    "your_message": message,
    "reply": reply,
    "suggestions": suggestions,
    "mode": selected_mode
}

@app.post("/study")
def study_tutor(request: StudyRequest):
    topic = request.topic.strip()

    if not topic:
        return {"reply": "Please enter a topic to study."}

    difficulty = request.difficulty.lower()
    if difficulty not in ["beginner", "intermediate", "advanced"]:
        difficulty = "intermediate"

    difficulty_instruction = {
        "beginner": "Use very simple language. Assume the student is new to the topic. Explain basic terms and give easy examples.",
        "intermediate": "Give a balanced explanation with useful details and practical examples. Assume some basic knowledge.",
        "advanced": "Give a deeper explanation with technical details, complex concepts, limitations, and practical applications."
    }[difficulty]

    try:
        response = ollama.chat(
            model="gemma3:4b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI Study Tutor. "
                        "Teach students in simple, clear English. "
                        "Explain topics step by step. "
                        "Use headings and examples where helpful. "
                        "Include important points and a short summary. "
                        "Keep the explanation educational and accurate. "
                        + difficulty_instruction + " "
"Always finish the lesson with a complete conclusion. "
"Never leave a sentence, list, or question unfinished. "
"End with exactly 3 short revision questions."
                    )
                },
                {
    "role": "user",
    "content": (
      f"Teach me this topic: {topic}\n"
f"Difficulty level: {difficulty}\n"
f"{difficulty_instruction}\n\n"
        + (
            "Continue from this previous lesson. "
            "Briefly review what was already covered, "
            "then teach new information without repeating the entire lesson:\n"
            + request.previous_lesson
            if request.previous_lesson.strip()
            else "This is a new lesson. Start from the basics."
        )
    )
}
            ],
            options={
               "num_predict": 1200,
                "temperature": 0.3,
                "top_p": 0.8
            }
        )

        reply = response["message"]["content"].strip()
        history.save_study_lesson(topic, reply)
        return {
            "assistant": "Offline Helper Study Tutor",
            "topic": topic,
            "reply": reply
        }

    except Exception as error:
        print("Study Tutor Error:", error)
        return {
            "reply": "Sorry, I could not generate the lesson. Please check that Ollama is running and the gemma3:4b model is installed."
        }

@app.post("/study-quiz")
def study_quiz(request: QuizRequest):
    topic = request.topic.strip()

    if not topic:
        return {"error": "Please enter a topic."}

    try:
        response = ollama.chat(
            model="gemma3:4b",
            format="json",
            messages=[
                {
                    "role": "system",
                   "content": (
    "You are an educational quiz generator. "
    "Generate exactly 5 complete multiple-choice questions. "
    "Do not stop after the first question. "
    "Every question must have exactly 4 options. "
    "Each question must have one correct answer. "
    "Use answer values 0, 1, 2, or 3. "
    "Include a short explanation for every question. "
    "Keep questions suitable for students. "
    "For cybersecurity, focus on concepts, defensive practices, "
    "and responsible learning. "
    "Return one complete JSON object with this structure: "
    '{"questions":['
    '{"question":"Question 1","options":["A","B","C","D"],"answer":0,"explanation":"Explanation"},'
    '{"question":"Question 2","options":["A","B","C","D"],"answer":1,"explanation":"Explanation"},'
    '{"question":"Question 3","options":["A","B","C","D"],"answer":2,"explanation":"Explanation"},'
    '{"question":"Question 4","options":["A","B","C","D"],"answer":3,"explanation":"Explanation"},'
    '{"question":"Question 5","options":["A","B","C","D"],"answer":0,"explanation":"Explanation"}'
    ']}'
    "Return valid JSON only. No Markdown or extra text."
)
                },
                {
                    "role": "user",
                    "content": f"Create a quiz about: {topic}"
                }
            ],
            options={
                "num_predict": 1200,
                "temperature": 0.3
            }
        )

        quiz_data = json.loads(
            response["message"]["content"]
        )

        questions = quiz_data.get("questions", [])

        if len(questions) < 5:
            raise ValueError(
                f"AI generated only {len(questions)} questions. Expected 5."
            )

        questions = questions[:5]
        for question in questions:
            if (
                not isinstance(question.get("question"), str)
                or not isinstance(question.get("options"), list)
                or len(question["options"]) != 4
                or not all(isinstance(option, str) for option in question["options"])
                or type(question.get("answer")) is not int
                or question["answer"] not in range(4)
                or not isinstance(question.get("explanation"), str)
            ):
                raise ValueError("Invalid quiz question format.")

        return {"questions": questions}

    except Exception as error:
        print("Study Quiz Error:", error)
        return {"error": "Unable to generate the quiz. Please try again."}
@app.get("/history")
def chat_history():
    saved_history = history.get_chat_history()
    return {
        "assistant": "Offline Helper",
        "history": [
            {
                "id": chat_id,
                "user_message": user_message,
                "assistant_reply": assistant_reply,
                "created_at": created_at
            }
            for chat_id, user_message, assistant_reply, created_at in saved_history
        ]
    }

@app.get("/study-history")
def get_study_history():
    lessons = history.get_study_history()

    return [
        {
            "id": lesson[0],
            "topic": lesson[1],
            "lesson": lesson[2],
            "created_at": lesson[3]
        }
        for lesson in lessons
    ]
    
@app.get("/memories")
def memories_list():
    return {
        "memories": [
            {"id": memory_id, "information": information}
            for memory_id, information in memory.get_memories()
        ]
    }

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)