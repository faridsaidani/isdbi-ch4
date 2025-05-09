from .base_agent import BaseAgent
import json
import re # For cleaning up rule_id
import os
# from main_orchestrator import initialize_srma_agent_if_needed
from utils.document_processor import PDF_DATA_DIR

class ShariahRuleMinerAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            temperature=0.15, # Slightly higher for a bit more nuanced rule interpretation
            system_message="You are an expert AI assistant specializing in meticulously analyzing AAOIFI Shari'ah Standards. Your primary task is to accurately identify explicit Shari'ah rules, prohibitions, and mandatory conditions, and then format them into a structured JSON output. Focus on actionable directives.",
            **kwargs
        )

    def _extract_potential_rules_from_chunk(self, text_chunk: str, standard_name: str):
        prompt_str = """
        From the following text chunk of the AAOIFI Shari'ah Standard '{standard_name}', identify and list ALL sentences or clauses that clearly state an explicit Shari'ah rule, prohibition, permission, or mandatory condition.
        - Focus on actionable directives (e.g., "It is permissible...", "It is not permitted...", "It is a requirement that...", "must be...", "shall not...").
        - Exclude general descriptions, historical context, explanations of wisdom, or examples unless they directly illustrate the scope of an explicit rule.
        - Each identified rule should be a direct quote or a very concise paraphrase if a direct quote is too context-dependent to stand alone as a rule.
        - If a single sentence contains multiple distinct rules, list them separately if possible.

        Text Chunk from {standard_name}:
        ---
        {text_chunk}
        ---

        Identified Explicit Rules (list each on a new line, prefixed with '- '. If no explicit rules found in this chunk, state "No explicit rules found in this chunk"):
        -
        """
        chain = self.create_chain(prompt_str, ["text_chunk", "standard_name"])
        response = self.invoke_chain(chain, text_chunk=text_chunk, standard_name=standard_name)

        raw_rules_text = response.get('text', "")
        potential_rules = []
        if "No explicit rules found" not in raw_rules_text.lower(): # case-insensitive check
            lines = raw_rules_text.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:].strip()
                if line and len(line) > 15: # Filter for slightly more meaningful sentences
                    potential_rules.append(line)
        return potential_rules

    def _format_rule_to_json_structure(self, rule_text: str, standard_name: str, original_chunk_ref: str):
        # Generate a more descriptive short name for standard_ref and rule_id
        ss_match = re.search(r'Standard No\. \((\d+)\)(.*)', standard_name, re.IGNORECASE)
        standard_number_str = ss_match.group(1) if ss_match else "SS_Unknown"
        standard_topic_match = re.search(r'\(([^)]+)\)', standard_name) # Try to get topic from brackets
        standard_topic_str = standard_topic_match.group(1).replace(" ", "_") if standard_topic_match else standard_name.split(" ")[-1] # Fallback to last word
        standard_name_short = f"SS{standard_number_str}_{standard_topic_str[:15]}".replace("(", "").replace(")", "") # Max 15 chars for topic

        # Attempt to create a rule_id from the rule text itself
        first_few_words = "_".join(re.sub(r'[^a-zA-Z0-9_ ]', '', rule_text).split()[:4]).upper()
        generated_rule_id = f"{standard_name_short}_{first_few_words}" if first_few_words else f"{standard_name_short}_RULE"

        prompt_str = """
        Given the following explicit Shari'ah rule extracted from the AAOIFI standard '{standard_name}'
        (Original context hint: part of a chunk starting with: '{original_chunk_ref_snippet}...')

        Extracted Rule Text:
        "{rule_text}"

        Your Task: Format this rule into a JSON object with the following keys:
        1.  "rule_id": A concise, unique, and descriptive ID based on the standard and rule content. Use the format: '{generated_rule_id_prefix}_[CONCISE_KEY_ASPECT_OF_RULE_IN_UPPERCASE]'.
        2.  "standard_ref": The name of the standard, e.g., "SS {standard_number}: {standard_topic_name}". Add a placeholder like "[Clause X.Y]" if the exact clause is not evident from the text.
        3.  "principle_keywords": A JSON list of 3-5 relevant lowercase keywords that capture the essence of this rule for searchability (e.g., ["ijarah", "permissible use", "shari'ah compliance"]).
        4.  "description": A clear, concise, and accurate restatement or summary of the rule text. This should be the primary human-readable rule statement, capturing its full meaning.
        5.  "validation_query_template": Generate a specific question template to validate if a proposed accounting clause conflicts with THIS Shari'ah rule. The template MUST include '{{clause_text}}' and '{{rule_description}}' as placeholders. Example: "Does the proposed accounting treatment in '{{clause_text}}' align with the Shari'ah rule: '{{rule_description}}'? Explain discrepancies."

        Ensure the "description" accurately and fully reflects the "Extracted Rule Text".
        Provide ONLY the single JSON object as your output, with no other text before or after.

        JSON Output:
        """
        chain = self.create_chain(prompt_str, ["rule_text", "standard_name", "original_chunk_ref_snippet", "generated_rule_id_prefix", "standard_number", "standard_topic_name"])
        response = self.invoke_chain(chain,
                                     rule_text=rule_text,
                                     standard_name=standard_name,
                                     original_chunk_ref_snippet=original_chunk_ref[:80],
                                     generated_rule_id_prefix=generated_rule_id,
                                     standard_number=standard_number_str,
                                     standard_topic_name=standard_topic_str
                                    )

        json_text_output = response.get('text', "{}")
        try:
            if json_text_output.strip().startswith("```json"):
                json_text_output = json_text_output.split("```json",1)[1].rsplit("```",1).strip()
            elif json_text_output.strip().startswith("```"): # Simpler markdown removal
                json_text_output = json_text_output.strip()[3:-3].strip()

            formatted_rule = json.loads(json_text_output)
            # Ensure all keys are present with default values if missing
            keys_to_ensure = {"rule_id": f"{generated_rule_id}_TODO",
                              "standard_ref": f"{standard_name} [Clause TODO]",
                              "principle_keywords": [],
                              "description": f"TODO: {rule_text}",
                              "validation_query_template": "Does the proposed accounting treatment in '{{clause_text}}' align with the Shari'ah rule: '{{rule_description}}'? Explain discrepancies."}
            for key, default_val in keys_to_ensure.items():
                if key not in formatted_rule or not formatted_rule[key]: # Also check for empty values for some keys
                    if key == "principle_keywords" and isinstance(formatted_rule.get(key), list): # Allow empty list for keywords
                        pass
                    else:
                        formatted_rule[key] = default_val
            return formatted_rule
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON from LLM for rule: '{rule_text[:50]}...'\nLLM Output: {json_text_output}\nError: {e}")
            return None

    def mine_rules_from_document_list(self, ss_document_filenames: list, base_output_dir: str):
        """
        Processes a list of Shari'ah Standard PDF documents to extract and format rules.
        Saves each document's rules into its own JSON file and a combined JSON file.
        """
        # if not initialize_srma_agent_if_needed(): # Ensure this agent is initialized
        #      print("ERROR: ShariahRuleMinerAgent could not be initialized for mining.")
        #      return False


        all_mined_rules_combined = []
        os.makedirs(base_output_dir, exist_ok=True)

        for ss_filename in ss_document_filenames:
            ss_document_path = os.path.join(PDF_DATA_DIR, ss_filename)
            print(f"\n--- Starting Shari'ah Rule Mining for: {ss_filename} ---")

            ss_texts_to_mine = doc_processor_global.load_and_process_pdf(ss_document_path)
            if not ss_texts_to_mine:
                print(f"Warning: Could not process {ss_filename} for rule mining. Skipping.")
                continue

            # Use a descriptive name for the standard in prompts
            standard_name_for_prompt = f"AAOIFI Shari'ah Standard ({os.path.splitext(ss_filename)[0]})"
            extracted_rules_for_doc = self.mine_rules_from_document( # Call the renamed internal method
                document_chunks=ss_texts_to_mine,
                standard_name=standard_name_for_prompt
            )

            if extracted_rules_for_doc:
                individual_output_path = os.path.join(base_output_dir, f"generated_{os.path.splitext(ss_filename)[0]}_rules.json")
                try:
                    with open(individual_output_path, 'w', encoding='utf-8') as f:
                        json.dump(extracted_rules_for_doc, f, indent=2, ensure_ascii=False)
                    print(f"  ✅ Successfully mined {len(extracted_rules_for_doc)} rules from {ss_filename} and saved to: {individual_output_path}")
                    all_mined_rules_combined.extend(extracted_rules_for_doc)
                except Exception as e:
                    print(f"  ERROR: Could not save mined rules for {ss_filename} to {individual_output_path}: {e}")
            else:
                print(f"  No rules were extracted from {ss_filename}.")

        if all_mined_rules_combined:
            combined_output_path = os.path.join(base_output_dir, "generated_ALL_shariah_rules_combined.json")
            try:
                with open(combined_output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_mined_rules_combined, f, indent=2, ensure_ascii=False)
                print(f"\n🌟 Successfully mined a total of {len(all_mined_rules_combined)} rules from all selected SS files and saved combined output to: {combined_output_path}")
                print("⚠️ IMPORTANT: Please MANUALLY REVIEW and CURATE ALL generated JSON files before use.")
                return True
            except Exception as e:
                print(f"ERROR: Could not save combined mined rules to {combined_output_path}: {e}")
                return False
        else:
            print("\nNo rules were extracted from any of the selected SS documents.")
            return False

    # Renamed the original single-doc method to avoid confusion
    def mine_rules_from_document(self, document_chunks: list, standard_name: str):
        all_formatted_rules = []
        # print(f"Mining rules from {standard_name} ({len(document_chunks)} chunks)...") # Verbose
        for i, chunk in enumerate(document_chunks):
            # print(f"  Processing chunk {i+1}/{len(document_chunks)} for {standard_name}...") # Verbose
            potential_rules_texts = self._extract_potential_rules_from_chunk(chunk, standard_name)
            if potential_rules_texts:
                # print(f"    Found {len(potential_rules_texts)} potential rule(s) in chunk {i+1}.") # Verbose
                for rule_text in potential_rules_texts:
                    # print(f"      Formatting rule: {rule_text[:70]}...") # Verbose
                    formatted_rule = self._format_rule_to_json_structure(rule_text, standard_name, chunk)
                    if formatted_rule:
                        all_formatted_rules.append(formatted_rule)
        return all_formatted_rules