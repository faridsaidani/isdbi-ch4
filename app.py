
import streamlit as st
import os
from dotenv import load_dotenv
import traceback # For better error display

# --- 1. SET PAGE CONFIG FIRST ---
st.set_page_config(layout="wide", page_title="ASAVE - AAOIFI AI Assistant")

# --- 2. THEN LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- 3. THEN TRY TO IMPORT YOUR MODULES ---
INITIALIZATION_POSSIBLE = False
initialize_components_fn = None # Use a different name to avoid conflict if function is not found
run_asave_orchestration_flow_fn = None
run_srma_on_selected_ss_files_fn = None
PDF_DATA_DIR_APP = "data_pdf" # Default

try:
    from main_orchestrator import (
        initialize_components, # This will be the function from main_orchestrator
        run_asave_orchestration_flow,
        run_srma_on_selected_ss_files,
        PDF_DATA_DIR as orchestrator_pdf_dir_app # Get PDF_DATA_DIR from orchestrator
    )
    initialize_components_fn = initialize_components
    run_asave_orchestration_flow_fn = run_asave_orchestration_flow
    run_srma_on_selected_ss_files_fn = run_srma_on_selected_ss_files
    PDF_DATA_DIR_APP = orchestrator_pdf_dir_app
    INITIALIZATION_POSSIBLE = True
except ImportError as e:
    st.error(f"CRITICAL ERROR: Failed to import core ASAVE components. Ensure 'main_orchestrator.py' and all agent/utility files are in the correct project structure and have no syntax errors. Details: {e}")
    print("Traceback for ImportError in app.py (at top level):")
    traceback.print_exc()
except ValueError as e:
    st.error(f"CRITICAL CONFIGURATION ERROR: {e}. This often relates to the GOOGLE_API_KEY. Please ensure it's correctly set in your .env file and accessible.")
    print("Traceback for ValueError in app.py (likely API key or Gemini model init):")
    traceback.print_exc()
except Exception as e:
    st.error(f"An unexpected error occurred during initial imports: {e}")
    print("Traceback for unexpected error in app.py imports:")
    traceback.print_exc()


# --- UI Configuration ---
st.title("🕋 ASAVE: AAOIFI Standard Augmentation & Validation Engine (MVP)")
st.caption("Leveraging Google Gemini & Langchain to enhance AAOIFI Standards")

# --- State Management ---
if 'components_ready' not in st.session_state: st.session_state.components_ready = False
if 'selected_fas_on_init' not in st.session_state: st.session_state.selected_fas_on_init = ""
if 'selected_ss_on_init' not in st.session_state: st.session_state.selected_ss_on_init = ""
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None

# --- Sidebar ---
st.sidebar.header("📚 Standard Selection & Main Analysis")

if not INITIALIZATION_POSSIBLE:
    st.sidebar.error("ASAVE system cannot start due to import or configuration errors. Please check the main page error messages and console output.")
else:
    available_pdfs = []
    if os.path.exists(PDF_DATA_DIR_APP): # Use the variable set from orchestrator or default
        available_pdfs = sorted([f for f in os.listdir(PDF_DATA_DIR_APP) if f.lower().endswith('.pdf')])
    # ... (rest of available_pdfs and default selection logic from your last app.py, using PDF_DATA_DIR_APP) ...
    else:
        st.sidebar.warning(f"'{PDF_DATA_DIR_APP}' directory not found. Please create it and add PDF standards.")
        try:
            os.makedirs(PDF_DATA_DIR_APP, exist_ok=True)
        except Exception as e_dir:
            st.sidebar.error(f"Could not create data_pdf directory: {e_dir}")


    if not available_pdfs:
        st.sidebar.info("No PDF files found in 'data_pdf' directory. Please add some AAOIFI standard PDFs for the tool to function.")
        # Fallback: Create dummy files if dir was initially empty, then re-list for UI
        dummy_fas_path_app_ui = os.path.join(PDF_DATA_DIR_APP, "dummy_fas_example.pdf")
        dummy_ss_path_app_ui = os.path.join(PDF_DATA_DIR_APP, "dummy_ss_example.pdf")
        DUMMY_PDF_CONTENT_APP_DETAILED_UI = "%PDF-1.4\n%âãÏÓ\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n4 0 obj<</Length 30>>stream\nBT /F1 12 Tf 70 700 Td (Dummy PDF Content Page) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000016 00000 n \n0000000065 00000 n \n0000000129 00000 n \n0000000231 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n308\n%%EOF"
        if not os.path.exists(dummy_fas_path_app_ui):
            with open(dummy_fas_path_app_ui, "w", encoding="utf-8") as f: f.write(DUMMY_PDF_CONTENT_APP_DETAILED_UI)
        if not os.path.exists(dummy_ss_path_app_ui):
            with open(dummy_ss_path_app_ui, "w", encoding="utf-8") as f: f.write(DUMMY_PDF_CONTENT_APP_DETAILED_UI)
        if not available_pdfs:
             available_pdfs = sorted([f for f in os.listdir(PDF_DATA_DIR_APP) if f.lower().endswith('.pdf')])


    default_fas_selection_ui = ""
    default_ss_selection_ui = ""
    if available_pdfs:
        for fname in available_pdfs:
            if "fas" in fname.lower() and ("32" in fname or "ijarah" in fname.lower()):
                default_fas_selection_ui = fname; break
        if not default_fas_selection_ui: default_fas_selection_ui = available_pdfs[0]

        for fname in available_pdfs:
            if "ss" in fname.lower() and (("09" in fname or "9" in fname) and "ijarah" in fname.lower()):
                default_ss_selection_ui = fname; break
        if not default_ss_selection_ui: default_ss_selection_ui = available_pdfs[-1] if len(available_pdfs) > 1 else available_pdfs[0]

    selected_fas_file_ui_app = st.sidebar.selectbox(
        "Select FAS Document (for main analysis):", options=available_pdfs,
        index=available_pdfs.index(default_fas_selection_ui) if default_fas_selection_ui and default_fas_selection_ui in available_pdfs else 0,
        key="fas_selector_app", disabled=not available_pdfs
    )
    selected_ss_file_ui_main_app = st.sidebar.selectbox(
        "Select related Shari'ah Standard (SS) (for main analysis):", options=available_pdfs,
        index=available_pdfs.index(default_ss_selection_ui) if default_ss_selection_ui and default_ss_selection_ui in available_pdfs else 0,
        key="ss_selector_app", disabled=not available_pdfs
    )

    if st.sidebar.button("🔄 Initialize/Load for Main Analysis", key="init_button_app", disabled=not (selected_fas_file_ui_app and selected_ss_file_ui_main_app and initialize_components_fn)):
        with st.spinner("Initializing components for main analysis..."):
            try:
                init_success = initialize_components_fn(selected_fas_file_ui_app, selected_ss_file_ui_main_app)
                if init_success:
                    st.session_state.components_ready = True
                    st.session_state.selected_fas_on_init = selected_fas_file_ui_app
                    st.session_state.selected_ss_on_init = selected_ss_file_ui_main_app
                    st.session_state.analysis_results = None
                    st.sidebar.success(f"Initialized for Analysis:\n- FAS: {selected_fas_file_ui_app}\n- SS: {selected_ss_file_ui_main_app}")
                else:
                    st.session_state.components_ready = False
                    st.sidebar.error("Main component initialization failed. Check console.")
            except Exception as e:
                st.session_state.components_ready = False
                st.sidebar.error(f"Critical Error during Main Initialization: {e}")
                st.sidebar.text_area("Init Traceback", traceback.format_exc(), height=150)

    if st.session_state.get('components_ready', False):
        st.sidebar.markdown("---")
        st.sidebar.info(f"Active FAS: **{st.session_state.selected_fas_on_init}**\nActive SS: **{st.session_state.selected_ss_on_init}**")
        default_section_text_app_main = """23. The cost of the right-of-use asset shall comprise:\na. the “prime cost” of the right-of-use asset (determined in line with the paragraphs 31 or 32);"""
        section_to_analyze_input_app_main = st.sidebar.text_area(
            f"Paste a section of '{st.session_state.selected_fas_on_init}' for analysis:",
            value=default_section_text_app_main, height=150, key="section_input_app"
        )
        if st.sidebar.button("🚀 Analyze & Suggest Enhancements", key="analyze_button_app", disabled=not run_asave_orchestration_flow_fn):
            if not section_to_analyze_input_app_main.strip():
                st.sidebar.error("Please paste a section to analyze.")
            else:
                with st.spinner("🤖 ASAVE Agents are meticulously working..."):
                    try:
                        st.session_state.analysis_results = run_asave_orchestration_flow_fn(
                            section_to_analyze_input_app_main.strip(),
                            fas_name_for_display=st.session_state.selected_fas_on_init
                        )
                    except Exception as e:
                        st.error(f"Error during orchestration: {e}")
                        st.text_area("Orchestration Traceback", traceback.format_exc(), height=300)
                        st.session_state.analysis_results = None
    elif INITIALIZATION_POSSIBLE:
        st.info("⬅️ Please select FAS and SS for main analysis and click 'Initialize/Load'.")

    # --- SRMA Section in Sidebar ---
    st.sidebar.markdown("---")
    st.sidebar.header("⛏️ Shari'ah Rule Miner (SRMA)")
    st.sidebar.caption("Extract explicit rules. Output in 'knowledge_bases/srma_generated_outputs'.")

    if not INITIALIZATION_POSSIBLE:
        st.sidebar.error("SRMA disabled due to core system errors.")
    elif not available_pdfs:
        st.sidebar.info("No PDF files in 'data_pdf' for rule mining.")
    else:
        selected_ss_files_for_mining_ui_app = st.sidebar.multiselect(
            "Select Shari'ah Standard (SS) PDFs for Rule Mining:", options=available_pdfs,
            default=[default_ss_selection_ui] if default_ss_selection_ui and default_ss_selection_ui in available_pdfs else [],
            key="ss_multiselect_srma_app"
        )
        srma_output_dir_ui_app = "knowledge_bases/srma_generated_outputs"

        if st.sidebar.button("💎 Mine Explicit Shari'ah Rules", key="srma_button_app",
                             disabled=not (selected_ss_files_for_mining_ui_app and run_srma_on_selected_ss_files_fn and st.session_state.get('components_ready'))):
            # Require main components (especially doc_processor) to be ready
            if not st.session_state.get('components_ready'):
                st.sidebar.warning("Please Initialize main analysis components first (SRMA uses shared resources).")
            else:
                with st.spinner(f"SRMA processing {len(selected_ss_files_for_mining_ui_app)} file(s)..."):
                    try:
                        srma_success = run_srma_on_selected_ss_files_fn(
                            selected_ss_filenames=selected_ss_files_for_mining_ui_app,
                            output_directory=srma_output_dir_ui_app
                        )
                        if srma_success:
                            st.sidebar.success(f"SRMA finished! Check '{srma_output_dir_ui_app}'.")
                            st.sidebar.warning("Manually review generated JSON files.")
                        else:
                            st.sidebar.error("SRMA failed or no rules extracted. Check console.")
                    except Exception as e:
                        st.sidebar.error(f"Error during SRMA: {e}")
                        st.sidebar.text_area("SRMA Traceback", traceback.format_exc(), height=150)

    # --- Display Area for Main Analysis Results ---
    # (This section remains the same as your previous complete app.py version,
    #  just ensure it uses st.session_state.analysis_results and keys are unique)
    if st.session_state.get('analysis_results'):
        results = st.session_state.analysis_results
        if results.get("error"):
            st.error(f"Main Analysis Flow Error: {results.get('error')}")
        else:
            # ... (Your full results display logic from before, ensure keys are unique if needed) ...
            st.header("📊 Analysis & Suggestion Dashboard")
            st.markdown(f"#### Analysis for: **{st.session_state.get('selected_fas_on_init', 'N/A')}**")
            # (The rest of your detailed column display)
            # ... (Ensure you use unique keys for any text_area widgets in the expanders, e.g., key="keea_debug_ui_app")

st.sidebar.markdown("---")
st.sidebar.caption("ASAVE MVP © [Your Team Name Here]")