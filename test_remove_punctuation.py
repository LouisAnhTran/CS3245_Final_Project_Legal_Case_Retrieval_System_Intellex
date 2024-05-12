import re

def remove_punctuation(text):
    # Preserve decimals and commas in numbers, and preserve "mr." followed by a letter or a period
    return re.sub(r'(?<!\d)(?<!mr)\.|(?<!\d)[^\w\s]|(?<=\bmr)\.', '', text)

# Example usage:
text_with_punctuation = "Hello, world! How are you? The value is 31.41, or maybe 31,313. Also, say hi to mr.T."
clean_text = remove_punctuation(text_with_punctuation)
print(clean_text)



