import os
import time
import openai
from openai import OpenAI
import streamlit as st
import json
import time

## connecting to api
try:
    def initialize_openai_client(api_key):
        return openai.OpenAI(api_key=api_key)

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    ## attaching the file
    with st.sidebar:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file = client.files.create(
        file= open(temp_file_path, "rb"),
        purpose='assistants'
        )
    ## creating assistant that help in reading files

    assistant = client.beta.assistants.create(
        name = "PDF Reader ChatBot",
        instructions = "You help in people query related to their files questions honestly.",
        tools = [{"type":"retrieval"}],
        model = "gpt-3.5-turbo-1106",
        file_ids=[file.id]
    )

    def show_json(obj):
        print(json.dumps(json.loads(obj.model_dump_json()), indent=4))

    show_json(assistant)

    ## creating the thread
    thread = client.beta.threads.create()

    ## adding the msg to thread
    def submit_message(assistant_id, thread, user_message):
        client.beta.threads.messages.create(
            thread_id=thread.id, 
            role="user", 
            content=user_message
        )
        return client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
        )

    ## waiting for run status complete
    def wait_on_run(run, thread):
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.10)
        return run

    ## response
    def get_response(thread):
        return client.beta.threads.messages.list(
            thread_id=thread.id
        )

    def pretty_print(messages):
        responses = []
        for m in messages:
            if m.role == "assistant":
                responses.append(m.content[0].text.value)
        return "\n".join(responses)


    st.title("PDF Analyzer  :mag:")

    # Description for PDF Analyzer
    st.markdown("""
        Use this tool to extract valuable information from PDF documents.
        Upload a PDF file and enter your specific query related to the document.
    """)

    # uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    user_query = st.text_input("Enter your query about the PDF:")

    if user_query:
        with st.spinner('Analyzing PDF...'):
            try:
                thread = client.beta.threads.create()
                run = submit_message(assistant.id, thread, user_query)
                run = wait_on_run(run, thread)
                response_messages = get_response(thread)
                response = pretty_print(response_messages)
                st.text_area("Response:", value=response, height=300)
            except Exception as e:
                st.error(f"An error occurred: {e}")
except Exception as e:
    st.markdown("""
                ## Please Upload Your PDF File To Start Discussion
                """)