from dotenv import load_dotenv
import os

# Load the environment variables when the module is imported
load_dotenv()


key = os.getenv("AZURE_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")
openaikey = os.getenv("OPENAI_API_KEY")
