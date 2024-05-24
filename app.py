from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_community.llms import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
import streamlit as st
import os
import time
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def getEmbeddings():
    model_name = "BAAI/bge-small-en"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    hf = HuggingFaceBgeEmbeddings(model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs)
    return hf

if not os.path.exists('database'):
    os.mkdir('database')

if 'template' not in st.session_state:
    st.session_state.template = """You are HAPPYLAMMA chatbot, here to help with questions of the user regarding neuroscience. Your tone should be professional and informative.
    I am providing you question from user and context. I want you to contruct solution from the provided context.

    Context: {context}

    User: {question}
    Chatbot:"""
if 'prompt' not in st.session_state:
    st.session_state.prompt = PromptTemplate(
        input_variables=["history", "context", "question"],
        template=st.session_state.template,
    )
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=True,
        input_key="question")
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = Chroma(persist_directory='database',
                                          embedding_function=getEmbeddings()
                                          )
if 'llm' not in st.session_state:
    st.session_state.llm = Ollama(base_url="http://localhost:11434",
                                  model="phi3",
                                  verbose=True,
                                  callback_manager=CallbackManager(
                                      [StreamingStdOutCallbackHandler()]),
                                  )

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


path = "logo2.png"
left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image(path)
st.markdown("<h1 style='text-align: center; color: grey;'>HAPPYLAMMA Chatbot</h1>", unsafe_allow_html=True)


for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["message"])



st.session_state.retriever = st.session_state.vectorstore.as_retriever(
    search_kwargs={"k": 5}
)
# Initialize the QA chain
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = RetrievalQA.from_chain_type(
        llm=st.session_state.llm,
        chain_type='stuff',
        retriever=st.session_state.retriever,
        verbose=False,
        chain_type_kwargs={
            "verbose": False,
            "prompt": st.session_state.prompt,
            "memory": st.session_state.memory,
        }
    )

# Chat input
if user_input := st.chat_input("You:", key="user_input"):
    user_message = {"role": "user", "message": user_input}
    st.session_state.chat_history.append(user_message)
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("Assistant is typing..."):
            response = st.session_state.qa_chain(user_input)
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response['result'].split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response + "")
    chatbot_message = {"role": "assistant", "message": response['result']}
    st.session_state.chat_history.append(chatbot_message)