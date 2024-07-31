import os
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import streamlit as st

# Ruta para guardar el historial de conversaciones
HISTORIAL_PATH = "historial_conversaciones.json"

def initialize_groq_client():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("No se encontró la clave API de Groq. Asegúrate de que esté configurada en el archivo .env")
        st.stop()
    return Groq(api_key=api_key)

def get_ai_response(client, messages):
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )

        response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                response += chunk.choices[0].delta.content
        return response
    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        return None

def save_historial(historial):
    with open(HISTORIAL_PATH, 'w') as file:
        json.dump(historial, file)

def load_historial():
    if os.path.exists(HISTORIAL_PATH):
        with open(HISTORIAL_PATH, 'r') as file:
            return json.load(file)
    return []

def chat():
    st.title("Asistente IA")
    st.write("Bienvenido al chatbot de Asistente IA. Por favor, escribe tu consulta. Escribe Exit o Salir para terminar la conversación.")

    client = initialize_groq_client()

    # Cargar historial de conversaciones
    historial = load_historial()
    historial_actual = []

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    if 'input' not in st.session_state:
        st.session_state['input'] = ""

    # Sidebar para mostrar el historial de conversaciones
    st.sidebar.title("Historial de Conversaciones")
    for i, conv in enumerate(historial):
        if st.sidebar.button(f"Conversación {i+1}"):
            st.session_state['messages'] = conv

    if st.sidebar.button("Nueva Conversación"):
        historial_actual = st.session_state['messages'].copy()
        historial.append(historial_actual)
        save_historial(historial)
        st.session_state['messages'] = []
        st.session_state['input'] = ""

    if st.sidebar.button("Eliminar Historial"):
        historial = []
        save_historial(historial)

    # Display chat history
    st.write("Historial del chat:")
    for message in st.session_state['messages']:
        role = "Tú" if message["role"] == "user" else "IA"
        st.write(f"**{role}**: {message['content']}")

    # Create a form for user input
    with st.form(key='chat_form'):
        user_input = st.text_input("Tú:", key="user_input", value=st.session_state['input'])
        submit_button = st.form_submit_button(label='Enviar')

    # Handle form submission
    if submit_button and user_input:
        if user_input.lower() in ["exit", "salir"]:
            st.write("¡Hasta pronto!")
            st.stop()

        st.session_state['messages'].append({"role": "user", "content": user_input})

        with st.spinner("Generando respuesta..."):
            response = get_ai_response(client, st.session_state['messages'])
            if response:
                st.session_state['messages'].append({"role": "assistant", "content": response})
                st.write(f"**IA**: {response}")
            else:
                st.write("No se recibió respuesta de Groq.")

        # Clear the input
        st.session_state['input'] = ""

    # Add a button to clear the conversation
    if st.button("Limpiar conversación actual"):
        st.session_state['messages'] = []
        st.session_state['input'] = ""

if __name__ == "__main__":
    chat()
