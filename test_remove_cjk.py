import re

def remove_cjk(text):
    # Unicode ranges for Chinese, Japanese, and Korean characters
    pattern = r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\u3131-\uD79D]'
    return re.sub(pattern, '', text)

# sample_text = "This is an English text with some Chinese characters 漢字 and Japanese かな and Korean 한글."
sample_text = "漢字かな한글"
print(sample_text)
clean_text = remove_cjk(sample_text)
print("clean text: ",clean_text)