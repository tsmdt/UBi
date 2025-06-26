import chainlit as cl
from chainlit import Message
from fastapi import Request, Response
from db import save_interaction
from rag_pipeline import process_message_with_memory
from conversation_memory import session_memory, MessageRole
from rss_reader import get_rss_items
from custom_data_layer import CustomDataLayer
from free_seats import get_occupancy_data, make_plotly_figure
# from website_search import search_ub_website


# === Authentication (optional) ===
users = [
    cl.User(identifier="1", display_name="Admin", metadata={"username": "admin", "password": "admin"})
]

# === Data Layer ===
@cl.data_layer
def get_data_layer():
    return CustomDataLayer()

# === Starter Buttons ===
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Öffnungszeiten", message="Ist die Bibliothek jetzt geöffnet?"),
        cl.Starter(label="Sitzplätze", message="Gibt es aktuell freie Sitzplätze in der Bibliothek?"),
        cl.Starter(label="Services", message="Liste alle Dienstleistungen an der UB Mannheim auf"),
        cl.Starter(label="Standorte", message="Standorte der UB Mannheim"),
        cl.Starter(label="Neuigkeiten", message="Neues aus der UB"),
    ]

# === Chat Start: Initialize Session Memory ===
@cl.on_chat_start
async def on_chat_start():
    session_id = cl.user_session.get("id") or "unknown"
    cl.user_session.set("session_id", session_id)
    
    # Clear any existing session memory for this user
    session_memory.clear_session(session_id)

# === Chat Message Handler ===
@cl.on_message
async def on_message(message: cl.Message):
    user_input = message.content.strip()
    session_id = cl.user_session.get("session_id") or "unknown"

    # RSS feed
    news_keywords = ["news", "neues", "neuigkeiten", "aktuelles", "nachrichten"]
    if any(keyword in user_input.lower() for keyword in news_keywords):
        items = get_rss_items()
        if not items:
            response = "Keine Neuigkeiten gefunden."
            await Message(content=response).send()
        else:
            response = "\n\n".join(f"- **{title}**\n  {link}" for title, link in items)
            await Message(content=response).send()
        
        # Add to memory
        session_memory.add_turn(session_id, MessageRole.USER, user_input)
        session_memory.add_turn(session_id, MessageRole.ASSISTANT, response)
        await save_interaction(session_id, user_input, response)
        return

    # Free seats
    seat_keywords = ["sitzplatz", "sitzplätze", "arbeitsplatz", "arbeitsplätze", "arbeitsplätzen",
                     "plätze", "freier platz", "freie plätze", "seats", "workspaces"]
    if any(keyword in user_input.lower() for keyword in seat_keywords):
        try:
            data = get_occupancy_data()
            areas = data["areas"]
            fig = make_plotly_figure(areas)
            response = f"📅 Zuletzt aktualisiert: {data['lastupdated']}"

            await cl.Message(
                content=response,
                elements=[
                    cl.Plotly(name="Bibliotheksauslastung", figure=fig, display="inline", size="large")
                ]
            ).send()
            
            # Add to memory
            session_memory.add_turn(session_id, MessageRole.USER, user_input)
            session_memory.add_turn(session_id, MessageRole.ASSISTANT, response)
            await save_interaction(session_id, user_input, response)
        except Exception as e:
            error_response = f"❌ Fehler beim Abrufen der Sitzplatzdaten: {str(e)}"
            await cl.Message(content=error_response).send()
            
            # Add to memory
            session_memory.add_turn(session_id, MessageRole.USER, user_input)
            session_memory.add_turn(session_id, MessageRole.ASSISTANT, error_response)
            await save_interaction(session_id, user_input, error_response)
        return

    # RAG Response with Memory
    try:
        response = await process_message_with_memory(session_id, user_input)
        await Message(content=response).send()
        await save_interaction(session_id, user_input, response)
    except Exception as e:
        error_response = f"❌ Fehler bei der Verarbeitung: {str(e)}"
        await Message(content=error_response).send()
        
        # Add error to memory
        session_memory.add_turn(session_id, MessageRole.USER, user_input)
        session_memory.add_turn(session_id, MessageRole.ASSISTANT, error_response)
        await save_interaction(session_id, user_input, error_response)

    # Optional: fallback to web search
    # fallback = search_ub_website(user_input)
    # await Message(content=f"Ich konnte nichts Genaues finden. Ergebnisse von der UB-Website:\n\n{fallback}").send()
    # await save_interaction(session_id, user_input, fallback)

# === Chat End ===
@cl.on_chat_end
async def on_chat_end():
    session_id = cl.user_session.get("session_id")
    if session_id:
        # End session and clear memory
        session_memory.end_session(session_id)
    print("User disconnected.")

# === Logout ===
@cl.on_logout
def on_logout(request: Request, response: Response):
    for cookie_name in request.cookies.keys():
        response.delete_cookie(cookie_name)

# === Optional: Password Auth ===
# @cl.password_auth_callback
# def on_login(username: str, password: str) -> Optional[cl.User]:
#     for user in users:
#         if user.metadata["username"] == username and user.metadata["password"] == password:
#             return user
#     return None
