import pickle

class Dictionary:
    def __init__(self,dict_file):
        self.dict_file=dict_file
        self.dictionary=dict()

    def insert_term_to_dictionary(self,term,doc_freq,offset):
        self.dictionary[term]=(doc_freq,offset)

    def save_dictionary_to_file(self):
        with open(self.dict_file,'wb') as file:
            pickle.dump(self.dictionary,file)
        file.close()

    def load_dictionary_from_file(self):
        with open(self.dict_file,'rb') as file:
            return pickle.load(file)
    
