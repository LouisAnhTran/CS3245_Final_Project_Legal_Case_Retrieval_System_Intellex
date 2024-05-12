import pickle

from Dictionary import Dictionary

class PostingsList:
    def __init__(self,posting_file):
        self.posting_file=posting_file
        self.dictionary=dict()

    def save_posting_to_disk(self,index_dict,dictionary: Dictionary):
        with open(self.posting_file,'wb') as file:
            for term, posting_list in index_dict.items():
                offset=file.tell()
                document_frequency=len(posting_list)
                dictionary.insert_term_to_dictionary(term,document_frequency,offset)
                pickle.dump(posting_list,file)
        file.close()

    def load_posting_from_disk(self,offset):
        with open(self.posting_file,'rb') as file:
            file.seek(offset)
            return pickle.load(file)
    