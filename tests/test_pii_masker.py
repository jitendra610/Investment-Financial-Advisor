from app.guardrails.pii_masker import mask_pii


query = (
    "My name is Rahul Sharma. "
    "I am 36 years old. "
    "My email is rahul@example.com. "
    "My phone number is 9876543210. "
    "Suggest an investment plan."
)

result = mask_pii(query)

print("Original:", query)
print("Masked:", result["masked_text"])
print("Detected:", result["entities"])