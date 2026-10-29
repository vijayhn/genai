import json
import os
import streamlit as st
from ollama import chat

# Configuration
MODEL_NAME = "qwen2.5-coder:14b"  # Change this to match your exact downloaded model name (e.g., 'llama3.2:7b')
JSON_FILE = "chat_context.json"
MD_FILE = "chat_context.md"

# Streamlit Page Settings
st.set_page_config(page_title="Syntax AI Assistant", page_icon="🤖", layout="centered")
st.title("🤖 Local AI Code Assist")

# Sidebar Configuration
st.sidebar.header("Chat Settings")
file_format = st.sidebar.selectbox("Save History Format", ["JSON", "Markdown (.md)"])

# Helper Functions to Save History
def save_as_json(messages):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4, ensure_ascii=False)

def save_as_markdown(messages):
    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write("# Chat Session Log\n\n")
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            f.write(f"### **{role}**\n{content}\n\n---\n\n")

def persist_context(messages):
    if file_format == "JSON":
        save_as_json(messages)
    else:
        save_as_markdown(messages)

# Helper Functions to Load History
def load_context():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Initialize Session State (Streamlit's internal memory)
if "messages" not in st.session_state:
    saved_messages = load_context()
    if saved_messages:
        st.session_state.messages = saved_messages
    else:
        st.session_state.messages = [{"role": "system", "content": "You are a helpful local AI assistant."}]

# Clear History Button
if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = [{"role": "system", "content": "You are a helpful local AI assistant."}]
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
    if os.path.exists(MD_FILE):
        os.remove(MD_FILE)
    st.rerun()

# Display current chat messages (skipping the system prompt for a cleaner UI)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# User input field
if user_input := st.chat_input("Message your local LLM..."):
    # 1. Display User Message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Stream AI Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = chat(model=MODEL_NAME, messages=st.session_state.messages, stream=True)
            for chunk in stream:
                token = chunk["message"]["content"]
                full_response += token
                # Real-time streaming update on screen
                response_placeholder.markdown(full_response + "▌")
            
            # Finalize response window without cursor token
            response_placeholder.markdown(full_response)
            
        except Exception as e:
            st.error(f"Failed to connect to Ollama. Is it running? Error: {e}")
            full_response = "Error connecting to local server."
            response_placeholder.markdown(full_response)

    # 3. Save response to session and instantly commit to local disk
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    persist_context(st.session_state.messages)
