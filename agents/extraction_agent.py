from .base_agent import BaseAgent
from langchain.chains import RetrievalQA

class ExtractionAgent(BaseAgent):
    def __init__(self, vector_store=None, **kwargs):
        super().__init__(system_message="You are an expert AAOIFI standard analyst focused on accurate information extraction.", **kwargs)
        self.vector_store = vector_store
        self.qa_chain = None
        if self.vector_store:
            try:
                retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.get_llm_instance(), # Get raw LLM for RetrievalQA
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=True
                )
            except Exception as e:
                print(f"Error initializing RetrievalQA in ExtractionAgent: {e}")


    def extract_definitions(self, text_chunk: str):
        prompt_str = """
        From the following text snippet from an AAOIFI standard, extract all explicitly defined terms and their corresponding definitions.
        Present the output as a JSON list, where each item is an object with "term" and "definition" keys.
        If no definitions are found, return an empty list.

        Text:
        {standard_text_chunk}

        JSON Output:
        """
        chain = self.create_chain(prompt_str, ["standard_text_chunk"])
        return self.invoke_chain(chain, standard_text_chunk=text_chunk)

    def identify_key_clauses(self, topic: str, standard_name="the standard"):
        if not self.qa_chain:
            return {"text": "Error: Vector store / QA chain not initialized.", "error": True}
        query = f"What are the key clauses, rules, or requirements related to '{topic}' in {standard_name}? Summarize them concisely."
        try:
            # RetrievalQA returns a dictionary
            result_dict = self.qa_chain.invoke({"query": query})
            return {
                "text": result_dict.get("result", "No answer found."),
                "sources": [doc.page_content for doc in result_dict.get("source_documents", [])]
            }
        except Exception as e:
            print(f"Error in identify_key_clauses: {e}")
            return {"text": f"Error during QA: {e}", "error": True}

    def find_ambiguities(self, text_chunk: str):
        prompt_str = """
        Review the following text snippet from an AAOIFI standard for potential ambiguities,
        unclear phrasing, or sections that might lead to misinterpretation in practical application.
        List each identified ambiguity with a brief explanation. If none, state "No significant ambiguities found".

        Text:
        {standard_text_chunk}

        Ambiguities Found:
        1. [Ambiguity 1]: [Explanation of why it's ambiguous]
        2. [Ambiguity 2]: [Explanation of why it's ambiguous]
        ...
        (If none, state: No significant ambiguities found in this chunk.)
        """
        chain = self.create_chain(prompt_str, ["standard_text_chunk"])
        return self.invoke_chain(chain, standard_text_chunk=text_chunk)