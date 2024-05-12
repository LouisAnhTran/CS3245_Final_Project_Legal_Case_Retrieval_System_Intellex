from nltk.stem.porter import *
from nltk.corpus import stopwords
import string
import re

stop_words = set(stopwords.words('english'))
valid_set = string.ascii_letters + string.digits

print("valid set: ",valid_set)

def is_valid(str):
    if str in stop_words:
        return False
    for letter in str:
        if letter not in valid_set:
            return False
    return True