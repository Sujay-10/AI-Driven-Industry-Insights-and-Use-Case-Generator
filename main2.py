from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel, ConfigDict

load_dotenv()

google_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if google_api_key is None:
    raise ValueError("Environment variable 'GOOGLE_GEMINI_API_KEY' is not set. Please set it before running the script.")

os.environ['GOOGLE_API_KEY'] = google_api_key

llm = GoogleGenerativeAI(model='gemini-pro')

industry_research_prompt = PromptTemplate(
    input_variables=["industry"],
    template="Conduct research on the {industry} industry, focusing on key trends and standards in AI and ML."
)

use_case_generation_prompt = PromptTemplate(
    input_variables=["industry"],
    template="Based on the research about the {industry} industry, propose relevant use cases where the company can leverage GenAI, LLMs, and ML technologies to improve their processes, enhance customer satisfaction, and boost operational efficiency."
)

resource_collection_prompt = PromptTemplate(
    input_variables=["use_cases"],
    template="""For the following use cases: {use_cases}, find datasets and relevant resources from trusted sources like:
    - Kaggle 
    - Hugging Face 
    - GitHub 
    Ensure all links are valid and lead to real datasets.
    """
)

# Define custom configuration for tools
class CustomTool(Tool):
    class Config:
        arbitrary_types_allowed = True

# Define tool functions
def industry_research_tool(industry):
    response = llm.generate([industry_research_prompt.format(industry=industry)])
    return clean_response(response)

def use_case_generation_tool(industry):
    response = llm.generate([use_case_generation_prompt.format(industry=industry)])
    return clean_response(response)

def resource_collection_tool(use_cases):
    response = llm.generate([resource_collection_prompt.format(use_cases=use_cases)])
    return clean_response(response)

# Initialize tools
tools = [
    CustomTool(
        name="Industry Research",
        func=industry_research_tool,
        description="Research the specified industry"
    ),
    CustomTool(
        name="Use Case Generation",
        func=use_case_generation_tool,
        description="Generate use cases based on industry research"
    ),
    CustomTool(
        name="Resource Collection",
        func=resource_collection_tool,
        description="Collect datasets for the proposed use cases from Kaggle, Hugging Face, and GitHub"
    ),
]

# Initialize agent
agent = initialize_agent(tools, llm, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

def clean_response(response):
    """Extracts the generated text from the response and removes unwanted characters."""
    if isinstance(response, dict):
        generations = response.get("generations", [])
        if generations and isinstance(generations[0], dict):
            # Extract the 'text' from the first generation and clean up the result
            generated_text = generations[0].get("text", "")
            return generated_text.replace("\n\n", "\n").strip()
    return str(response).replace("\n\n", "\n").strip()

def main():
    st.title("Industry Research and Generative AI Use Cases")

    if "industry" not in st.session_state:
        st.session_state.industry = None
    if "use_cases" not in st.session_state:
        st.session_state.use_cases = None
    if "resources" not in st.session_state:
        st.session_state.resources = None

    industry = st.text_input("Enter the Industry/Company you want to search:")

    if st.button("Submit"):
        if industry:
            st.session_state.industry = industry
            
            def safe_run(func, *args):
                try:
                    return func(*args)
                except Exception as e:
                    return f"Error: {str(e)}"

            # Call tools and clean the responses
            research_results = safe_run(agent.tools[0].func, industry)
            use_cases = safe_run(agent.tools[1].func, industry)
            st.session_state.use_cases = use_cases

            resources = safe_run(agent.tools[2].func, use_cases)
            st.session_state.resources = resources  

            # Save results to text files
            with open("research_results.txt", "w") as f:
                f.write(f"Industry Research Results:\n\n{research_results}\n")

            with open("use_cases.txt", "w") as f:
                f.write(f"Proposed Use Cases:\n\n{use_cases}\n")
            
            with open("resources.txt", "w") as f:
                f.write(f"Resource Links:\n\n{resources}\n")

            st.success("Results have been saved to research_results.txt, use_cases.txt, and resources.txt.")
        else:
            st.error("Please enter an industry.")

    # Display output in Streamlit
    if st.session_state.use_cases and st.session_state.resources:
        output_option = st.selectbox("Select the output you want to see:", ("Use Cases", "Resources"))

        if output_option == "Use Cases":
            st.subheader("Proposed Use Cases")
            st.markdown(st.session_state.use_cases)
        else:
            st.subheader("Resource Links")
            st.markdown(st.session_state.resources)

if __name__ == "__main__":
    main()


