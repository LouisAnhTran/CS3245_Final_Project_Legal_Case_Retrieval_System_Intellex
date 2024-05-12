#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import os
from nltk.stem.porter import *
from nltk.corpus import stopwords
from collections import defaultdict
import pickle
import math
from nltk.tokenize import RegexpTokenizer
import csv
from nltk.util import bigrams
import string

import config
from Dictionary import Dictionary
from PostingList import PostingsList

STOP_WORDS=set(stopwords.words('english'))
VALID_SET=string.ascii_letters + string.digits

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    # create dictionary for indexing
    index_dict=dict()

    # store the total number of documents
    number_of_documents=0

    # dictionary to store length of all documents in the collection
    dictionary_doc_id_to_length=dict()

    # dictionary to store the court information of all documents
    dictionary_docids_to_court=dict()

    # set up size contrainst to read csv file
    if config.IS_TESTING:
        print("testing size: ",config.TESTING_SIZE)
    csv.field_size_limit(2147483647)

    # print("STOP WORDS: ",STOP_WORDS)
    
	# open the csv file
    with open(in_dir, encoding='utf-8') as csv_file:
        # read csv file
        csv_reader = csv.DictReader(csv_file)
        
        # for each document in csv file
        for each in csv_reader:

            # check if document id is of numeric value
            if each[config.DOCUMENT_ID].isdigit():

                # join content of some fields
                join_fields=join_text_from_fields(each)

                dictionary_docids_to_court[int(each[config.DOCUMENT_ID])]=each[config.COURT]

                # implement tokenization, stemming and case folding
                stemmed_tokens=tokenize_stemming_case_folding(join_fields)

                # remove all invalid tokens from the array of stemmed tokens
                stemmed_tokens=remove_invalid_tokens_from_list_of_tokens(stemmed_tokens)

                if not stemmed_tokens:
                    break 

                # increment total number of document by 1
                number_of_documents+=1

                # create this dictionary to keep track of term frequency of all terms in document
                term_to_frequency_for_doc=dict()

                # add unigrams to dictionary and update term frequency
                create_uni_gram(stemmed_tokens,index_dict,int(each[config.DOCUMENT_ID]),term_to_frequency_for_doc)

                # add bigrams to dictionary and update term frequency
                create_bi_gram(stemmed_tokens,index_dict,int(each[config.DOCUMENT_ID]),term_to_frequency_for_doc)

                # compute the length of document
                compute_document_length(term_to_frequency_for_doc,int(each[config.DOCUMENT_ID]),dictionary_doc_id_to_length)

                if config.IS_TESTING and number_of_documents==config.TESTING_SIZE:
                    break

    # sort the posting list in ascending order of document id
    index_dict={term:sorted([(docid,tf) for docid,tf in value.items()]) for term,value in index_dict.items()}


    # add skip pointers to every posting lists 
    for term in index_dict:
        doc_frequency=len(index_dict[term])
        number_of_skip_pointers=int(math.sqrt(doc_frequency))
        skip_pointing_size=int(doc_frequency/number_of_skip_pointers)

        for i in range(doc_frequency-skip_pointing_size):
            if i%skip_pointing_size==0 and i+skip_pointing_size<doc_frequency:
                index_dict[term][i]=(index_dict[term][i][0],index_dict[term][i][1],i+skip_pointing_size)


    # apply gap encoding for all posting list 
    gap_encoding_for_posting_list(index_dict)

    # print("index dict: ",index_dict)

    # instantiate dictionary object and posting list object
    dictionary_object=Dictionary(out_dict)
    posting_object=PostingsList(out_postings)

    # write out posting lists to hard disk
    posting_object.save_posting_to_disk(index_dict,dictionary_object)

    # write out dictionary to hard disk
    dictionary_object.save_dictionary_to_file()

    # write out number of documents to hard disk
    write_to_disk(config.STORE_NUMBER_DOCS,number_of_documents)

    # write out dictionary of documents id to length to hard disk
    write_to_disk(config.STORE_LENGTH_DOCS,dictionary_doc_id_to_length)

    # write out dictionay of document id to court information to hard disk
    write_to_disk(config.STORE_COURT_DOCS,dictionary_docids_to_court)

def gap_encoding_for_posting_list(dictionary):
    '''
        Method to implement gap encoding for posting list document id
    '''
    for term in dictionary:
        if len(dictionary[term])>1:
            first_doc_id=dictionary[term][0][0]
            accumulate=0
            for i in range(1,len(dictionary[term])):
                gap=dictionary[term][i][0]-first_doc_id
                gap-=accumulate
                dictionary[term][i]=(gap,dictionary[term][i][1])
                accumulate+=gap

def is_token_valid(token):
    for letter in token:
        if letter not in VALID_SET:
            return False
    return True

def remove_invalid_tokens_from_list_of_tokens(list_of_tokens):
    if not list_of_tokens:
        return None
    return [token for token in list_of_tokens if is_token_valid(token)]

def create_uni_gram(stemmed_token,index_dict,docid,dict_term_to_freq):
    '''
        add unigrams to dictionary and update the term frequency for document
    '''
    for term in stemmed_token:
        # if is_token_valid(term):
        if term not in index_dict:
            index_dict[term]={docid:1}
        else:
            index_dict[term][docid]=index_dict[term].get(docid,0)+1
        dict_term_to_freq[term]=dict_term_to_freq.get(term,0)+1
    
def create_bi_gram(stemmed_token,index_dict,docid,dict_term_to_freq):
    '''
        add bigrams to dictionary and update the term frequency for document
    '''
    # valid_stemmed_token=[token for token in stemmed_token if is_token_valid(token)]
    bi_grams=list(bigrams(stemmed_token))
    for bi_gram in bi_grams:
        if bi_gram not in index_dict:
            index_dict[bi_gram]={docid:1}
        else:
            index_dict[bi_gram][docid]=index_dict[bi_gram].get(docid,0)+1
        dict_term_to_freq[bi_gram]=dict_term_to_freq.get(bi_gram,0)+1

def remove_cjk(text):
    # Unicode ranges for Chinese, Japanese, and Korean characters
    pattern = r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff66-\uff9f\u3131-\uD79D]'
    return re.sub(pattern, '', text)

def write_to_disk(file_name,dict_docid_to_court):
    with open(file_name,'wb') as file:
        pickle.dump(dict_docid_to_court,file)
    file.close()

def compute_document_length(term_dict: dict,docid,length_d):
    """
        compute the lenght for given document
    """
    length_d[docid]=math.sqrt(sum([(1+math.log(val,10))**2 for val in term_dict.values()]))
    return length_d[docid]

def join_text_from_fields(row):
    return " ".join([row[config.TITLE],row[config.CONTENT],row[config.DATE_POSTED],row[config.COURT]])

def tokenize_stemming_case_folding(input_str):
    if not input_str:
        return None
    # tokenize the document content using sentence tokenization and word tokenization
    tokens=[token for sent in nltk.sent_tokenize(input_str) for token in nltk.word_tokenize(sent)] 
    # remove all stop words from the list of tokens
    tokens_with_no_stop_words=[token for token in tokens if token.lower() not in STOP_WORDS]
    # apply stemming and case folding
    stemmer = PorterStemmer()
    stemmed_and_case_folded_tokens=[stemmer.stem(token).lower() for token in tokens_with_no_stop_words]
    return stemmed_and_case_folded_tokens

def load_number_of_documents_to_disk(file_name,number_of_document):
    """
        write out the number of documents within the collection to hard disk
    """
    with open(file_name,'wb') as file:
        pickle.dump(number_of_document,file)

def load_length_documents_to_disk(file_name,length_N_dict):
    """
        write out the length of all documents to hard disk
    """
    with open(file_name,'wb') as file:
        pickle.dump(length_N_dict,file)

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
