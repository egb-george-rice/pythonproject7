import streamlit as st
import boto3
import json

# Initialize the Bedrock Runtime client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def query_knowledge_base(query, conversation_history):
    # Ensure the conversation alternates between user and assistant
    if len(conversation_history) == 0 or conversation_history[-1]["role"] != "user":
        # Add the new user query to the conversation history
        conversation_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": query
                }
            ]
        })

    # Define the payload for the Claude 3.5 Sonnet model
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": conversation_history
    }

    # Call the Bedrock Runtime API to query the knowledge base
    response = bedrock_client.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        body=json.dumps(payload),
        contentType='application/json',
        accept='application/json'
    )

    # Parse the response
    response_body = json.loads(response['body'].read())

    # Extract the text from the content key
    if 'content' in response_body and len(response_body['content']) > 0:
        assistant_response = response_body['content'][0]['text']
        # Add the assistant's response to the conversation history
        conversation_history.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": assistant_response
                }
            ]
        })
        return assistant_response, conversation_history
    else:
        return 'No output found in response', conversation_history

# Streamlit app
st.set_page_config(layout="wide")
st.title("AWS Knowledge Base Query")

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Layout
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### Enter your query")
    with st.form(key='query_form'):
        query = st.text_input("Query", placeholder="*Enter next question here.*", label_visibility="collapsed")
        submit_button = st.form_submit_button(label='Submit')
        if submit_button and query:
            response, st.session_state.conversation_history = query_knowledge_base(query, st.session_state.conversation_history)
            # Clear the input field after submission
            st.session_state['query'] = ''
            st.experimental_rerun()

with col2:
    st.markdown("### Conversation History")
    conversation_container = st.container()
    with conversation_container:
        # Display conversation in reverse order (newest to oldest)
        for message in reversed(st.session_state.conversation_history):
            role = message['role']
            text = message['content'][0]['text']
            if role == 'user':
                st.markdown(f"**You:** {text}")
            else:
                st.markdown(f"**Claude 3.5 Sonnet:** {text}")

    # Make the conversation history scrollable
    conversation_container.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"] > div:first-child {
            max-height: 500px;
            overflow-y: auto;
            display: flex;
            flex-direction: column-reverse;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
