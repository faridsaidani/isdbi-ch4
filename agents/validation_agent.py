from .base_agent import BaseAgent
import json
from langchain.chains import RetrievalQA # For SS context retrieval
import re # Import re for finding placeholders

class ValidationAgent(BaseAgent):
    def __init__(self, explicit_shariah_rules_path=None, ss_vector_store=None, fas_vector_store=None, **kwargs):
        super().__init__(temperature=0.1, system_message="You are a meticulous AAOIFI standards validation expert. Your role is to critically assess proposals for Shari'ah compliance and inter-standard consistency based on provided rules and contexts.", **kwargs)
        self.explicit_rules = []
        if explicit_shariah_rules_path:
            try:
                with open(explicit_shariah_rules_path, 'r', encoding='utf-8') as f:
                    self.explicit_rules = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load explicit Shari'ah rules from {explicit_shariah_rules_path}: {e}")

        self.ss_retriever = ss_vector_store.as_retriever(search_kwargs={"k": 3}) if ss_vector_store else None
        self.fas_retriever = fas_vector_store.as_retriever(search_kwargs={"k": 3}) if fas_vector_store else None # For ISCCA

    def _get_placeholders(self, template_string):
        """Helper to find placeholders like {key} in a string."""
        return re.findall(r'\{(\w+)\}', template_string)

    def validate_shariah_compliance(self, proposed_text: str, specific_aspect_under_review: str = "the overall clause"):
        explicit_rules_assessment_str = ""
        all_possible_args = {
            'clause_text': proposed_text,
            'specific_aspect': specific_aspect_under_review,
            # 'description' and 'ref' will be added per rule
        }

        for rule in self.explicit_rules:
            current_template = rule.get("validation_query_template", "Assess if '{clause_text}' conflicts with Shari'ah principle: {description} (Ref: {ref}).")
            placeholders_in_template = self._get_placeholders(current_template)

            # Prepare arguments specifically for the current template
            current_args = {}
            for ph in placeholders_in_template:
                if ph in all_possible_args:
                    current_args[ph] = all_possible_args[ph]
                elif ph == 'description':
                    current_args[ph] = rule.get("description", "N/A")
                elif ph == 'ref':
                    current_args[ph] = rule.get("standard_ref", "N/A")
                # Add other rule-specific keys if needed, or handle missing keys gracefully

            # Ensure all placeholders in the template are satisfied by current_args
            # or provide defaults/handle if a placeholder is not in current_args (though the above logic tries to populate them)
            try:
                query_for_llm = current_template.format(**current_args)
            except KeyError as e:
                print(f"KeyError during template formatting for rule '{rule.get('rule_id')}': {e}. Template: '{current_template}', Args: {current_args}")
                explicit_rules_assessment_str += f"\nCheck against Rule '{rule.get('rule_id')}' ({rule.get('description')}):\nAssessment: Error formatting query - missing key {e}.\n"
                continue # Skip this rule if formatting fails

            rule_assessment_chain = self.create_chain("{query}", ["query"]) # Simple pass-through
            assessment_result = self.invoke_chain(rule_assessment_chain, query=query_for_llm)
            explicit_rules_assessment_str += f"\nCheck against Rule '{rule.get('rule_id')}' ({rule.get('description')}):\nAssessment: {assessment_result.get('text', 'Error in rule assessment.')}\n"

        # ... (rest of the SCVA method remains the same as in the previous full code block)
        ss_context = "No relevant Shari'ah Standard context automatically retrieved."
        if self.ss_retriever:
            try:
                # Retrieve context relevant to the proposed text
                docs = self.ss_retriever.get_relevant_documents(proposed_text + " " + specific_aspect_under_review)
                ss_context = "\n---\n".join([f"Source Chunk:\n{doc.page_content}" for doc in docs])
            except Exception as e:
                ss_context = f"Error retrieving SS context: {e}"

        prompt_str = """
        Task: Perform a Shari'ah Compliance Validation.

        Proposed Text for an AAOIFI Financial Accounting Standard:
        "{proposed_text}"
        (This proposal concerns: {specific_aspect_under_review})

        Assessment against Explicit Shari'ah Rules:
        {explicit_rules_assessment_str}

        Relevant General Shari'ah Principles/Clauses from AAOIFI Shari'ah Standards (retrieved context):
        "{shariah_standard_context}"

        Overall Assessment Request:
        Based on ALL the above information (explicit rule checks and general SS context), provide an overall Shari'ah compliance assessment for the "Proposed Text".
        1. State your overall assessment: [Compliant / Potential Conflict / Needs Further Scholarly Review / Insufficient Information for Assessment].
        2. Provide a detailed explanation. If potential conflicts or areas needing review are identified, be specific, reference the rule/principle from the explicit checks or the SS context, and explain WHY it's a concern. If compliant, explain how it aligns.

        Shari'ah Compliance Assessment:
        [Your Overall Assessment Status]

        Detailed Explanation & Justification:
        [Your Detailed Explanation]
        """
        chain = self.create_chain(prompt_str, ["proposed_text", "specific_aspect_under_review", "explicit_rules_assessment_str", "shariah_standard_context"])
        return self.invoke_chain(chain, proposed_text=proposed_text,
                                 specific_aspect_under_review=specific_aspect_under_review,
                                 explicit_rules_assessment_str=explicit_rules_assessment_str,
                                 shariah_standard_context=ss_context)


    def validate_inter_standard_consistency(self, proposed_text: str, fas_name: str):
        # Simplified ISCCA for MVP
        fas_context = "No other FAS context automatically retrieved for consistency check."
        if self.fas_retriever:
            try:
                # Retrieve potentially conflicting or related definitions/rules from other FAS
                docs = self.fas_retriever.get_relevant_documents(f"Definitions or rules related to concepts in: {proposed_text[:100]}")
                fas_context = "\n---\n".join([f"Relevant excerpt from another FAS:\n{doc.page_content}" for doc in docs])
            except Exception as e:
                fas_context = f"Error retrieving other FAS context: {e}"

        prompt_str = """
        Task: Perform an Inter-Standard Consistency Check.

        A proposed amendment for AAOIFI Standard {fas_name} is:
        "{proposed_text}"

        Potentially relevant context from OTHER AAOIFI Financial Accounting Standards (for checking terminology, definitions, or conflicting treatments):
        "{other_fas_context}"

        Assessment Request:
        1. Does the terminology used in the "Proposed Text" align with established AAOIFI glossaries or definitions used in other FAS (based on provided context or general knowledge of AAOIFI standards)?
        2. Does the "Proposed Text" introduce any potential contradictions with established principles or treatments in other AAOIFI FAS (based on provided context or general knowledge)?
        Highlight any specific concerns regarding consistency or coherence.

        Consistency Assessment:
        [Consistent / Potential Inconsistency / Needs Further Review for Consistency]

        Detailed Explanation:
        [Your Detailed Explanation]
        """
        chain = self.create_chain(prompt_str, ["proposed_text", "fas_name", "other_fas_context"])
        return self.invoke_chain(chain, proposed_text=proposed_text, fas_name=fas_name, other_fas_context=fas_context)