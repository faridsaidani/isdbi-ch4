import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser # For simple string output
from langchain.chains import LLMChain # Still useful for simple chains

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class BaseAgent:
    """
    A base class for AI agents, initializing the Gemini LLM.
    """
    def __init__(self, model_name="gemini-2.0-flash", temperature=0.2, system_message=None): # Using flash for speed
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
        try:
            # For ChatGoogleGenerativeAI, system messages are part of the prompt or handled differently.
            # We'll add a system instruction to the prompt directly if needed.
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=GOOGLE_API_KEY,
                # convert_system_message_to_human=True # May be needed depending on Langchain version and Gemini model
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini LLM. Check API key/model name: {e}")
        self.output_parser = StrOutputParser()
        self.system_message_prefix = f"{system_message}\n\n" if system_message else ""
        print(f"BaseAgent initialized with model: {model_name}, temperature: {temperature}")

    def create_chain(self, prompt_template_str: str, input_variables: list):
        """Creates an LLMChain with a prompt and the initialized LLM."""
        # Prepend system message to the user's prompt template
        full_prompt_template_str = self.system_message_prefix + prompt_template_str
        prompt = PromptTemplate(template=full_prompt_template_str, input_variables=input_variables)
        chain = prompt | self.llm | self.output_parser # Using LCEL (Langchain Expression Language)
        return chain

    def invoke_chain(self, chain, **kwargs):
        """Invokes a pre-created chain with provided arguments."""
        try:
            response = chain.invoke(kwargs)
            return {"text": response} # Ensuring dictionary output for consistency
        except Exception as e:
            print(f"Error invoking chain: {e}")
            return {"text": f"Error: {e}", "error": True}

    def get_llm_instance(self):
        """Returns the raw LLM instance for more complex Langchain constructs if needed."""
        return self.llm