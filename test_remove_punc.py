import re

# Sample text with punctuation
text = "This is a sample text, [] with some punctuation! How can we remove it? ' ' '" " And keep numbers like $23.1."

# Remove punctuation, keeping numbers
clean_text = re.sub(r'[^\w\s.$]+', '', text)

# Print the cleaned text
print(clean_text)