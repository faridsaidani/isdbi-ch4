import streamlit as st
import os
from dotenv import load_dotenv
import traceback # For more detailed error reporting in the UI

# Load environment variables at the very beginning
load_dotenv()

# Import orchestrator functions after dotenv
INITIALIZATION_POSSIBLE = False
initialize_components = None
run_asave_orchestration_flow = None
PDF_DATA_DIR = "data_pdf" # Default, will be confirmed from orchestrator

try:
    from main_orchestrator import initialize_components, run_asave_orchestration_flow, PDF_DATA_DIR as orchestrator_pdf_dir
    PDF_DATA_DIR = orchestrator_pdf_dir # Use the one defined in orchestrator
    INITIALIZATION_POSSIBLE = True
except ImportError as e:
    st.error(f"Failed to import orchestrator components. Ensure all files are in place: {e}")
except ValueError as e: # Catches API key issues from BaseAgent or DocumentProcessor
    st.error(f"Initialization Value Error: {e}. Check .env file and GOOGLE_API_KEY.")


# --- UI Configuration ---
st.set_page_config(layout="wide", page_title="ASAVE - AAOIFI Standards AI Assistant")
st.title("🕋 ASAVE: AAOIFI Standard Augmentation & Validation Engine (MVP)")
st.caption("Leveraging Gemini & Langchain to enhance AAOIFI Financial Accounting Standards")

# --- State Management ---
if 'components_ready' not in st.session_state:
    st.session_state.components_ready = False
if 'selected_fas_on_init' not in st.session_state: # Store which FAS was used for current init
    st.session_state.selected_fas_on_init = ""
if 'selected_ss_on_init' not in st.session_state:  # Store which SS was used for current init
    st.session_state.selected_ss_on_init = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# --- File Selection Sidebar ---
st.sidebar.header("📚 Standard Selection & Initialization")

if not INITIALIZATION_POSSIBLE:
    st.sidebar.error("Core system files might be missing or API key issue. Cannot proceed.")
else:
    # List available PDF files in the data_pdf directory
    available_pdfs = []
    if os.path.exists(PDF_DATA_DIR):
        available_pdfs = sorted([f for f in os.listdir(PDF_DATA_DIR) if f.lower().endswith('.pdf')])
    else:
        st.sidebar.warning(f"'{PDF_DATA_DIR}' directory not found. Please create it and add PDF standards.")
        os.makedirs(PDF_DATA_DIR, exist_ok=True) # Create if not exists

    if not available_pdfs:
        st.sidebar.info("No PDF files found in 'data_pdf' directory. Please add some AAOIFI standard PDFs.")
        # Fallback: Create dummy files if dir was initially empty, then re-list
        dummy_fas_path = os.path.join(PDF_DATA_DIR, "dummy_fas_example.pdf")
        dummy_ss_path = os.path.join(PDF_DATA_DIR, "dummy_ss_example.pdf")
        DUMMY_PDF_CONTENT_APP = "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj 4 0 obj<</Length 18>>stream\nBT /F1 12 Tf 70 700 Td (Dummy PDF) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\n0000000240 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n310\n%%EOF"
        if not os.path.exists(dummy_fas_path):
            with open(dummy_fas_path, "w") as f: f.write(DUMMY_PDF_CONTENT_APP)
        if not os.path.exists(dummy_ss_path):
            with open(dummy_ss_path, "w") as f: f.write(DUMMY_PDF_CONTENT_APP)
        if not available_pdfs: # if still no pdfs after trying to create dummies
             available_pdfs = sorted([f for f in os.listdir(PDF_DATA_DIR) if f.lower().endswith('.pdf')])


    # Default selections logic (more robust)
    default_fas_selection = None
    default_ss_selection = None
    if available_pdfs:
        # Try to find common default names
        for fname in available_pdfs:
            if "fas" in fname.lower() and ("32" in fname or "ijarah" in fname.lower()):
                default_fas_selection = fname
                break
        if not default_fas_selection:
            default_fas_selection = available_pdfs[0]

        for fname in available_pdfs:
            if "ss" in fname.lower() and ("09" in fname or "ijarah" in fname.lower()):
                default_ss_selection = fname
                break
        if not default_ss_selection:
            default_ss_selection = available_pdfs[0] if len(available_pdfs) > 1 else available_pdfs[0]


    selected_fas_file_ui = st.sidebar.selectbox(
        "Select FAS Document:",
        options=available_pdfs,
        index=available_pdfs.index(default_fas_selection) if default_fas_selection and default_fas_selection in available_pdfs else 0,
        key="fas_selector_ui",
        disabled=not available_pdfs # Disable if no PDFs
    )
    selected_ss_file_ui = st.sidebar.selectbox(
        "Select related Shari'ah Standard (SS) Document:",
        options=available_pdfs,
        index=available_pdfs.index(default_ss_selection) if default_ss_selection and default_ss_selection in available_pdfs else 0,
        key="ss_selector_ui",
        disabled=not available_pdfs # Disable if no PDFs
    )

    if st.sidebar.button("🔄 Initialize/Load Selected Standards", key="init_button_ui", disabled=not (selected_fas_file_ui and selected_ss_file_ui)):
        with st.spinner("Initializing AI components with selected standards... This may take a moment."):
            try:
                # Call initialize_components from main_orchestrator
                init_success = initialize_components(selected_fas_file_ui, selected_ss_file_ui)
                if init_success:
                    st.session_state.components_ready = True
                    st.session_state.selected_fas_on_init = selected_fas_file_ui # Store the files used for this initialization
                    st.session_state.selected_ss_on_init = selected_ss_file_ui
                    st.session_state.analysis_results = None # Clear previous results
                    st.sidebar.success(f"Components Initialized!\n- FAS: {selected_fas_file_ui}\n- SS: {selected_ss_file_ui}")
                else:
                    st.session_state.components_ready = False
                    st.sidebar.error("Some components failed to initialize. Check console logs for details.")
            except Exception as e:
                st.session_state.components_ready = False
                st.sidebar.error(f"Critical Error during Initialization: {e}")
                st.sidebar.text_area("Initialization Traceback", traceback.format_exc(), height=150)

    # Main analysis section - only available if components are ready
    if st.session_state.get('components_ready', False):
        st.sidebar.markdown("---")
        st.sidebar.header("✍️ Analyze Section")
        st.sidebar.info(f"Active FAS: **{st.session_state.selected_fas_on_init}**\n\nActive SS: **{st.session_state.selected_ss_on_init}**")

        default_section_text_app = """23. The cost of the right-of-use asset shall comprise:
a. the “prime cost” of the right-of-use asset (determined in line with the paragraphs 31 or 32);
b. any initial direct costs incurred by the lessee; and
c. dismantling or decommissioning costs."""

        section_to_analyze_input_app = st.sidebar.text_area(
            f"Paste a section of '{st.session_state.selected_fas_on_init}' for analysis:",
            value=default_section_text_app,
            height=200,
            key="section_input_main_ui"
        )

        if st.sidebar.button("🚀 Analyze & Suggest Enhancements", key="analyze_button_main_ui"):
            if not section_to_analyze_input_app.strip():
                st.sidebar.error("Please paste a section to analyze.")
            else:
                with st.spinner("🤖 ASAVE Agents are meticulously working... This might take some time..."):
                    try:
                        # run_asave_orchestration_flow is now called with the FAS name used for initialization
                        st.session_state.analysis_results = run_asave_orchestration_flow(
                            section_to_analyze_input_app.strip(),
                            fas_name_for_display=st.session_state.selected_fas_on_init # Pass the loaded FAS name
                        )
                    except Exception as e:
                        st.error(f"An error occurred during the ASAVE orchestration: {e}")
                        st.text_area("Orchestration Traceback", traceback.format_exc(), height=300)
                        st.session_state.analysis_results = None # Clear results on error
    else:
        st.info("⬅️ Please select your FAS and related SS documents from the sidebar and click 'Initialize/Load Selected Standards' to begin.")
        st.markdown("Ensure your `GOOGLE_API_KEY` is set in the `.env` file and PDF documents are present in the `data_pdf` directory.")


    # --- Display Area for Results (remains the same as previous version) ---
    if st.session_state.get('analysis_results'):
        results = st.session_state.analysis_results
        if results.get("error"):
            st.error(f"Flow Error: {results.get('error')}")
        else:
            st.header("📊 Analysis & Suggestion Dashboard")
            st.markdown(f"#### Analysis for: **{st.session_state.selected_fas_on_init}**")
            st.markdown("---")

            col_orig, col_suggested = st.columns(2)

            with col_orig:
                st.subheader("Original Text Under Review")
                st.markdown(f"```text\n{results.get('original_text', 'N/A')}\n```")
                st.markdown("---")
                st.subheader("🧠 KEEA - Ambiguity/Focus Points")
                st.info(f"**Identified Focus for AISGA:** {results.get('aisga_input_ambiguity_focus', 'N/A')}")
                with st.expander("Raw KEEA Output (for debugging)"):
                    st.text_area("KEEA Raw", results.get('keea_identified_ambiguity_raw', 'N/A'), height=150, key="keea_debug")
                with st.expander("FAS Context Provided to AISGA"):
                    st.text_area("FAS Context", results.get('aisga_input_fas_context', 'N/A'), height=150, key="fas_context_debug")
                with st.expander("SS Context Provided to AISGA"):
                    st.text_area("SS Context", results.get('aisga_input_ss_context', 'N/A'), height=150, key="ss_context_debug")

            with col_suggested:
                st.subheader("💡 AISGA - AI-Driven Suggestion")
                st.markdown("**Suggested Revised Text:**")
                suggested_text_aisga = results.get('suggested_text_by_aisga', 'No suggestion generated.')
                if "Error" in suggested_text_aisga:
                    st.error(suggested_text_aisga)
                else:
                    st.success(f"{suggested_text_aisga}")

                st.markdown("**Reasoning & Shari'ah Alignment by AISGA:**")
                reasoning_aisga = results.get('reasoning_by_aisga', 'No reasoning provided.')
                st.markdown(f"{reasoning_aisga}")
                with st.expander("Raw AISGA Output (for debugging)"):
                    st.text_area("AISGA Raw", results.get('aisga_raw_output', 'N/A'), height=150, key="aisga_debug")

            st.markdown("---")
            st.subheader("⚖️ SCVA - Shari'ah Compliance Validation")
            scva_full_text = results.get('shariah_validation_by_scva', 'SCVA Error: No assessment generated.')
            try:
                assessment_status_line = "Status not parsed"
                detailed_explanation_line = scva_full_text
                if "Shari'ah Compliance Assessment:" in scva_full_text:
                    temp_split = scva_full_text.split("Shari'ah Compliance Assessment:",1)[1]
                    assessment_status_line = temp_split.split("\n",1)[0].strip()
                    if "Detailed Explanation & Justification:" in temp_split:
                        detailed_explanation_line = temp_split.split("Detailed Explanation & Justification:",1)[1].strip()
                    else:
                        detailed_explanation_line = "\n".join(temp_split.split("\n")[1:]).strip()

                if "Compliant" in assessment_status_line: st.success(f"**Assessment Status:** {assessment_status_line}")
                elif "Potential Conflict" in assessment_status_line or "Needs Further Scholarly Review" in assessment_status_line or "Insufficient Information" in assessment_status_line: st.warning(f"**Assessment Status:** {assessment_status_line}")
                else: st.info(f"**Assessment Status:** {assessment_status_line if assessment_status_line else 'Review SCVA output'}")

                with st.expander("Detailed SCVA Explanation & Justification", expanded=True):
                    st.markdown(detailed_explanation_line)
            except Exception as e_parse:
                st.error(f"Error parsing SCVA output for display: {e_parse}")
            with st.expander("Raw SCVA Output (for debugging)"):
                st.text_area("Raw SCVA Full", scva_full_text, height=200, key="scva_raw_main_debug_app")

            st.markdown("---")
            st.subheader("🔗 ISCCA - Inter-Standard Consistency Validation")
            iscca_full_text = results.get('consistency_validation_by_iscca', 'ISCCA Error: No assessment generated.')
            try:
                iscca_status_line = "Status not parsed"
                iscca_explanation_line = iscca_full_text
                if "Consistency Assessment:" in iscca_full_text:
                    temp_split_iscca = iscca_full_text.split("Consistency Assessment:",1)[1]
                    iscca_status_line = temp_split_iscca.split("\n",1)[0].strip()
                    if "Detailed Explanation:" in temp_split_iscca:
                         iscca_explanation_line = temp_split_iscca.split("Detailed Explanation:",1)[1].strip()
                    else:
                        iscca_explanation_line = "\n".join(temp_split_iscca.split("\n")[1:]).strip()

                if "Consistent" in iscca_status_line: st.success(f"**Assessment Status:** {iscca_status_line}")
                else: st.warning(f"**Assessment Status:** {iscca_status_line if iscca_status_line else 'Review ISCCA output'}")
                with st.expander("Detailed ISCCA Explanation", expanded=True):
                    st.markdown(iscca_explanation_line)
            except Exception as e_parse_iscca:
                st.error(f"Error parsing ISCCA output: {e_parse_iscca}")
            with st.expander("Raw ISCCA Output (for debugging)"):
                 st.text_area("Raw ISCCA Full", iscca_full_text, height=150, key="iscca_raw_main_debug_app")

st.sidebar.markdown("---")
st.sidebar.caption("ASAVE MVP - Hackathon Edition")