import pickle 

import config_origin

with open('number_of_documents.txt','rb') as file:
    file.seek(0)
    no_docs=pickle.load(file)
    print("no of docs: ",no_docs)

# with open('dictionary.txt','rb') as file:
#     file.seek(0)
#     dictionary=pickle.load(file)
#     print(dictionary)
#     print("call ",dictionary["call"])

# with open('postings.txt','rb') as file:
#     file.seek(72)
#     print(pickle.load(file))

# with open('length_documents.txt','rb') as file:
#     file.seek(0)
#     dictionary=pickle.load(file)
#     print("doc: ",dictionary[2211154])
#     # print(pickle.load(file))

# with open('dictionary.txt','rb') as file:
#     file.seek(0)
#     dictionary=pickle.load(file)
#     print("dictionary: ",dictionary)
    # print(pickle.load(file))

# with open('dict_docid_to_court.txt','rb') as file:
#     file.seek(0)
#     print(pickle.load(file))

# [(246391, 2, [2455, 2643], 2), (246400, 1, [1111]), (246403, 2, [1798, 1829]), (246404, 5, [1371, 2233, 2534, 2657, 2683]), (246407, 2, [1856, 1869])]


# [(246391, 5, 2), (246400, 2), (246404, 3), (246407, 3)]