#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import string 
import re
from nltk.stem.porter import *
from nltk.corpus import stopwords
import pickle
import math 
from nltk.tokenize import RegexpTokenizer
import os
from nltk.corpus import wordnet
from nltk.util import bigrams


import config_origin
from Dictionary import Dictionary
from PostingList import PostingsList

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    
    # retrieve dictionary from memory
    dictionary_object=Dictionary(dict_file)
    dictionary=dictionary_object.load_dictionary_from_file()

    # instantiate posting list object
    posting_list=PostingsList(postings_file)

    # load number of documents from memory
    number_of_docs=load_data_from_memory(config_origin.STORE_NUMBER_DOCS)

    # load dictionary of document length from memory
    dict_docids_to_length=load_data_from_memory(config_origin.STORE_LENGTH_DOCS)

    # load dictionary of docids to court informarion
    dict_docids_to_court_info=load_data_from_memory(config_origin.STORE_COURT_DOCS)

    with open(queries_file, 'r') as file:
        lines = file.readlines()
        # Do something with the file content
        print(f'Content of {queries_file}:')
        query=lines[0]
        if "AND" not in query:
            handle_free_text_queries(lines[0],dictionary,number_of_docs,posting_list,dict_docids_to_length,results_file,dict_docids_to_court_info)
        else: 
            handle_boolean_queries(query,dictionary,posting_list,number_of_docs,dict_docids_to_length,results_file,dict_docids_to_court_info)


def handle_boolean_queries(query,dictionary,posting_list,number_of_docs,length_dictionary,results_file,dict_docids_to_court_info):
    # Regular expression pattern to match phrases within double quotes or single terms
    pattern = r'"([^"]+)"|(\b\w+\b)'

    # Extracting matched phrases or terms
    parsed_terms = [match.group(1) or match.group(2) for match in re.finditer(pattern, query)]
    parsed_terms_without_and=[term for term in parsed_terms if term!='AND']
    uni_terms=[term for term in parsed_terms_without_and if " " not in term]
    phrases=[term for term in parsed_terms_without_and if " " in term]              
    print(parsed_terms_without_and)
    print("single terms ",uni_terms)
    print("phrases: ",phrases)

    # handle single term 
    # expanded_query=expand_query_with_wordnet(" ".join(uni_terms))
    # print("expanded query: ",expanded_query)
    single_terms_query = tokenize_and_sanitize_query(' '.join(uni_terms))  # Tokenize the query
    # print("for single: ",query_terms)
    
    # handle phrases
    phrase_terms=handle_phrase_in_boolean_queries(phrases)

    all_terms=single_terms_query+phrase_terms

    print("all_terms: ",all_terms)

    all_docs=find_all_docs_for_boolean_query(all_terms,dictionary,posting_list)
    print(all_docs)

    if not all_docs:
        with open(results_file,'w') as out_file:
            out_file.write(""+"\n")
    else:
        vector_query = convert_query_to_vector(all_terms, dictionary, number_of_docs)  # Construct the vector query
        result=""
        if vector_query:
            score_dictionary = implement_cosine_score_for_a_query(vector_query, posting_list, length_dictionary, dictionary,all_docs)
            print("score dictionary: ",score_dictionary)
            adjust_score_for_court(score_dictionary,dict_docids_to_court_info)
            result = sort_docs_output(score_dictionary)
            result=" ".join(list(map(str,result)))
            print("result: ",result)
        
        with open(results_file,'w') as out_file:
            out_file.write(result+"\n")

def find_all_docs_for_boolean_query(all_terms,dictionary,posting_list:  PostingsList):
    all_terms_in_dict=[term for term in all_terms if term in dictionary]
    print("all term in dict: ",all_terms_in_dict)
    if not all_terms_in_dict :
        return None
    
    # print("all term in dict: ",all_terms_in_dict)
    all_posting_lists=[posting_list.load_posting_from_disk(dictionary[term][1]) for term in all_terms_in_dict]
    sorted_all_in_dict=sorted(all_posting_lists,key=len)
    # print("sorted all post: ",sorted_all_in_dict)
    # print("sorted all in list: ",sorted_all_in_dict)
    # print("quick check ",list(map(len,sorted_all_in_dict)))
    # sorted_all_in_dict=[[(1,1,3),(2,1),(3,1),(4,1)],[(1, 4, 3), (2, 1), (3, 1), (4, 2, 6), (5, 1), (6, 1), (7, 7,9), (8, 2), (9, 1), (10, 2)],[(2, 4, 3), (4, 1), (5, 1), (6, 2, 6), (7, 1), (8, 1), (9, 7,9), (10, 2), (11, 1), (12, 2)]]
    # print("new sorted: ",sorted_all_in_dict)

    # decoding all posting list
    for posting_list in sorted_all_in_dict:
        gap_decoding_posting_list(posting_list)

    if len(sorted_all_in_dict)==1:
        return [doc[0] for doc in sorted_all_in_dict[0]]
    stack=[sorted_all_in_dict[0]]
    j=1
    while j<len(sorted_all_in_dict) and stack[0]:
        print("//////////////")
        print("first list: ",stack[0])
        print("second list: ",sorted_all_in_dict[j])
        merged_list=merge_two_posting_list(stack[0],sorted_all_in_dict[j])
        print("merged list: ",merged_list)
        if not merged_list:
            return None
        add_skip_pointer_to_merged_posting_list(merged_list)
        print("merged list after add pointer ",merged_list)
        print()
        stack[0]=merged_list
        j+=1
    print("stack ",stack)
    return [doc[0] for doc in stack[0]]

def merge_two_posting_list(first_list,second_list):
    result=[]
    if not first_list or not second_list:
        return []
    i,j=0,0

    while i<len(first_list) and j<len(second_list):
        if first_list[i][0]==second_list[j][0]:
            result.append(first_list[i])
            i+=1
            j+=1
        elif first_list[i][0]<second_list[j][0]:
            if len(first_list[i])==3 and first_list[first_list[i][2]][0]<=second_list[j][0]:
                while len(first_list[i])==3 and first_list[first_list[i][2]][0]<=second_list[j][0]:
                    i=first_list[i][2]
            else:
                i+=1
        elif first_list[i][0]>second_list[j][0]:
            if len(second_list[j])==3 and second_list[second_list[j][2]][0]<=first_list[i][0]:
                while len(second_list[j])==3 and second_list[second_list[j][2]][0]<=first_list[i][0]:
                    j=second_list[j][2]
            else:
                j+=1
    return result

def handle_phrase_in_boolean_queries(phrases):
    result=[]
    for phrase in phrases:
        query_terms=tokenize_and_sanitize_query(phrase)
        list_bi_grams=list(bigrams(query_terms))
        result.extend(list_bi_grams)
    print("result: ",result)
    return result 

def handle_free_text_queries(query,dictionary,number_of_docs,posting_list,length_dictionary,results_file,dict_docids_to_court_info):
    # Convert query to vector
    query = query.strip()
    expanded_query=expand_query_with_wordnet(query)
    print("expanded query: ",expanded_query)
    query_terms = tokenize_and_sanitize_query(' '.join(expanded_query))  # Tokenize the query
    vector_query = convert_query_to_vector(query_terms, dictionary, number_of_docs)  # Construct the vector query
    
    result=""
    if vector_query:
        score_dictionary = implement_cosine_score_for_a_query(vector_query, posting_list, length_dictionary, dictionary)
        print("score dictionary: ",score_dictionary)
        adjust_score_for_court(score_dictionary,dict_docids_to_court_info)
        result = sort_docs_output(score_dictionary)
        print("result after sorted: ",result)
        result=" ".join(list(map(str,result)))
        print("result: ",result)
    
    with open(results_file,'w') as out_file:
        out_file.write(result+"\n")

def adjust_score_for_court(score_dict,docid_to_court):
    for docid in score_dict:
        court_info=docid_to_court[docid]
        score_dict[docid]*=(config_origin.WEIGHT_MOST_IMPORTANT if court_info in config_origin.COURT_MOST_IMPORTANT else config_origin.WEIGHT_IMPORTANT if court_info in config_origin.COURT_IMPORTANT else 1)

def expand_query_with_wordnet(query):
    expanded_query = []
    for term in query.split():
        synonyms = []
        for syn in wordnet.synsets(term):
            synonyms.extend(syn.lemma_names())
        synonyms=list(set([term.lower() for term in synonyms]))
        expanded_query.extend(synonyms)
    return list(set(expanded_query))

def implement_cosine_score_for_a_query(vector_query,posting_lists:PostingsList,length_dictionary,dictionary,list_of_docids=[]):
    """
        implement the cosine score computation for a given query
    """
    score_dictionary={}
    for term in vector_query:
        # load the posting list given the term
        fetch_post_list=posting_lists.load_posting_from_disk(dictionary[term][1])
        gap_decoding_posting_list(fetch_post_list)
        for item in fetch_post_list:
            if not list_of_docids:    
                score_dictionary[item[0]]=score_dictionary.get(item[0],0)+(1+math.log(item[1],10))*vector_query[term]
            elif item[0] in list_of_docids:
                score_dictionary[item[0]]=score_dictionary.get(item[0],0)+(1+math.log(item[1],10))*vector_query[term]
    # normalize the score
    score_dictionary={docid:(score_before_normalization/length_dictionary[docid]) for docid,score_before_normalization in score_dictionary.items()}
    return score_dictionary    

def gap_decoding_posting_list(posting_list):
    if len(posting_list)==1:
        return
    accumulate=posting_list[0][0]
    for j in range(1,len(posting_list)):
        decode_doc_id=accumulate+posting_list[j][0]
        if len(posting_list[j])>2:
            posting_list[j]=(decode_doc_id,posting_list[j][1],posting_list[j][2])
        else:
            posting_list[j]=(decode_doc_id,posting_list[j][1])
        accumulate=decode_doc_id

def sort_docs_output(score_dictionary):
    """
        return a top documents with highest normalized scores
    """
    return sorted(score_dictionary,key=lambda x: score_dictionary[x],reverse=True)


def load_data_from_memory(filename):
    """
        load data structure or object from the hard disk
    """
    with open(filename,'rb') as file:
        return pickle.load(file)
    
def tokenize_and_sanitize_query(query_term):
    """
        tokenize the query using sentence tokenization, word tokenization, case folding and stemming
    """
    stop_words=set(stopwords.words('english'))
    tokens=[word for sentence in nltk.sent_tokenize(query_term) for word in nltk.word_tokenize(sentence)]
    tokens_without_stop_words=[token for token in tokens if token.lower not in stop_words]
    stemmer=PorterStemmer()
    query_terms=[stemmer.stem(token).lower() for token in tokens_without_stop_words] # stemming and lower case
    return query_terms

def remove_punctuation_token(token):
    punctuation_set = {",","."}
    i=0
    while i<len(token) and token[i] in punctuation_set:
        i+=1
    if i==len(token):
        return ""
    left_token=token[i:]
    i=len(left_token)-1
    while i>=0 and left_token[i] in punctuation_set:
        i-=1
    right_token=left_token[:i+1]
    return right_token

def add_skip_pointer_to_merged_posting_list(merged_posting_list):
    # remove previous pointer
    for i in range(len(merged_posting_list)):
        merged_posting_list[i]=(merged_posting_list[i][0],merged_posting_list[i][1])
    doc_frequency=len(merged_posting_list)
    if doc_frequency<=1:
        return
    number_of_skip_pointers=int(math.sqrt(doc_frequency))
    skip_pointing_size=int(doc_frequency/number_of_skip_pointers)

    for i in range(doc_frequency-skip_pointing_size-1):
        if i%skip_pointing_size==0:
            merged_posting_list[i]=(merged_posting_list[i][0],merged_posting_list[i][1],i+skip_pointing_size)

def convert_query_to_vector(query_terms,dictionary,number_of_docs):
    """
        convert the query into vector, using (1+log(tf))*(log(N/df)) formula
    """
    query_terms=[term for term in query_terms if term in dictionary] # remove term that not appear in dictionary or vocabulary
    if not query_terms:
        return None
    dict_query_terms=dict()
    for term in query_terms:
        dict_query_terms[term]=dict_query_terms.get(term,0)+1
    # apply the formula: (1+log(tf))*(log(N/df)) 
    vector_query={term:(1+math.log(tf,10))*math.log(number_of_docs/dictionary[term][0],10) for term,tf in dict_query_terms.items()}
    return vector_query


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
