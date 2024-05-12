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


import config
from bool_search import handle_boolean_queries
from Dictionary import Dictionary
from PostingList import PostingsList

def handle_free_text_queries(query,dictionary,number_of_docs,posting_list,length_dictionary,results_file,dict_docids_to_court_info):
    """
    perform search on free-text queries

    Args:
        query (str): query to perform search on
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        number_of_docs (int): total number of documents
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
        length_dictionary ({int : float}): dictionary of key - doc_id, val - length
        results_file (str): output file name
        dict_docids_to_court ({int : str}): dictionary of key - doc_id, val - court name
    """
    
    query = query.strip()
    
    # get expanded query using WordNet thesaurus
    expanded_query=expand_query_with_wordnet(query)

    # consolidate expanded terms and original terms 
    combined_query=query.split()+expanded_query

    # tokenize and apply stemming, case-folding to the expanded query
    query_terms = tokenize_and_sanitize_query(' '.join(combined_query))  # Tokenize the query

    # stemming, case folding for term in original query
    stemmed_original_query=tokenize_and_sanitize_query(query)


    # convert expanded query to vector
    vector_query = convert_query_to_vector(query_terms, dictionary, number_of_docs,stemmed_original_query)  # Construct the vector query
    
    result=""
    if vector_query:
        # retrieve adjusted cosine scores for each (relevant) document 
        score_dictionary = implement_cosine_score_for_a_query(vector_query, posting_list, length_dictionary, dictionary)
        adjust_score_for_court(score_dictionary,dict_docids_to_court_info)
        # sort the scores, and reformat as a space-seperated string 
        result = sort_docs_output(score_dictionary)
        result=" ".join(list(map(str,result)))
    
    # write string into the results file
    with open(results_file,'w') as out_file:
        out_file.write(result+"\n")

def adjust_score_for_court(score_dict,docid_to_court):
    """
    Method to adjust the cosine scores of each document in score_dict, based on the importance of the court in which it comes from
    
    Args:
        score_dict({int: float}): cosine scores of each document represented by a dictionary of key-val, docID-cosine_score
        docid_to_court({int: str}): represents the courts each document belong to, using a dictionary of key-val, docID-court
    """
    for docid in score_dict:
        court_info=docid_to_court[docid]
        # Multiplies the cosine score of a document, depending if the court is categorised as most important, important, or not important 
        score_dict[docid]*=(config.WEIGHT_MOST_IMPORTANT if court_info in config.COURT_MOST_IMPORTANT else config.WEIGHT_IMPORTANT if court_info in config.COURT_IMPORTANT else 1)

def expand_query_with_wordnet(query):
    """
    Method to expand query using wordnet for free-text queries
    If there exists synonyms, the synonyms will exist in the list of words returned

    Args:
        gram (str): word or phrase obtained from the query

    Returns:
        synonyms ([str]): list of words that are synonyms to the word or phrase provided
    """
    # initialise expanded query variable
    expanded_query = []
    # obtain synonyms for each term
    for term in query.split():
        synonyms = []
        for syn in wordnet.synsets(term):
            synonyms.extend(syn.lemma_names())
        # case-folding for the obtained synonyms
        synonyms=list(set([term.lower() for term in synonyms]))
        expanded_query.extend(synonyms)
    return list(set(expanded_query))


def implement_cosine_score_for_a_query(vector_query,posting_lists:PostingsList,length_dictionary,dictionary,list_of_docids=[]):
    """
    Implement the cosine score computation for a given query

    Args:
        vector_query ({str: float}): dictionary representing the query vector, with each key correlating to a dimension in the vector space
        postings_lists (PostingsList): contains postings list, which is an array of tuples containing doc_id, term freq, skip pointer
        length_dictionary ({int: int}): dictionary representing the length of each document with key-val, docID-doc_len
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        list_of_docids ([int]): list containing all the document IDs of the documents in the dataset
    
    Output:
        score_dictionary ({int: float}): cosine scores of each document represented by a dictionary of key-val, docID-cosine_score
    """
    # Initialise dictionary to contain cosine score of document
    score_dictionary={}
    for term in vector_query:
        # load the posting list for given term
        fetch_post_list=posting_lists.load_posting_from_disk(dictionary[term][1])
        gap_decoding_posting_list(fetch_post_list)
        # add tf-idf score of term to its respective document
        for item in fetch_post_list:
            if not list_of_docids:    
                score_dictionary[item[0]]=score_dictionary.get(item[0],0)+(1+math.log(item[1],10))*vector_query[term]
            elif item[0] in list_of_docids:
                score_dictionary[item[0]]=score_dictionary.get(item[0],0)+(1+math.log(item[1],10))*vector_query[term]
    # normalize the score based on each document's length, to get its final cosine score
    score_dictionary={docid:(score_before_normalization/length_dictionary[docid]) for docid,score_before_normalization in score_dictionary.items()}
    return score_dictionary  

def gap_decoding_posting_list(posting_list):
    """
    Void method that performs gap decoding of posting list to obtain accurate values
    Except for the first node, every doc_id in the posting list nodes is the offset value from the node before it

    Args:
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
    """
    # check if posting list is of length 1
    if len(posting_list)==1:
        return
    # initialize accumulate variable
    accumulate=posting_list[0][0]
    for j in range(1,len(posting_list)):
        # calculate actual doc_id
        decode_doc_id=accumulate+posting_list[j][0]
        if len(posting_list[j])>2:
            posting_list[j]=(decode_doc_id,posting_list[j][1],posting_list[j][2])
        else:
            posting_list[j]=(decode_doc_id,posting_list[j][1])
        # update accumulate variable
        accumulate=decode_doc_id

def sort_docs_output(score_dictionary):
    """
    Return a top documents with highest normalized scores

    Args:
        score_dictionary ({int: float}): cosine scores of each document represented by a dictionary of key-val, docID-cosine_score

    Output:
        sorted score_dictionary based on its value in descending order
    """
    return sorted(score_dictionary,key=lambda x: score_dictionary[x],reverse=True)

def tokenize_and_sanitize_query(query_term):
    """
    Tokenize the query using sentence tokenization, word tokenization, case folding and stemming
    
    Args:
        query_term (str): query string 

    Output:
        query_terms ([str]): list of tokens from query string, after undergoing various steps
    """
    stop_words=set(stopwords.words('english'))
    # tokenize the query using sentence tokenization and word tokenization
    tokens=[word for sentence in nltk.sent_tokenize(query_term) for word in nltk.word_tokenize(sentence)]
    # remove stop words amongst the tokens
    tokens_without_stop_words=[token for token in tokens if token.lower not in stop_words]
    # apply stemming and case-folding
    stemmer=PorterStemmer()
    query_terms=[stemmer.stem(token).lower() for token in tokens_without_stop_words] # stemming and lower case
    return query_terms

def remove_punctuation_token(token):
    """
    Removes any commas or fullstops from a token

    Args:
        token (str): token in which punctuation is to be removed from
    
    Output:
        right_token (str): token with commas and fullstops removed
    """
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

def convert_query_to_vector(query_terms,dictionary,number_of_docs,stemmed_original_query):
    """
    Convert the query into vector, using (1+log(tf))*(log(N/df)) formula
    
    Args:
        query_terms: ([str]): list of tokens from query string, after undergoing various steps
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        number_of_docs (int):  number of documents in the dataset
    
    Output:
        vector_query ({str: float}): dictionary representing the query vector, with each key correlating to a dimension in the vector space
    """
    # remove terms that not appear in dictionary or vocabulary
    query_terms=[term for term in query_terms if term in dictionary] 
    if not query_terms:
        return None
    dict_query_terms=dict()
    # for each term, find its term frequency 
    for term in query_terms:
        dict_query_terms[term]=dict_query_terms.get(term,0)+1
    # apply the formula: (1+log(tf))*(log(N/df)) to each term 
    vector_query={term:(1+math.log(tf,10))*math.log(number_of_docs/dictionary[term][0],10) for term,tf in dict_query_terms.items()}
    vector_query={term:(score*10 if term in stemmed_original_query else score) for term,score in vector_query.items()}
    return vector_query