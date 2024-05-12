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
from datetime import datetime

import config

STOP_WORDS=set(stopwords.words('english'))

def expand_query_with_wordnet_for_bool_query(gram):
    """Method to expand query using wordnet for boolean queries
    If there exists synonyms, the synonyms will exist in the list of words returned

    Args:
        gram (str): word or phrase obtained from the query

    Returns:
        synonyms ([str]): list of words that are synonyms to the word or phrase provided
    """
    # initialise synonyms variable
    synonyms = []
    
    # obtain synonums for gram
    for syn in wordnet.synsets(gram):
        synonyms.extend(syn.lemma_names())
    
    # casefolding for all synonyms obtain
    synonyms=list(set([term.lower() for term in synonyms]))
    return synonyms

def gap_decoding_posting_list(posting_list):
    """Void method that performs gap decoding of posting list to obtain accurate values
    Except for the first node, every doc_id in the posting list nodes is the offset value from the node before it

    Args:
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
    """
    # check if posting list is of length 1
    if len(posting_list) == 1:
        return
    
    # initialize accumulate variable
    accumulate = posting_list[0][0]
    
    # iterate over remainig nodes of posting list
    for node_idx in range(1, len(posting_list)):
        # calculate actual doc_id
        decode_doc_id = accumulate + posting_list[node_idx][0]
        
        # check if skip pointer exists in posting list
        if len(posting_list[node_idx]) > 2:
            posting_list[node_idx]=(decode_doc_id, posting_list[node_idx][1], posting_list[node_idx][2])
        else:
            posting_list[node_idx]=(decode_doc_id, posting_list[node_idx][1])
        
        # update accumulate variable
        accumulate = decode_doc_id

def tokenize_stemming_case_folding(input_str):
    """
    same method as the one in indexing 
    """
    # tokenize the document content using sentence tokenization and word tokenization
    tokens=[token for sent in nltk.sent_tokenize(input_str) for token in nltk.word_tokenize(sent)] 
    # remove all stop words from the list of tokens
    tokens_with_no_stop_words=[token for token in tokens if token.lower() not in STOP_WORDS]
    # apply stemming and case folding
    stemmer = PorterStemmer()
    stemmed_and_case_folded_tokens=[stemmer.stem(token).lower() for token in tokens_with_no_stop_words]
    return stemmed_and_case_folded_tokens

def get_documents_for_term(tokens, words_in_vector_dict, dictionary, posting_list):
    """Method to retrieve document_ids for each term with or without expanding the query.
    If tokens is a phrase, we seek out the intersection between the bigrams in the phrase
    
    If we need to expand the query, it will be done with wordnet, and applied on all the tokens possible. 
    We weekd the union between posting lists for each addtional token.

    Args:
        tokens (string): A string that represents a portion of the query, could be a single word or a phrase
        words_in_vector_dict ({str: int}): words inside a query reprsented by dictionary of key - term, val - freq
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer

    Returns:
        output ([int]): list of doc_ids which are present across all terms
        words_in_vector_dict ({str: int}): words inside a query reprsented by dictionary of key - term, val - freq 
    """
    if config.EXPAND_QUERY:
        # intialise new tokens array
        new_tokens = []
        
        # expand query with additional terms from wordnet
        worndnet_terms = expand_query_with_wordnet_for_bool_query(tokens)
        
        # validate if expansion was successful
        if len(worndnet_terms) > 0:
            new_tokens.extend(worndnet_terms)
        else:
            new_tokens.append(tokens)
        
        # initialise output array 
        ouptut = []
        
        # iterate over tokens for search
        for new_token in new_tokens:
            # replace underscore from wordnet with white space
            new_token = new_token.replace("_", " ")
            
            # stem tokens
            stem_tokens = tokenize_stemming_case_folding(new_token)
            
            # check if phrase is obtained by checking for bigrams
            bi_grams = list(bigrams(stem_tokens))
        
            # get array of tokens to search for
            final_tokens = bi_grams if len(bi_grams) > 0 else stem_tokens 
            
            # initialize intersection arr
            intersection_between_final_tokens = []

            # iterate over tokens to search for
            for term in final_tokens:
                
                # check if term exists in dictionary
                if term in dictionary.keys():
                    # obtain offset for seeking posting list
                    term_dict_pair = dictionary[term]
                    term_offset = term_dict_pair[1]
                    
                    # obtain posting list
                    term_posting_list = posting_list.load_posting_from_disk(term_offset)
                    
                    # gap decoding of posting list
                    gap_decoding_posting_list(term_posting_list)
                    
                    # get list of doc_ids inside posting list
                    term_doc_ids = [tup[0] for tup in term_posting_list]
                    
                    # find intersection between current list of doc_ids and doc_ids for bigrams
                    if len(intersection_between_final_tokens) > 0:
                        intersection_between_final_tokens = list(set(intersection_between_final_tokens) & set(term_doc_ids))
                    else:
                        intersection_between_final_tokens = term_doc_ids
                    
                    # manage term frequency in query
                    if term in words_in_vector_dict.keys():
                        words_in_vector_dict[term] += 1
                    else:
                        words_in_vector_dict[term] = 1

            # perform union between all synonyms from wordnet
            ouptut = list(set(ouptut) | set(intersection_between_final_tokens))  
        return ouptut, words_in_vector_dict
    
    else:
        # stem tokens
        stem_tokens = tokenize_stemming_case_folding(tokens)
        
        # check if phrase is obtained by checking for bigrams
        bi_grams=list(bigrams(stem_tokens))
        
        # get array of tokens to search for
        final_tokens = bi_grams if len(bi_grams) > 0 else stem_tokens 
        
        # initialize output
        output = []
        
        # iterate over tokens to search for
        for term in final_tokens:
            
            # check if term exists in dictionary
            if term in dictionary.keys():
                # obtain offset for seeking posting list
                term_dict_pair = dictionary[term]
                term_offset = term_dict_pair[1]
                
                # obtain posting list
                term_posting_list = posting_list.load_posting_from_disk(term_offset)
                
                # gap decoding of posting list
                gap_decoding_posting_list(term_posting_list)
                
                # get list of doc_ids inside posting list
                term_doc_ids = [tup[0] for tup in term_posting_list]
                
                # find intersection between current list of doc_ids and doc_ids for bigrams
                if len(output) > 0:
                    output = list(set(output) & set(term_doc_ids))
                else:
                    output = term_doc_ids

                # manage term frequency in query
                if term in words_in_vector_dict.keys():
                    words_in_vector_dict[term] += 1
                else:
                    words_in_vector_dict[term] = 1
                
        return output, words_in_vector_dict
    
def get_length_of_vector(vector):
    """method to obtain length of vector

    Args:
        vector ([float]): list of weights

    Returns:
        length_of_vector (float): length of vector 
    """
    # initialize square_sum_of_all_vector_values variable 
    square_sum_of_all_vector_values = 0
    
    # iterate over values in vector
    for val in vector:
        # square each value and add to square_sum_of_all_vector_values
        square_sum_of_all_vector_values += val ** 2
    
    # obtain length from square root of square_sum_of_all_vector_values
    length_of_vector = math.sqrt(square_sum_of_all_vector_values)
    
    return length_of_vector
        
def normalize_vector(vector):
    """method that normalizes vectors to their unit vectors
    
    Args:
        vector ([float]): arr of floats
    
    Output:
    - norm_vector ([float]): arr of floats
    """
    
    # get length of vector
    length_of_vector = get_length_of_vector(vector)
    
    # check for zero to avoid zero error
    if length_of_vector == 0:
        return None
    
    # initialise norm_vector that is the same length as vector
    norm_vector = [0] * len(vector)
    
    # normalize each value and set it in norm_vector
    for idx in range(0, len(vector)):
        curr_val = vector[idx]
        norm_vector[idx] = curr_val / length_of_vector
    
    return norm_vector

def get_doc_term_log_tf(doc_id, posting_list):
    """generate document log_tf for term
    
    Args:
        gram (str): unigram or bigram
        doc_id (int): document_id
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer

    Returns:
        log_tf_val (float): log_tf_val
    """
    # iterate over all tuples in posting list to perform linear search
    for tup in posting_list:
        if doc_id == tup[0]:
            term_freq_in_doc = tup[1]
            # obtain log_tf_val
            log_tf_val = 0 if term_freq_in_doc == 0 else 1 + math.log10(term_freq_in_doc)
            
            return log_tf_val
    
    return 0

def get_sorted_results(intersection, words_in_vector_dict, normalized_query_vector, dictionary, posting_list, dict_docids_to_length, dict_docids_to_court):
    """Generate normalized document vectors for each document id, where each document vector is of same length as words_in_vector_dict
    Apply the lnc scheme for each document vector, and caluclate the total score with between the document vector and normalized_query_vector
    
    Args:
        intersection ([int]): array of document ids that contain all the terms queried
        words_in_vector_dict ({str: int}): words inside a query reprsented by dictionary of key - term, val - freq
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
        dict_docids_to_length ({int : float}): dictionary of key - doc_id, val - length
        dict_docids_to_court ({int : str}): dictionary of key - doc_id, val - court name
    
    Output:
        sorted_results ([(int, float)]): array of tuple (doc_id, score) that is sorted in descending order
    """
    # get grams in query
    query_vector = [key_val_pair[0] for key_val_pair in words_in_vector_dict.items()]
    #print(f"query_vector in gndv func is {query_vector}")
    
    # initialize a list to hold the total_score for each doc, default value of 0
    doc_scores = [0] * len(intersection)
    
    # create a dictionary to store mapping from document_ids to index in the sorted list, keys - doc_id, val - index
    doc_id_to_index = {}
    index = 0
    
    # store mapping in doc_id_to_index
    for doc_id in intersection:
        doc_id_to_index[doc_id] = index
        index += 1
    
    # iterate over each gram
    for gram_idx in range(len(query_vector)):
        gram = query_vector[gram_idx]
        
        # get posting list for gram
        if gram in dictionary.keys():
            term_dict_pair = dictionary[gram]
            term_offset = term_dict_pair[1]
            
            # load posting list from disk
            term_posting_list = posting_list.load_posting_from_disk(term_offset)
            
            # gap decoding of posting list
            gap_decoding_posting_list(term_posting_list)
            
            # iterate over each doc_id
            for doc_id in intersection:
                # get log_tf of gram in doc
                log_tf_of_term_in_doc = get_doc_term_log_tf(doc_id, term_posting_list)
                
                # get length of document
                length_of_doc = dict_docids_to_length[doc_id]
                
                # get normalized weight
                #doc_vector[gram_idx] = log_tf_of_term_in_doc / length_of_doc
                gram_weight = log_tf_of_term_in_doc / length_of_doc
                
                # calculate partial weight
                doc_scores[doc_id_to_index[doc_id]] += gram_weight * normalized_query_vector[gram_idx]
    
    # initialize array to hold the pair of doc_id and total_score 
    results = []
    
    # store results in the array
    for doc_id in intersection:
        # get index of of doc_scores from dict of doc_id_index
        temp_doc_id_index = doc_id_to_index[doc_id]
        
        # get court from dict
        court_name = dict_docids_to_court[doc_id]
        
        # get court importance weight
        court_importance_weight = 1
        if court_name in config.COURT_MOST_IMPORTANT:
            court_importance_weight = config.WEIGHT_MOST_IMPORTANT
        elif court_name in config.COURT_IMPORTANT:
            court_importance_weight = config.WEIGHT_IMPORTANT
        
        # get total score from index, inclusive of court importance weight
        total_score = doc_scores[temp_doc_id_index] * court_importance_weight
        
        # add tuple to results
        results.append((doc_id, total_score))
    
    # sort the results by total_score in descending order
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    
    return sorted_results

def apply_ltc_scheme(words_in_vector_dict, dictionary, number_of_docs):
    """ apply ltc scheme to query, log-tf, idf, cosine normalization

    Args:
        words_in_vector_dict ({str: int}): words inside a query reprsented by dictionary of key - term, val - freq
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        number_of_docs (int): number of documents in training corpus, used for calculating IDF

    Returns:
        normalized_query_tf_vector ([float]): array of normalized_tf_idf_weights
    """
    # initialise vector from dict key value pairs
    query_vector = [key_val_pair[0] for key_val_pair in words_in_vector_dict.items()]
    query_tf_vector = [key_val_pair[1] for key_val_pair in words_in_vector_dict.items()]
    
    # intialise vector for storing tf-idf weights
    query_tf_idf_vector = [0] * len(query_tf_vector)
    # convert from raw_term_freq to tf-idf
    for idx in range(len(query_tf_vector)):
        # get log_tf
        val = query_tf_vector[idx]
        log_tf_val = 0 if val == 0 else 1 + math.log10(val)
        
        # get idf val
        doc_freq = dictionary[query_vector[idx]][0] if query_vector[idx] in dictionary.keys() else 0
        idf_val = math.log10(number_of_docs / doc_freq) if doc_freq > 0 else 0
        
        # store tf-idf weight
        query_tf_idf_vector[idx] = log_tf_val * idf_val
    
    # normalize vector
    normalized_query_tf_vector = normalize_vector(query_tf_idf_vector)
    return normalized_query_tf_vector
    
def calculate_scores(intersection, words_in_vector_dict, dictionary, posting_list, number_of_docs, dict_docids_to_length, dict_docids_to_court):
    """This method follows the lnc.ltc ranking scheme
    We apply ltc scheme for queries, and lnc for documents, before obtaining scores.

    Args:
        intersection ([int]): array of doc_ids that contain all the terms specified in a boolean query
        words_in_vector_dict ({str : int}): dictionary of unigram/bigram and raw_term_frequency in query
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
        number_of_docs (int): total number of documents
        dict_docids_to_length ({int : float}): dictionary of key - doc_id, val - length
        dict_docids_to_court ({int : str}): dictionary of key - doc_id, val - court name
    
    Output:
        sorted_results ([(int, float)]): array of tuple (doc_id, score) that is sorted in descending order
    """
    # term freq to log_tf, document freq to idf, normalization
    normalized_query_vector = apply_ltc_scheme(words_in_vector_dict, dictionary, number_of_docs)
    
    # get sorted results
    sorted_results = get_sorted_results(intersection, words_in_vector_dict, normalized_query_vector, dictionary, posting_list, dict_docids_to_length, dict_docids_to_court)
    
    return sorted_results

def format_results(sorted_results):
    """Method to format results before writing to file

    Args:
        sorted_results ([(int, float)]): array of tuple (doc_id, score) that is sorted in descending order

    Returns:
        str_output (str): string of all doc_ids in sorted results joined by whitespace
    """
    # obtain all doc_ids
    sorted_doc_ids = [str(temp_tup[0]) for temp_tup in sorted_results]
    
    # join all doc_ids with whitespace
    str_output = ' '.join(sorted_doc_ids)
    return str_output
    
def handle_boolean_queries(query, dictionary, posting_list, number_of_docs, dict_docids_to_length,results_file,dict_docids_to_court):
    """perform search on boolean queries

    Args:
        query (str): query to perform search on
        dictionary ({str : (int, int)}}): dictionary of key - term, val - (freq, offset)
        posting_list ([(doc_id, tf, ?skip_pointer)]): array of tuples containing doc_id, term freq, skip pointer
        file_name (str): output file name
        number_of_docs (int): total number of documents
        dict_docids_to_length ({int : float}): dictionary of key - doc_id, val - length
        dict_docids_to_court ({int : str}): dictionary of key - doc_id, val - court name
    Output:
        scores ([(int, float)]): array of tuple (doc_id, score) that is sorted in descending order
    """
    
    # split query by the command AND
    search_terms = query.split("AND")
    
    # remove leading and trailing whitespace for each term in search_terms
    cleaned_search_terms = [term.strip() for term in search_terms]
    
    # remove double quotation marks from each term
    replaced_quotes_for_terms = [term.replace('"', '') for term in cleaned_search_terms]
    #print(f"terms after replacing quotations {replaced_quotes_for_terms}")
    
    # initialise intersection array for storing doc_ids
    intersection = []
    
    # initialise words_in_vector_dict, with key - term, val - freq
    words_in_vector_dict = {} 
    
    # iterate over each term in replace_quotes_for_terms
    for searches in replaced_quotes_for_terms:
        # obtain document ids for each term
        search_res, words_in_vector_dict = get_documents_for_term(searches, words_in_vector_dict, dictionary, posting_list)
        
        # perform intersection between list of document ids retrieved
        if len(intersection) > 0:
            intersection = list(set(intersection) & set(search_res))
        else:
            intersection = search_res
    
    # calculate scores based on the lnc.ltc scheme
    scores = calculate_scores(intersection, words_in_vector_dict, dictionary, posting_list, number_of_docs, dict_docids_to_length, dict_docids_to_court)
    
    # format scores to write to file
    query_output = format_results(scores)
    
    # write results to file
    with open(results_file,'w') as out_file:
            out_file.write(query_output+"\n")
    
    # return scores
    return scores