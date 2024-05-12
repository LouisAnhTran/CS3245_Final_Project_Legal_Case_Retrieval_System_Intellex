import pickle 
import config_origin

with open(config_origin.STORE_COURT_DOCS,'rb') as file:
    file.seek(0)
    dictionary=pickle.load(file)
    print("court info docs: ",dictionary[4273155])