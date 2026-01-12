from turtle import dot
from volcenginesdkarkruntime import Ark
import os
import dotenv
dotenv.load_dotenv()

client = Ark(api_key=os.environ.get("DOUBAO_API_KEY"))

if __name__ == "__main__":
    resp = client.content_generation.tasks.get(
        task_id="cgt-20260109140619-qj2t5",
    )
    print(resp)