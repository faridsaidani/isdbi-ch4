# 🕋 ASAVE: AAOIFI Standard Augmentation & Validation Engine (MVP) 🚀

**Hackathon Project** - _Leveraging Google Gemini & Langchain to Enhance AAOIFI Standards_

Welcome to ASAVE, a cutting-edge AI-powered tool designed to enhance and validate Islamic financial standards, specifically focusing on AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards. This project leverages advanced AI models, such as Google's Gemini, and the LangChain framework to provide insights, suggestions, and validations for financial accounting standards.

---

## 🌟 Project Goal

ASAVE aims to demonstrate how Artificial Intelligence, specifically Large Language Models (LLMs) like Google's Gemini, orchestrated with the Langchain framework, can assist the Accounting and Auditing Organization for Islamic Financial Institutions (AAOIFI) in:

1.  **Reviewing** existing Financial Accounting Standards (FAS).
2.  **Suggesting** AI-driven updates, clarifications, or enhancements.
3.  **Validating** proposed changes for Shari'ah compliance, inter-standard consistency, and practical applicability.

This project focuses on building a Minimum Viable Product (MVP) to showcase this capability.

## 📜 Problem Statement

AAOIFI standards are complex and critical for the Islamic finance industry. Keeping them up-to-date, ensuring clarity, consistency, and robust Shari'ah alignment is a continuous and demanding process. Manual review can be time-consuming and may overlook subtle inconsistencies or areas needing modernization in light of evolving global accounting practices (like IFRS) and new financial product innovations.

## 🌟 Key Features

1. **📚 Document Analysis**: Analyze AAOIFI Financial Accounting Standards (FAS) and Shari'ah Standards (SS).
2. **🧠 Ambiguity Detection**: Identify ambiguities or areas for improvement in standards.
3. **💡 AI-Driven Suggestions**: Generate suggestions to improve clarity and compliance.
4. **⚖️ Shari'ah Compliance Validation**: Validate compliance with Shari'ah principles.
5. **🔗 Inter-Standard Consistency**: Ensure consistency between FAS and SS documents.
6. **🌐 Streamlit Interface**: User-friendly web interface for seamless interaction.

---

## ✨ Our Solution: A Multi-Agent AI System

ASAVE employs a multi-agent system (MAS) architecture where specialized AI agents collaborate to analyze and enhance AAOIFI standards. Each agent has clear duties:

**Core Technologies:**
*   🧠 **Google Gemini Pro/Flash:** The primary Large Language Model for understanding, generation, and reasoning.
*   🔗 **Langchain:** Framework for developing applications powered by LLMs, managing agents, chains, prompts, and tools.
*   📄 **PyMuPDF (`fitz`):** For robust PDF document loading and text extraction.
*   💾 **ChromaDB:** For creating and querying vector stores (semantic search on standard texts).
*   🖥️ **Streamlit:** For building the interactive user interface for AAOIFI experts.

**Knowledge Base (KB) 📚:**
A crucial component, the KB consists of:
*   Selected AAOIFI Financial Accounting Standards (FAS) in PDF format (e.g., FAS 32 - Ijarah).
*   Related AAOIFI Shari'ah Standards (SS) in PDF format (e.g., SS 9 - Ijarah).
*   A simplified JSON file of explicit Shari'ah rules for direct validation checks.
*   (Conceptually) Other comparative standards (IFRS), academic papers, etc.

**Key Agents & Their Roles:**

1.  **📄 Document Processor (`utils/document_processor.py`):**
    *   **Duty:** Loads PDF documents (FAS, SS), splits them into manageable chunks, generates vector embeddings using Gemini, and creates/loads ChromaDB vector stores.
    *   **Tech:** PyMuPDF, Langchain TextSplitters, GoogleGenerativeAIEmbeddings, ChromaDB.

2.  **🧐 Extraction Agent (KEEA - `agents/extraction_agent.py`):**
    *   **Duty:** Reviews standard text to extract key elements, identify definitions, and pinpoint potentially ambiguous or unclear sections.
    *   **Tech:** Gemini, Langchain LLMChain, RetrievalQA (from FAS vector store).

3.  **💡 Suggestion Agent (AISGA - `agents/suggestion_agent.py`):**
    *   **Duty:** Proposes AI-driven modifications, clarifications, or enhancements to the standard based on KEEA's findings and retrieved context from FAS and SS.
    *   **Tech:** Gemini, Langchain LLMChain, Retrieval Augmented Generation (RAG) principles. Generates suggestions *and* provides reasoning with Shari'ah alignment considerations.

4.  **⚖️ Validation Agent (SCVA & ISCCA - `agents/validation_agent.py`):**
    *   **SCVA (Shari'ah Compliance):** Validates AISGA's suggestions against explicit Shari'ah rules (from JSON) and general principles (retrieved from SS vector store).
    *   **ISCCA (Inter-Standard Consistency - Conceptual for MVP):** Checks for terminology consistency and potential conflicts with other AAOIFI standards.
    *   **Tech:** Gemini, Langchain LLMChain, custom rule checking logic, RetrievalQA (from SS/FAS vector stores).

5.  **⚙️ Orchestration & Workflow Agent (OWA - `main_orchestrator.py`):**
    *   **Duty:** Manages the flow of information and tasks between the agents. Initializes all components dynamically based on user-selected standards.
    *   **Tech:** Python scripting, Langchain (conceptual use of AgentExecutor or SequentialChains for more advanced versions).

6.  **🧑‍💻 Human Expert Review & Approval Interface Agent (HERAIA - `app.py`):**
    *   **Duty:** Provides an interactive web interface for AAOIFI experts to select standards, trigger the AI analysis, review AI outputs (suggestions, reasoning, validations), and make final decisions.
    *   **Tech:** Streamlit.

## 🚀 Project Roadmap (MVP Focus)

1.  **Setup & Data Prep:** Environment, API keys, gather initial FAS/SS PDFs.
2.  **Core Agent Logic:** Implement KEEA, AISGA, and a simplified SCVA.
3.  **Vector Stores:** Use PyMuPDF for loading, Langchain for chunking/embedding, ChromaDB for storage.
4.  **Basic Orchestration:** Script the flow: KEEA → AISGA → SCVA.
5.  **Streamlit UI:** Develop HERAIA to allow dynamic standard selection, trigger analysis, and display results with AI reasoning and validation outputs.

## 🏗️ Project Structure

The project is organized as follows:

```
ASAVE Project
├── app.py                  # Streamlit web application
├── main_orchestrator.py    # Orchestrates the workflow between agents
├── requirements.txt        # Python dependencies
├── agents/                 # Specialized AI agents
│   ├── base_agent.py       # Base class for AI agents
│   ├── extraction_agent.py # Extracts ambiguities and key elements
│   ├── suggestion_agent.py # Generates suggestions for improvement
│   ├── validation_agent.py # Validates Shari'ah compliance
├── data/                   # Processed data files
├── data_pdf/               # Raw PDF files for FAS and SS
├── knowledge_bases/        # Knowledge bases for Shari'ah rules
├── utils/                  # Utility functions
│   ├── document_processor.py # Handles PDF processing and vectorization
```

---

## 🛠️ How It Works

### 1. **Initialization**
- Load environment variables from `.env` (e.g., `GOOGLE_API_KEY`).
- Select FAS and SS documents from the `data_pdf/` directory.
- Initialize AI components using the `main_orchestrator.py`.

### 2. **Document Processing**
- PDFs are processed and vectorized using `document_processor.py`.
- Vector stores are created for semantic search and context retrieval.

### 3. **Analysis Workflow**
- **KEEA (Key Element Extraction Agent)**: Identifies ambiguities or focus points in the text.
- **AISGA (AI Standard Generation Agent)**: Suggests improvements and ensures Shari'ah alignment.
- **SCVA (Shari'ah Compliance Validation Agent)**: Validates compliance with Shari'ah principles.
- **ISCCA (Inter-Standard Consistency Check Agent)**: Ensures consistency between FAS and SS.

### 4. **Results Presentation**
- Results are displayed in the Streamlit interface, including:
  - Original text under review
  - AI-driven suggestions
  - Shari'ah compliance status
  - Inter-standard consistency status

---

## 🚀 Getting Started

### Prerequisites

1. Install Python 3.10 or higher.
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(This includes: `langchain langchain-google-genai langchain-community google-generativeai pymupdf chromadb streamlit python-dotenv`)*
4. Add your `GOOGLE_API_KEY` to a `.env` file:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   ```
5. Prepare Data:
   * Create a directory `data_pdf/` in the project root.
   * Place your AAOIFI standard PDF files (e.g., `fas_32_ijarah.pdf`, `ss_09_ijarah.pdf`) inside `data_pdf/`.
     * _Note: The application includes a fallback to create dummy PDFs if these are missing, but **real content is required for meaningful results**._
   * Ensure `knowledge_bases/shariah_rules_explicit.json` exists with your defined explicit rules.

### Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Open the app in your browser at `http://localhost:8501`.
3. In the sidebar, select the FAS and related SS PDF documents you wish to process.
4. Click "🔄 Initialize/Load Selected Standards". Wait for the process to complete.
5. Once initialized, paste or type a specific section from the selected FAS into the text area in the sidebar.
6. Click "🚀 Analyze & Suggest Enhancements".
7. View the results in the main panel.

## 🛠️ How to Run the MVP

1.  **Clone the Repository:**
    ```bash
    # git clone <your-repo-url>
    # cd asave_hackathon_project
    ```
2.  **Create a Python Virtual Environment:** (Recommended)
    ```bash
    python -m venv venv
    # Windows:
    # .\venv\Scripts\activate
    # macOS/Linux:
    # source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Create a `requirements.txt` file with all necessary packages: `langchain langchain-google-genai langchain-community google-generativeai pymupdf chromadb streamlit python-dotenv`)*

4.  **Set up Environment Variable:**
    *   Create a file named `.env` in the project root (`asave_hackathon_project/`).
    *   Add your Google API Key:
        ```env
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
        ```

5.  **Prepare Data:**
    *   Create a directory `data_pdf/` in the project root.
    *   Place your AAOIFI standard PDF files (e.g., `fas_32_ijarah.pdf`, `ss_09_ijarah.pdf`) inside `data_pdf/`.
        *   _Note: The application includes a fallback to create dummy PDFs if these are missing, but **real content is required for meaningful results**._
    *   Ensure `knowledge_bases/shariah_rules_explicit.json` exists with your defined explicit rules.

6.  **Run the Streamlit Application:**
    ```bash
    streamlit run app.py
    ```
    This will open the ASAVE interface in your web browser.

7.  **Using the Application:**
    *   In the sidebar, select the FAS and related SS PDF documents you wish to process.
    *   Click "🔄 Initialize/Load Selected Standards". Wait for the process to complete (this involves PDF parsing, chunking, embedding, and vector store creation).
    *   Once initialized, paste or type a specific section from the selected FAS into the text area in the sidebar.
    *   Click "🚀 Analyze & Suggest Enhancements".
    *   View the original text, AI-identified focus points, AI-generated suggestions with reasoning, and Shari'ah/consistency validation reports in the main panel.

---

## 🧩 Components

### 1. **BaseAgent**
- Initializes the Gemini LLM using LangChain.
- Provides methods to create and invoke AI chains.

### 2. **Specialized Agents**
- **ExtractionAgent**: Extracts ambiguities and key elements.
- **SuggestionAgent**: Generates AI-driven suggestions.
- **ValidationAgent**: Validates Shari'ah compliance.

### 3. **Orchestrator**
- Coordinates the flow between agents.
- Manages document processing and vector store creation.

### 4. **Streamlit Interface**
- User-friendly interface for selecting documents, analyzing text, and viewing results.

---

## 📂 Data

- **Raw PDFs**: Stored in `data_pdf/`.
- **Processed Data**: Stored in `data/`.
- **Knowledge Bases**: JSON files with Shari'ah rules in `knowledge_bases/`.

---

## 🛡️ Error Handling

- Missing API keys or files are reported in the UI.
- Detailed error tracebacks are displayed for debugging.

---

## 🧪 Example Workflow

1. Select `fas_32_ijarah.pdf` and `ss_09_ijarah.pdf` from the sidebar.
2. Paste a section of text for analysis.
3. Click "Analyze & Suggest Enhancements".
4. View results:
   - Ambiguities identified by KEEA.
   - Suggestions generated by AISGA.
   - Shari'ah compliance validated by SCVA.
   - Consistency checked by ISCCA.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature-name"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## 🎯 Expected Outcome & Key Features Demonstrated

*   **Dynamic Standard Selection:** Users can choose which FAS and SS to work with.
*   **AI-Powered Document Understanding:** Extraction of key information and potential ambiguities by KEEA.
*   **AI-Driven Suggestion Generation:** AISGA proposes clarifications or enhancements with:
    *   **Explainability:** Clear reasoning for each suggestion.
    *   **Source Grounding:** Conceptual linkage to FAS and SS context.
*   **AI-Assisted Validation:**
    *   **Shari'ah Compliance (SCVA):** Checks against explicit rules and general Shari'ah principles.
    *   **Inter-Standard Consistency (ISCCA - Conceptual):** Basic checks for terminology.
*   **Multi-Agent Architecture:** Clear segregation of duties demonstrated through different Python modules/classes.
*   **Interactive UI (HERAIA):** A user-friendly interface for experts to interact with the AI outputs.

## 🔮 Future Enhancements

*   Full implementation of all conceptualized agents (ETLRA, PAIAA).
*   More sophisticated Knowledge Graph for Shari'ah rules and inter-standard relationships.
*   Advanced Langchain AgentExecutor for more dynamic agent interactions.
*   User authentication and feedback mechanisms to refine AI models.
*   Version control and history tracking for standard amendments.
*   Integration with persisted ChromaDB or a cloud-based vector database for scalability.
*   Direct PDF rendering or annotation in the UI.

---

## 📜 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **AAOIFI**: For their comprehensive financial standards.
- **Google**: For the Gemini AI model.
- **LangChain**: For the powerful framework.

---

## 📞 Contact

For questions or support, please contact:
- **Email**: kf_saidani@esi
- **GitHub**: [Farid's GitHub](https://github.com/farid)

---

_This README provides an overview of the ASAVE project for the hackathon. For detailed code implementation, please refer to the respective Python files in the repository._
