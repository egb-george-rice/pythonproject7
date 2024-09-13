import streamlit as st
import boto3
import json

# Initialize the Bedrock Runtime client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def query_knowledge_base(query, conversation_history):
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
st.title("AWS Knowledge Base Query")

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

query = st.text_input("Enter your query:")

if st.button("Submit"):
    if query:
        response, st.session_state.conversation_history = query_knowledge_base(query, st.session_state.conversation_history)
        st.write("Response (Claude 3.5 Sonnet):")
        st.write(response)
    else:
        st.write("Please enter a query.")

# Display the conversation history
st.write("Conversation History:")
for message in st.session_state.conversation_history:
    role = message['role']
    text = message['content'][0]['text']
    st.write(f"{role.capitalize()}: {text}")

# Provide a new prompt box for continuing the conversation
st.text_input("Continue the conversation:", key="new_query")
