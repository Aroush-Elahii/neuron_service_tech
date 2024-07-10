import shutil
import os
from pydantic import BaseModel
from fastapi import FastAPI,File, UploadFile,Query
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from fastapi import APIRouter
from langchain_chroma import Chroma
from langchain.globals import set_debug

set_debug(True)


#chat router is being used to make routes in this seprate section


chat_router = APIRouter()




os.environ["OPENAI_API_KEY"] ="insert key here"


class Question(BaseModel):
    query: str
    session_id: str

UPLOAD_DIR = "./uploaded_files"

@chat_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure the upload directory exists
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Define the path where the file will be saved
        file_path = os.path.join(UPLOAD_DIR, file.filename) # type: ignore

        # Check if the file already exists
        if os.path.exists(file_path):
            return {"info": f"File '{file.filename}' already uploaded."}

        # Save the uploaded file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Load and process the document
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        print(splits)
        vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings(), persist_directory="./chroma_vector_db")

        return {"info": f"File '{file.filename}' uploaded and processed successfully."}
    except Exception as e:
        print(e)
        return {"error": str(e)}



@chat_router.post("/chat/")
def handle_query(query: Question):


    # load vectorstore

    vectorstore = Chroma(persist_directory="./chroma_vector_db", embedding_function=OpenAIEmbeddings())
    

    # make retriever out of vector store
    retriever = vectorstore.as_retriever(score_threshold=80)

    

    # Initialize the language model and template prompts
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    
    #make prompt to modify question according to history, so we get better retrieval data

    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])


    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)



    qa_system_prompt =  """
    You are a helpful assistant Your name is Neuron. 
    Use the following context as your learned knowledge.

    context : "{context}"

    When answer to user:
    - If you don't know, just say that you don't know.
    - If you don't know when you are not sure, ask for clarification.
    Avoid mentioning that you obtained the information from the context.
    And answer according to the language of the user's question.
    And dont mention context
    """
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    


    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        return MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string="mongodb://localhost:27017/",
            database_name="nst",
            collection_name="chat_histories",
        )

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
        
    )

    answer = conversational_rag_chain.invoke(
        {"input": query.query},
        config={"configurable": {"session_id": query.session_id}}
    )



    return {"answer": answer["answer"]}









@chat_router.get("/uploaded-files")
def get_unique_files():
    # Initialize the Chroma vector store
    vectorstore = Chroma(persist_directory="./chroma_vector_db", embedding_function=OpenAIEmbeddings())

    # Get all documents from the vector store
    all_docs = vectorstore.get()
    data = all_docs['metadatas']

    # Extract unique filenames
    unique_files = set(doc['source'] for doc in data)

    # Convert set to list
    unique_files_list = list(unique_files)

    return {"uploaded_files": unique_files_list}




async def get_chat_history(session_id: str):
    chat_message_history = MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string="mongodb://localhost:27017/",
        database_name="nst",
        collection_name="chat_histories",
    )

    messages = await chat_message_history.aget_messages()

    message_list = []
    for message in messages:
        msg_dict = message.dict()
        msg_format = {
            'text': msg_dict['content'],
            'type': msg_dict['type']
        }
        message_list.append(msg_format)
        
    return message_list

@chat_router.get("/chat_history")
async def chat_history(session_id: str = Query(...)):
    return await get_chat_history(session_id)


