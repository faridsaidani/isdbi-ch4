import os
import json
from dotenv import load_dotenv

from utils.document_processor import DocumentProcessor
from agents.extraction_agent import ExtractionAgent
from agents.suggestion_agent import SuggestionAgent
from agents.validation_agent import ValidationAgent

# load_dotenv()

# --- Configuration ---
PDF_DATA_DIR = "data_pdf" # Base directory for all PDFs
EXPLICIT_SHARIAH_RULES_PATH = os.path.join("knowledge_bases", "shariah_rules_explicit.json")

# Global Variables for initialized components
# These will now be populated based on dynamic user selection
doc_processor_global = None
fas_vector_store_global = None
ss_vector_store_global = None
extraction_agent_global = None
suggestion_agent_global = None
validation_agent_global = None
current_fas_filename_global = None # To track which FAS is loaded
current_ss_filename_global = None  # To track which SS is loaded


def initialize_components(fas_filename: str, ss_filename: str, api_key: str = None):
    """
    Initializes components based on dynamically selected FAS and SS filenames.
    Returns True if successful, False otherwise.
    """
    global doc_processor_global, fas_vector_store_global, ss_vector_store_global
    global extraction_agent_global, suggestion_agent_global, validation_agent_global
    global current_fas_filename_global, current_ss_filename_global

    print(f"Attempting to initialize components for FAS: {fas_filename}, SS: {ss_filename}")

    # Initialize DocumentProcessor if not already done
    if doc_processor_global is None:
        print("Initializing DocumentProcessor for the first time...")
        doc_processor_global = DocumentProcessor()

    # --- Process and Create/Load Vector Stores for selected FAS ---
    fas_document_path = os.path.join(PDF_DATA_DIR, fas_filename)
    fas_collection_name = f"{os.path.splitext(fas_filename)[0]}_collection" # e.g., fas_32_ijarah_collection

    # Only re-initialize if the FAS file has changed
    if current_fas_filename_global != fas_filename or fas_vector_store_global is None:
        print(f"Processing NEW or UNLOADED FAS Document: {fas_document_path}")
        fas_texts = doc_processor_global.load_and_process_pdf(fas_document_path)
        if fas_texts:
            fas_vector_store_global = doc_processor_global.create_vector_store(
                texts=fas_texts,
                collection_name=fas_collection_name
                # persist_directory=os.path.join("chroma_db_dynamic", fas_collection_name) # Optional persistence
            )
            if fas_vector_store_global:
                current_fas_filename_global = fas_filename
                print(f"FAS Vector Store for '{fas_collection_name}' created/updated.")
            else:
                print(f"ERROR: FAS Vector Store for '{fas_collection_name}' could not be created.")
                return False # Critical error
        else:
            print(f"ERROR: No texts extracted from FAS document: {fas_document_path}")
            return False # Critical error
    else:
        print(f"FAS document '{fas_filename}' is already processed and loaded.")


    # --- Process and Create/Load Vector Stores for selected SS ---
    ss_document_path = os.path.join(PDF_DATA_DIR, ss_filename)
    ss_collection_name = f"{os.path.splitext(ss_filename)[0]}_collection"

    if current_ss_filename_global != ss_filename or ss_vector_store_global is None:
        print(f"Processing NEW or UNLOADED SS Document: {ss_document_path}")
        ss_texts = doc_processor_global.load_and_process_pdf(ss_document_path)
        if ss_texts:
            ss_vector_store_global = doc_processor_global.create_vector_store(
                texts=ss_texts,
                collection_name=ss_collection_name
                # persist_directory=os.path.join("chroma_db_dynamic", ss_collection_name) # Optional persistence
            )
            if ss_vector_store_global:
                current_ss_filename_global = ss_filename
                print(f"SS Vector Store for '{ss_collection_name}' created/updated.")
            else:
                print(f"ERROR: SS Vector Store for '{ss_collection_name}' could not be created.")
                # Decide if this is critical enough to return False, or if SCVA can somewhat function without SS context
                # For now, let's allow it but SCVA will be limited.
        else:
            print(f"Warning: No texts extracted from SS document: {ss_document_path}. SCVA will have limited context.")
    else:
        print(f"SS document '{ss_filename}' is already processed and loaded.")


    # --- Initialize/Re-initialize Agents with potentially new vector stores ---
    # Re-initialize agents even if only one store changes, as they might depend on both
    print("Re-initializing Agents with current vector stores...")
    if fas_vector_store_global:
        extraction_agent_global = ExtractionAgent(vector_store=fas_vector_store_global, api_key=api_key)
    else:
        extraction_agent_global = None # Cannot function without FAS store
        print("ERROR: ExtractionAgent cannot be initialized without FAS vector store.")
        return False

    suggestion_agent_global = SuggestionAgent(api_key=api_key) # Context passed dynamically

    if ss_vector_store_global or fas_vector_store_global: # ISCCA needs FAS, SCVA ideally needs SS
        validation_agent_global = ValidationAgent(
            explicit_shariah_rules_path=EXPLICIT_SHARIAH_RULES_PATH,
            ss_vector_store=ss_vector_store_global, # Can be None if SS file failed
            fas_vector_store=fas_vector_store_global, # For ISCCA
            api_key=api_key # Pass API key for LLM initialization
        )
    else:
        validation_agent_global = None
        print("Warning: ValidationAgent not fully initialized as one or both vector stores are missing.")


    print("Dynamic component initialization attempt finished.")
    # Check if essential agents are initialized
    return (extraction_agent_global is not None and
            suggestion_agent_global is not None and
            validation_agent_global is not None) # Validation agent might be partially functional

def run_asave_orchestration_flow(section_text_to_analyze: str, fas_name_for_display: str):
    """x
    Orchestrates the flow of operations. Assumes components are already initialized
    by initialize_components() based on user's dynamic selection.
    """
    global extraction_agent_global, suggestion_agent_global, validation_agent_global
    global fas_vector_store_global, ss_vector_store_global

    if not all([extraction_agent_global, suggestion_agent_global, validation_agent_global, fas_vector_store_global]):
        print("ERROR in orchestration: Core components not initialized. Please load standards first.")
        return {"error": "Core components not initialized. Please select and load standards via the UI."}

    print(f"\n🚀 --- ASAVE Orchestration Flow Started for section of {fas_name_for_display} ---")
    # ... (The rest of this function's logic remains the same as in the previous complete example)
    # ... it will use the globally set vector stores and agents.

    print(f"Original Section Text:\n'''\n{section_text_to_analyze}\n'''\n")
    results = {"original_text": section_text_to_analyze}

    # 1. KEEA
    print("🔍 KEEA: Finding Ambiguities...")
    keea_ambiguity_output = extraction_agent_global.find_ambiguities(section_text_to_analyze)
    results["keea_identified_ambiguity_raw"] = keea_ambiguity_output.get('text', "KEEA Error: Could not identify ambiguities.")
    print(f"KEEA Ambiguity Output (Raw):\n{results['keea_identified_ambiguity_raw']}\n")
    # (Heuristic for ambiguity focus remains the same)
    if "No significant ambiguities found" in results["keea_identified_ambiguity_raw"] or \
       "Error" in results["keea_identified_ambiguity_raw"]:
        ambiguity_for_aisga = "General review for clarity, Shari'ah alignment, and potential enhancement of the provided text."
    else:
        first_ambiguity_line = results["keea_identified_ambiguity_raw"].split("1.", 1)[-1].split("2.", 1)[0].strip()
        ambiguity_for_aisga = first_ambiguity_line if first_ambiguity_line else results["keea_identified_ambiguity_raw"]
    results["aisga_input_ambiguity_focus"] = ambiguity_for_aisga
    print(f"Focus for AISGA (derived from KEEA): {ambiguity_for_aisga}")

    # Retrieve context for AISGA
    print("📚 Retrieving context for AISGA...")
    fas_context_docs = fas_vector_store_global.similarity_search(section_text_to_analyze, k=2)
    fas_context_for_aisga = "\n---\n".join([f"FAS Excerpt ({current_fas_filename_global}):\n{doc.page_content}" for doc in fas_context_docs])
    results["aisga_input_fas_context"] = fas_context_for_aisga

    ss_context_for_aisga = "No specific SS context retrieved or SS not loaded."
    if ss_vector_store_global:
        shariah_query_for_aisga = f"Shari'ah principles (from AAOIFI SS {current_ss_filename_global}) relevant to: {section_text_to_analyze[:150]}"
        ss_context_docs = ss_vector_store_global.similarity_search(shariah_query_for_aisga, k=2)
        ss_context_for_aisga = "\n---\n".join([f"Shari'ah Standard Excerpt ({current_ss_filename_global}):\n{doc.page_content}" for doc in ss_context_docs])
    results["aisga_input_ss_context"] = ss_context_for_aisga
    print("Context retrieval for AISGA complete.")

    # 2. AISGA
    print("\n💡 AISGA: Generating Suggestion...")
    # (AISGA call and parsing logic remains the same)
    aisga_response = suggestion_agent_global.generate_clarification(
        original_text=section_text_to_analyze,
        identified_ambiguity=ambiguity_for_aisga,
        fas_context=fas_context_for_aisga,
        ss_context=ss_context_for_aisga
    )
    # (Parsing logic for aisga_full_text, suggested_text, suggestion_reasoning as before)
    aisga_full_text = aisga_response.get('text', "AISGA Error: No suggestion generated.")
    results["aisga_raw_output"] = aisga_full_text
    suggested_text = "AISGA Error: Could not parse suggested text."
    suggestion_reasoning = "AISGA Error: Could not parse reasoning."
    if "Revised Paragraph:" in aisga_full_text and "Reasoning & Shari'ah Alignment:" in aisga_full_text:
        temp_split = aisga_full_text.split("Revised Paragraph:", 1)[-1]
        suggested_text = temp_split.split("Reasoning & Shari'ah Alignment:", 1)[0].strip()
        suggestion_reasoning = temp_split.split("Reasoning & Shari'ah Alignment:", 1)[-1].strip()
    elif "Revised Paragraph:" in aisga_full_text:
        suggested_text = aisga_full_text.split("Revised Paragraph:", 1)[-1].strip()
    results["suggested_text_by_aisga"] = suggested_text
    results["reasoning_by_aisga"] = suggestion_reasoning
    print(f"AISGA Suggested Text:\n{suggested_text}")
    print(f"AISGA Reasoning:\n{suggestion_reasoning}\n")

    if "Error" in suggested_text:
        print("Halting flow due to AISGA error.")
        results["error"] = "AISGA failed to generate a parsable suggestion."
        return results

    # 3. SCVA
    print("🛡️ SCVA: Validating Shari'ah Compliance...")
    scva_response = validation_agent_global.validate_shariah_compliance(
        proposed_text=suggested_text,
        specific_aspect_under_review=ambiguity_for_aisga
    )
    results["shariah_validation_by_scva"] = scva_response.get('text', "SCVA Error: No Shari'ah assessment generated.")
    print(f"SCVA Shari'ah Assessment:\n{results['shariah_validation_by_scva']}\n")

    # 4. ISCCA
    print("🔗 ISCCA: Validating Inter-Standard Consistency...")
    iscca_response = validation_agent_global.validate_inter_standard_consistency(
        proposed_text=suggested_text,
        fas_name=fas_name_for_display # Use the display name
    )
    results["consistency_validation_by_iscca"] = iscca_response.get('text', "ISCCA Error: No consistency assessment generated.")
    print(f"ISCCA Consistency Assessment:\n{results['consistency_validation_by_iscca']}\n")

    print("🏁 --- ASAVE Orchestration Flow Completed ---")
    return results


# Test block for main_orchestrator (can be commented out when running with Streamlit)
if __name__ == '__main__':
    # Dummy PDF creation (as in previous utils/document_processor.py test)
    # This is just to ensure the script can run if the files are missing on first go.
    # You MUST have actual PDFs in data_pdf/ for meaningful operation.
    os.makedirs(PDF_DATA_DIR, exist_ok=True)
    DUMMY_PDF_CONTENT_MAIN = "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj 4 0 obj<</Length 18>>stream\nBT /F1 12 Tf 70 700 Td (Main Orchestrator Test PDF FAS 32 Ijarah.) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\n0000000240 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n310\n%%EOF"
    if not os.path.exists(FAS_DOCUMENT_PATH):
        with open(FAS_DOCUMENT_PATH, "w") as f: f.write(DUMMY_PDF_CONTENT_MAIN.replace("FAS 32 Ijarah", "FAS 32 Ijarah Content"))
        print(f"Created dummy PDF for testing: {FAS_DOCUMENT_PATH}")
    if not os.path.exists(SS_DOCUMENT_PATH):
        with open(SS_DOCUMENT_PATH, "w") as f: f.write(DUMMY_PDF_CONTENT_MAIN.replace("FAS 32 Ijarah", "SS 09 Ijarah Content"))
        print(f"Created dummy PDF for testing: {SS_DOCUMENT_PATH}")

    # Initialize with default/example files for direct run
    init_success = initialize_components(fas_filename=FAS_DOC_FILENAME, ss_filename=SS_DOC_FILENAME)

    if init_success:
        example_section = """
        23. The cost of the right-of-use asset shall comprise:
        a. the “prime cost” of the right-of-use asset (determined in line with the paragraphs 31 or 32);
        b. any initial direct costs incurred by the lessee; and
        c. dismantling or decommissioning costs.
        """
        flow_results = run_asave_orchestration_flow(example_section.strip(), FAS_DOC_FILENAME)
        print("\n--- ### FINAL ORCHESTRATION RESULTS (Direct Run) ### ---")
        if flow_results and not flow_results.get("error"):
            for key, value in flow_results.items():
                print(f"\n\n➡️ {key.replace('_', ' ').title()}:\n{'-'*30}\n{value}")
        elif flow_results:
            print(f"Error in flow: {flow_results.get('error')}")
        else:
            print("Flow did not produce results directly.")
    else:
        print("Could not run direct orchestration test because components failed to initialize.")