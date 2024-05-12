import pickle 

import config

# with open('blocks.txt','rb') as file:
#     file.seek(1233210)
#     blocks=pickle.load(file)
#     # print("no of docs: ",blocks)
#     with open("b2.txt",'ab') as file:
#         pickle.dump(blocks,file)
#         file.close()

def compare_dicts():
    with open('dictionary.txt','rb') as file:
        dict1=pickle.load(file)

    with open('store_for_bsbi/dictionary.txt','rb') as file:
        dict2=pickle.load(file)
    
    # Check if keys are the same
    if set(dict1.keys()) != set(dict2.keys()):
        return False

    # Check if values are the same for each key
    for key in dict1:
        if dict1[key] != dict2[key]:
            return False
    return True

print(compare_dicts())

# c=[1,2,3]
# print(c[::-1])
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