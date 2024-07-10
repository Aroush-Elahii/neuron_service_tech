from fastapi import FastAPI,File, UploadFile
import shutil
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory # old history inmemory
from langchain_community.chat_message_histories.postgres import PostgresChatMessageHistory # new history postgres

from langchain_chroma import Chroma
from langchain.globals import set_debug

set_debug(True)



import os
import tempfile

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
