from .base_agent import BaseAgent
# No need for RetrievalQA here if context is passed directly

class SuggestionAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(temperature=0.5, system_message="You are an AI assistant specialized in drafting and enhancing AAOIFI Financial Accounting Standards with a focus on clarity, Shari'ah alignment, and practicality.", **kwargs)
        # Retrievers for RAG can be passed to methods if needed, or managed by orchestrator

    def generate_clarification(self, original_text: str, identified_ambiguity: str,
                               fas_context: str = "No specific FAS context provided.",
                               ss_context: str = "No specific SS context provided."):
        prompt_str = """
        The following paragraph from an AAOIFI FAS has been identified with an ambiguity:
        Original Paragraph:
        "{original_text}"

        Identified Ambiguity by another agent:
        "{identified_ambiguity}"

        Relevant context from the Financial Accounting Standard (FAS) itself:
        "{fas_context}"

        Relevant context from related AAOIFI Shari'ah Standards (SS):
        "{ss_context}"

        Task:
        1. Draft a revised version of the Original Paragraph to address the identified ambiguity and significantly improve its clarity and precision.
        2. The revised version MUST maintain the original intent of the standard as much as possible.
        3. The revised version MUST remain compliant with Shari'ah principles as reflected in the provided SS context.
        4. Provide detailed reasoning for your changes, explaining how they address the ambiguity and align with any cited FAS or SS context. Specifically mention how Shari'ah alignment is maintained or improved.

        Output Format:
        Revised Paragraph:
        [Your Suggested Text for the revised paragraph]

        Reasoning & Shari'ah Alignment:
        [Your Detailed Explanation, including specific references to FAS/SS context if applicable]
        """
        chain = self.create_chain(prompt_str, ["original_text", "identified_ambiguity", "fas_context", "ss_context"])
        return self.invoke_chain(chain, original_text=original_text, identified_ambiguity=identified_ambiguity,
                                 fas_context=fas_context, ss_context=ss_context)

    def propose_enhancement_for_gap(self, gap_description: str, fas_name: str,
                                    fas_context: str = "No specific FAS context provided.",
                                    ss_context: str = "No specific SS context provided.",
                                    external_standard_context: str = "No external standard context provided."):
        prompt_str = """
        A potential gap or area for enhancement has been identified in {fas_name}:
        Gap Description: "{gap_description}"

        Relevant context from {fas_name} (if any part is being amended):
        "{fas_context}"

        Relevant context from related AAOIFI Shari'ah Standards (SS):
        "{ss_context}"

        Relevant context from comparative external standards (e.g., IFRS), if provided:
        "{external_standard_context}"

        Task:
        1. Propose a new clause, or an amendment to an existing clause (if fas_context is provided for amendment), for {fas_name} to address this gap/enhancement.
        2. The proposal must be clear, practical for implementation by Islamic financial institutions, and rigorously align with Shari'ah principles outlined in the SS context.
        3. Explain your reasoning in detail, including how the proposal addresses the gap and how it aligns with the cited FAS, SS, or external standard contexts.

        Output Format:
        Proposed Clause/Amendment for {fas_name}:
        [Your Suggested Text for the new or amended clause]

        Reasoning & Source Alignment:
        [Your Detailed Explanation, citing specific contexts]
        """
        chain = self.create_chain(prompt_str, ["gap_description", "fas_name", "fas_context", "ss_context", "external_standard_context"])
        return self.invoke_chain(chain, gap_description=gap_description, fas_name=fas_name,
                                 fas_context=fas_context, ss_context=ss_context,
                                 external_standard_context=external_standard_context)