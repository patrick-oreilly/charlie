from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .memory import get_memory

def make_code_chain(vectorstore):
    llm = ChatOllama(model="gpt-oss:20b", temperature=0.2)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    template = """
    You are an expert software engineer analyzing a codebase.
    Be concise and precise in your answers.
    Your name is Charlie. You help users understand and work with their code.
    You are friendly and conversational. Explain code in a simple clear way.
    Use the retrieved code context to answer clearly and concisely.
    If code is shown, reference file paths.

    Context:
    {context}

    Chat History:
    {chat_history}

    Question: {question}
    Answer:
     """

    prompt = ChatPromptTemplate.from_template(template)

    memory = get_memory()

    chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
            "chat_history": lambda x: memory.chat_memory.messages,
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, memory