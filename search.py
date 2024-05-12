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
nltk.download('wordnet')
from nltk.corpus import wordnet
from nltk.util import bigrams


import config
from bool_search import handle_boolean_queries
from Dictionary import Dictionary
from PostingList import PostingsList
from free_text_search import handle_free_text_queries

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
    number_of_docs=load_data_from_memory(config.STORE_NUMBER_DOCS)
    
    # load dictionary of document length from memory
    dict_docids_to_length=load_data_from_memory(config.STORE_LENGTH_DOCS)
    
    # load dictionary of doc_ids to court
    dict_docids_to_court_info = load_data_from_memory(config.STORE_COURT_DOCS)

    with open(queries_file, 'r') as file:
        lines = file.readlines()
        # Do something with the file content
        print(f"processing query in file {queries_file}")
        # obtain query from file
        query=lines[0]
        
        # check query to determine which search to use
        if "AND" not in query:
            handle_free_text_queries(lines[0],dictionary,number_of_docs,posting_list,dict_docids_to_length,results_file,dict_docids_to_court_info)
        else: 
            # check the number of "AND" terms inside the query 
            temp_search_terms = query.split("AND")
            
            # if there is only one "AND" term, perform bool search
            if len(temp_search_terms) == 2:
                # perform bool search and return scores obtained from search
                scores = handle_boolean_queries(query,dictionary,posting_list,number_of_docs,dict_docids_to_length,results_file,dict_docids_to_court_info)
                
                # if number of documents found from bool_search exceeds 100, perform free text search on query instead
                if len(scores) > 100:
                    # convert bool query to free text query
                    new_query=convert_bool_free_text(query)
                    # perform free text search
                    handle_free_text_queries(new_query,dictionary,number_of_docs,posting_list,dict_docids_to_length,results_file,dict_docids_to_court_info)
            # if more than one "AND" term, perform free text search
            else:
                # convert bool query to free text query
                new_query=convert_bool_free_text(query)
                # perform free text search
                handle_free_text_queries(new_query,dictionary,number_of_docs,posting_list,dict_docids_to_length,results_file,dict_docids_to_court_info)
            
                
def convert_bool_free_text(bool_query):
    """
        method to convert bool query to free text query by replacing AND keywords and double quotation marks
    """
    bool_query=bool_query.replace("AND","")
    new_query=""
    for char in bool_query:
        new_query+=char if char!='"' else ""
    return " ".join(new_query.split())

def load_data_from_memory(filename):
    """
        load data structure or object from the hard disk
    """
    with open(filename,'rb') as file:
        return pickle.load(file)

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
