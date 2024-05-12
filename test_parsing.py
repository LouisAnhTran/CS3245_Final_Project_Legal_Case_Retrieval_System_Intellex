import re

search_query = '"fertility treatment" AND damages AND testoteron AND "legal retriever"'

# Regular expression pattern to match phrases within double quotes or single terms
pattern = r'"([^"]+)"|(\b\w+\b)'

# Extracting matched phrases or terms
parsed_terms = [match.group(1) or match.group(2) for match in re.finditer(pattern, search_query)]

print(parsed_terms)