import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    model = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")

    response = client.responses.create(
        model=model,
        instructions="You are MyAgent, a helpful AI assistant.",
        input="请用一句话解释什么是 AI Agent。",
    )

    print(response.output_text)
    print(response.to_json())
    print(response.to_dict())


if __name__ == "__main__":
    main()
