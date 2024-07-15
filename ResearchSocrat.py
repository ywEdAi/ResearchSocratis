import json
import time

import streamlit as st
import openai
from openai import OpenAI
from streamlit_markmap import markmap

#######################################
# PREREQUISITES
#######################################

st.set_page_config(
    page_title="Wanderlust",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.title("ResearchSocrat")
st.write("Research tutor that guides students for independent research based on research methodologies and Socratic questioning")

st.write("Please ask questions about how to conduct an independent research related to your interested topic")

assistant_id = 'asst_EaBv4T3DNDv8CMlMDLu19mHm'

# Some helper functions
def getMarkupFromProvidedContent(content):
    if len(content) > 10000:
        content = content[:10000]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": "please extract the key concepts and ideas from the content for the purpose of generating a mindmap to help a high school student learn systematically. PLEASE GENERATE OUTPUT AS MARKUP LANGUAGE.Please also adjust the format and markup language accordingly if it is chinese"
            },
            {
            "role": "user",
            "content": content
            }
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    assistant_reply = response.choices[0].message.content.strip()

    return assistant_reply    

# Function to verify OpenAI API key
def verify_api_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        # Attempt to make a simple API call to verify the key
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                "role": "system",
                "content": "Say Hello"
                }
            ],
            temperature=0,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response is not None
    except RuntimeError:
        st.write("Invalid API Key")
        return False
    
    
# Sidebar for API key input
aopen_api_key = st.sidebar.text_input("Enter your OpenAI API Key/请输入您的 OpenAI API Key", type="password")

if aopen_api_key:
    if verify_api_key(aopen_api_key):
        st.sidebar.success("API Key is valid")

        client = OpenAI(api_key=aopen_api_key)

        assistant_state = "assistant"
        thread_state = "thread"
        conversation_state = "conversation"
        last_openai_run_state = "last_openai_run"
        answers = "answers"

        user_msg_input_key = "input_user_msg"

        #######################################
        # SESSION STATE SETUP
        #######################################

        if (assistant_state not in st.session_state) or (thread_state not in st.session_state):
            st.session_state[assistant_state] = client.beta.assistants.retrieve(assistant_id)
            st.session_state[thread_state] = client.beta.threads.create()

        if conversation_state not in st.session_state:
            st.session_state[conversation_state] = []

        if last_openai_run_state not in st.session_state:
            st.session_state[last_openai_run_state] = None

        if answers not in st.session_state:
            st.session_state[answers] = None

        #######################################
        # TOOLS SETUP
        #######################################



        #######################################
        # HELPERS
        #######################################

        def get_assistant_id():
            return st.session_state[assistant_state].id

        def get_thread_id():
            return st.session_state[thread_state].id

        def get_run_id():
            return st.session_state[last_openai_run_state].id

        def on_text_input(status_placeholder):
            """Callback method for any chat_input value change
            """
            if st.session_state[user_msg_input_key] == "":
                return

            client.beta.threads.messages.create(
                thread_id=get_thread_id(),
                role="user",
                content=st.session_state[user_msg_input_key],
            )
            st.session_state[last_openai_run_state] = client.beta.threads.runs.create(
                assistant_id=get_assistant_id(),
                thread_id=get_thread_id(),
            )

            completed = False

            # Polling
            with status_placeholder.status("Computing Assistant answer") as status_container:
                st.write(f"Launching run {get_run_id()}")

                while not completed:
                    run = client.beta.threads.runs.retrieve(
                        thread_id=get_thread_id(),
                        run_id=get_run_id(),
                    )

                    if run.status == "completed":
                        st.write(f"Completed run {get_run_id()}")
                        status_container.update(label="Assistant is done", state="complete")
                        completed = True

                    else:
                        time.sleep(0.1)

            st.session_state[conversation_state] = [
                (m.role, m.content[0].text.value)
                for m in client.beta.threads.messages.list(get_thread_id()).data
            ]

        def on_reset_thread():
            client.beta.threads.delete(get_thread_id())
            st.session_state[thread_state] = client.beta.threads.create()
            st.session_state[conversation_state] = []
            st.session_state[last_openai_run_state] = None

        #######################################
        # SIDEBAR
        #######################################

        with st.sidebar:
            st.header("Debug")
            st.write(st.session_state.to_dict())

            st.button("Reset Thread", on_click=on_reset_thread)

        #######################################
        # MAIN
        #######################################

        left_col, right_col = st.columns(2)

        mindmap_content = ""
        with left_col:
            with st.container():
                for role, message in st.session_state[conversation_state]:
                    with st.chat_message(role):
                        st.write(message)
            status_placeholder = st.empty()

        with right_col:
            st.write("Mindmap on demand")
            if st.session_state[conversation_state] and st.session_state[conversation_state][0]:
                content = st.session_state[conversation_state][0][1]
                if content and len(content) > 0:
                    markup = getMarkupFromProvidedContent(content)
                    markmap(markup, height=800)

        st.chat_input(
            placeholder="Ask your question here",
            key=user_msg_input_key,
            on_submit=on_text_input,
            args=(status_placeholder,),
        )

    else:
        st.sidebar.error("Invalid API Key. Please try again.")
else:
    st.write("Please enter your OpenAI API Key in the sidebar to use the app.")
