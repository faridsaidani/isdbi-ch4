import os
# from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class DocumentProcessor:
    """
    Handles loading, processing (chunking), and creating vector stores from PDF documents.
    """
    def __init__(self, embedding_model_name="models/embedding-001",
                 chunk_size=1200, chunk_overlap=200, api_key=None):
        # Use provided API key from UI if available, otherwise use from environment
        self.api_key = api_key if api_key else GOOGLE_API_KEY
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file or provide it to the constructor.")
        try:
            self.embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model_name, google_api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize GoogleGenerativeAIEmbeddings. Check API key and model name: {e}")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        print("DocumentProcessor initialized.")

    def load_and_process_pdf(self, file_path: str):
        """Loads a PDF, extracts text, and splits it into manageable chunks."""
        print(f"Loading and processing PDF: {file_path}")
        if not os.path.exists(file_path):
            print(f"Warning: File not found at {file_path}. Returning empty list.")
            return []
        try:
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()
            if not documents:
                print(f"Warning: No content extracted from {file_path}.")
                return []
            texts = self.text_splitter.split_documents(documents)
            print(f"Successfully processed {file_path} into {len(texts)} chunks.")
            return texts
        except Exception as e:
            print(f"Error loading/processing PDF document {file_path}: {e}")
            return []

    def create_vector_store(self, texts, collection_name: str, persist_directory: str = None):
        """Creates a Chroma vector store from text chunks. Can be in-memory or persisted."""
        if not texts:
            print(f"No texts provided for collection '{collection_name}'. Cannot create vector store.")
            return None
        print(f"Creating Chroma vector store for collection: {collection_name}...")
        try:
            if persist_directory:
                # Ensure directory exists if persisting
                os.makedirs(persist_directory, exist_ok=True)
                vector_store = Chroma.from_documents(
                    documents=texts,
                    embedding=self.embeddings,
                    collection_name=collection_name,
                    persist_directory=persist_directory
                )
                # vector_store.persist() # Chroma.from_documents with persist_directory handles this.
                print(f"Chroma store for '{collection_name}' created and persisted at '{persist_directory}'.")
            else: # In-memory
                vector_store = Chroma.from_documents(
                    documents=texts,
                    embedding=self.embeddings,
                    collection_name=collection_name
                )
                print(f"In-memory Chroma store for '{collection_name}' created.")
            return vector_store
        except Exception as e:
            print(f"Error creating Chroma vector store for '{collection_name}': {e}")
            return None

    def load_persisted_vector_store(self, collection_name: str, persist_directory: str):
        """Loads a persisted Chroma vector store."""
        if not os.path.exists(persist_directory):
            print(f"Persist directory '{persist_directory}' for collection '{collection_name}' not found.")
            return None
        print(f"Loading persisted Chroma vector store for collection: {collection_name} from {persist_directory}")
        try:
            vector_store = Chroma(
                collection_name=collection_name,
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Successfully loaded Chroma store '{collection_name}'.")
            return vector_store
        except Exception as e:
            print(f"Error loading persisted Chroma store for '{collection_name}': {e}")
            return None

# --- Conceptual Self-Test (run this file directly to test PDF processing) ---
if __name__ == '__main__':
    PDF_DATA_DIR_TEST = "../data_pdf" # Assumes this script is in utils/
    FAS32_PDF_PATH_TEST = os.path.join(PDF_DATA_DIR_TEST, "fas_32_ijarah.pdf")
    SS9_PDF_PATH_TEST = os.path.join(PDF_DATA_DIR_TEST, "ss_09_ijarah.pdf")

    # Create dummy PDF files if they don't exist for basic testing
    os.makedirs(PDF_DATA_DIR_TEST, exist_ok=True)
    DUMMY_PDF_CONTENT = "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj 4 0 obj<</Length 18>>stream\nBT /F1 24 Tf 100 700 Td (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\n0000000230 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"

    if not os.path.exists(FAS32_PDF_PATH_TEST):
        with open(FAS32_PDF_PATH_TEST, "w") as f: f.write(DUMMY_PDF_CONTENT)
        print(f"Created dummy PDF: {FAS32_PDF_PATH_TEST} (Replace with actual FAS 32 PDF)")
    if not os.path.exists(SS9_PDF_PATH_TEST):
        with open(SS9_PDF_PATH_TEST, "w") as f: f.write(DUMMY_PDF_CONTENT)
        print(f"Created dummy PDF: {SS9_PDF_PATH_TEST} (Replace with actual SS 9 PDF)")

    processor = DocumentProcessor()
    CHROMA_PERSIST_DIR_TEST = "../chroma_db_asave_test" # For testing persistence

    print("\n--- Testing FAS 32 Processing ---")
    fas32_texts_test = processor.load_and_process_pdf(FAS32_PDF_PATH_TEST)
    if fas32_texts_test:
        fas32_vs_test_in_memory = processor.create_vector_store(fas32_texts_test, "fas32_test_in_memory")
        if fas32_vs_test_in_memory:
            retriever = fas32_vs_test_in_memory.as_retriever()
            sample_query_results = retriever.get_relevant_documents("Ijarah term")
            print(f"In-memory FAS32 store query test results: {len(sample_query_results)} documents")

        fas32_vs_test_persisted = processor.create_vector_store(
            fas32_texts_test, "fas32_test_persisted",
            persist_directory=os.path.join(CHROMA_PERSIST_DIR_TEST, "fas32_test_persisted")
        )
        if fas32_vs_test_persisted:
            loaded_fas32_vs = processor.load_persisted_vector_store(
                "fas32_test_persisted",
                persist_directory=os.path.join(CHROMA_PERSIST_DIR_TEST, "fas32_test_persisted")
            )
            if loaded_fas32_vs:
                retriever_loaded = loaded_fas32_vs.as_retriever()
                sample_query_results_loaded = retriever_loaded.get_relevant_documents("objective of standard")
                print(f"Persisted FAS32 store query test results: {len(sample_query_results_loaded)} documents")

    print("\n--- Testing SS 9 Processing ---")
    ss9_texts_test = processor.load_and_process_pdf(SS9_PDF_PATH_TEST)
    if ss9_texts_test:
        ss9_vs_test = processor.create_vector_store(ss9_texts_test, "ss9_test")
        if ss9_vs_test:
             print("SS9 Vector store created successfully (in-memory).")