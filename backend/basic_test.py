import os
from openai import OpenAI

# 1) Upload directly to OpenAI (this MUST use the same OpenAI key that the gateway will use)
openai_direct = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pdf_path = "source_example/02-backtracking.pdf"
with open(pdf_path, "rb") as f:
    uploaded = openai_direct.files.create(file=f, purpose="user_data")

# 2) Call KeywordsAI Gateway for chat
gateway = OpenAI(
    base_url="https://api.keywordsai.co/api/",  # note trailing slash matches their docs
    api_key=os.getenv("KEYWORDSAI_API_KEY_TEST"),
)

response = gateway.chat.completions.create(
    model="gpt-4.1",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's this file about?"},
            {"type": "file", "file": {"file_id": uploaded.id}},
        ],
    }],
    # IMPORTANT: force gateway to use the same OpenAI key as the upload
    extra_body={
        "customer_credentials": {
            "openai": {"api_key": os.getenv("OPENAI_API_KEY")}
        }
    },
)

print(response.choices[0].message.content)
