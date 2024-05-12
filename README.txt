This is the README file for A0290532J, A0233054R, A0214947X's submission
Email(s): e1325138@u.nus.edu, e0725054@u.nus.edu, e0533998@u.nus.edu

== Python Version ==

We are using Python Version <3.10.7> for this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps in your program, and discuss your experiments in general.  A few paragraphs are usually sufficient.

The entire program is composed of two main parts, namely indexing and seaching and each part contain various helper functions to implement required algorithms and logics. In this section, we will provide detailed used algorithms and steps for both parts

I. INDEXING:

The purpose of indexing is to create a dictionary of all terms within collection which contains correct pointers pointing to posting lists stored in the hard disk. In addition to dictionary of terms and posting lists, we also created a dictionary to store length of documents for VSM, a dictionary that store court information for each document. 

If the indexing algorithm is implemented correctly, we would write out 5 entities to hard disk. The data structure for each entity is shown below:

Dictionary:  {term:(document_frequency,pointer_to_poiting_list),...}

Posting List for a specific term: [..,(doc_id,term_frequency,skip_pointer),..], tuple elements in posting list are sorted in the ascending order of document id.

Dictionary for document length: {doc_id: length} 

Dictionary for court information: {doc_id: court_information}

Number of documents in the collection: integer value

Note: 
+ Since we are required to deal with boolean queries which contain pharases, we decided to add bigrams to our indexing step (positional list was dismissed due to potential expansion of posting list). This will lead to the dictionary containing both unigram and bigrams as keys. Hence, the dictionary combining unigrams and bigrams will have the following structure:

{term:(document_frequency,offset)} => for unigram 
{(term1,term2):(document_frequency,offset)} => for bigrams

+ Instead of indexing documents in text file format, we will read csv file to build the index for this assignment. There are 5 fields in the csv file, namely "document_id","title","content","date_posted","court". We decided to merge content of the last 4 fields, namely "title", "content", "date_posted" and "court" for indexing and the information from court will be used later for ranking documents during searching. 

We are given the court hierarchy which classifies courts by importannce, which we can make use for ranking relevant documents during searching. After we obtain the documents score for a given query, we will adjust the score based on the court information as belows:

for document with most important court: updated score = old score * 1.1
for document with important court:      updated score = old score * 1.05
for others:                             updated score = old score        

Indexing steps:

1. for each document, consolidate content from 3 fields, namely "title", "content", "date_posted", "court"
2. insert the court information of the current document to dictionary
3. increment the total number of document by 1
4. remove stop words from merged text
5. implement Tokenization, Stemming, Case fording for merged text after removal of stop words.
6. populate the dictionary with unigrams, keep track of the term frequency for documents
7. populate the dictionary with bigrams, keep track of the term frequency for documents.
8. calculate the document length and store it in the document length dictionary
9. finalize the dictionary structure, with the value being the posting list with elements sorted in ascending of document ids.
10. add skip pointers to all posting lists to perform AND operation for boolean queries during searching stage. 
11. write out posting list, dictionary of unigrams and bigrams, dictionary of documents lengths, dictionary of document's court information, total number of documents to hard disk. 

The detailed implementation of some main steps can be found below.

1. Tokenization, Stemming, Stop Word Removal:
   - Initialize a variable for the dictionary of terms, denoted as D.
   - Initialize a variable to keep track of the length for documents, denoted as D1.
   - Initialize a variable to keep track of total documents, denoted as N.
   - For each document, perform the following steps:
     + Increment N by 1.
     + Initialize a dictionary to keep track of occurrences for each term in the document, denoted as D2, which will be used to calculate the length for the document vector.
     + Obtain the list of tokens using `sent_tokenize` and `word_tokenize` provided by NLTK.
     + Retrieve the list of stop words from NLTK.
     + Create a new list of tokens using list comprehension and applying these conditions: a token must not be in the stop word list, apply stemming, and case-folding to reduce the token to its lowercase form.
     For unigram:
     + Once a list of tokens is obtained in accordance with the requirements, iterate through each token. For each token, perform the following steps:
       - If the token is not in the dictionary, add this token to dictionary D as a key, with the value being {docid: 1}.
       - Otherwise, update the term frequency of this term for the given docid.
       - Update the term frequency in the current docid in D2.
     For bigrams:
     + Create an array of bigrams from the list of tokens, and for each token, perform the following step:
       - If the token is not in the dictionary, add this token to dictionary D as a key, with the value being {docid: 1}.
       - Otherwise, update the term frequency of this term for the given docid.
       - Update the term frequency in the current docid in D2.
     + Compute the document length d based on D2 and add the docid to D1 as a key and its corresponding value for document length as d.
     Note: document length is given by this formula: math.sqrt((1+log(tf1))^2 + (1+log(tf2))^2 ... + (1+log(tf2))^n ), for all unigrams and bigrams appear in document.
   - Update D by implementing sorting for the posting list by docid in dictionary D.

2. Writing out Dictionary and Posting Lists to Hard Disk:
   - Instantiate a dictionary object from the Dictionary class.
   - Instantiate a posting list object from the PostingList class.
   Notice: The dictionary to be loaded into memory for searching will look like: `{docid: (document_frequency, offset or pointer)}`, where the offset is the pointer to the corresponding posting list on the hard disk.
   - Iterate through all terms in dictionary D from part 1. For each term:
     + Get the current pointer on the hard disk.
     + Retrieve the posting list from the dictionary D.
     + Add the term to the dictionary as the key, with values being a tuple containing document frequency and a pointer to the posting list.
     + Write out the pointing list to the hard disk.
   - At this point, we have successfully constructed the dictionary, with each term having a pointer to its respective posting list on the hard disk. Then, write out the term dictionary, document length dictionary as well as the number of documents to the hard disk to complete the indexing phase.

II. INDEXING COMPRESSION IMPLEMENTATION / CONSTRAINT ON INDEX:

The first round of indexing without adopting any compression techniques on the dictionary and posting results in sizes of 215MB and 800MB for the dictionary and posting list, respectively. The total size of the submission substantially exceeds the maximum size allowed, which pushes us towards implementing several compression techniques covered in the lecture to cut down on the submission size.

Since the size was predominantly occupied by the posting list, we were only performing compression on the posting list. The techniques used are as follows:

1. Remove stop words using NLTK.
2. Gap encoding for the posting list.

Posting list before gap encoding: [(246391, 2, 4), (246400, 1), (246403, 2), (246404, 5), (246407, 2), (246417, 1), (246427, 1), (246436, 1)]

Posting list after gap encoding: [(246391, 2, 4), (9, 1), (3, 2), (1, 5), (3, 2), (10, 1), (10, 1), (9, 1)]

After implementing the combination of stop word removal and document ID gap encoding for the posting list, we have successfully reduced the dictionary size to 204MB and the posting list size to 582MB. Along with other files, the total submission size before zipping is less than 800MB, which complies with the requirement.

II. SEARCHING:

Do note that in this section, query expansion via nltk.wordnet was used as the method of query refinement.

For each query from the given query file, we will perform the following steps:

1. Identifying type of Query (boolean or free text query):
   - Our 1st check is to determine if the query contains the keyword "AND". 
      - If query does not contain "AND", it will be a free text query.
   - Even if query contains "AND", we might not process it as a bool query. We use the following heuristic to guide us:
      - Check the number of "AND" keywords in the query
         - If number of "AND" is greater than 1, treat it as a free text query instead
   - After performing the bool query, we check if the number of documents returned is > 100.
      - If number of documents returned is > 100, we treat the query as a free text query instead and perform free text search on the query
   - Do refer to the remarks section for greater detail

2a. Handling boolean queries:
   - Preprocessing of query string with the following actions 
      - splitting query string by keyword "AND" to obtain an array of search terms
      - removing leading and trailing whitespaces for each search term
      - removing any double quotation marks from search terms
   - Find intersection of doc_ids by iterating over all search terms with the following process
      - If performing query expansion 
         - Obtain all synonyms for each word/phrase with wordnet (if applicable)
            - replace all underscores with whitespace (if applicable)
         - perform preprocessing for each word / phrase - setence tokenization, word tokenization, stemming, case folding (see 3a)
         - breakdown phrase to bigrams (if applicable)
         - search for unigram/bigram in dictionary and obtain offset to seek in posting list
            - obtain gap encoded posting list and decode
         - Find intersection between posting list of bigrams (if applicable)
            e.g. for a phrase of "C D E", the search performs "C D" ^ "D E"
         - Find Union between synonyms of a single term
            - e.g. for the given query of A ^ B ^ "C D", the search performs (A1 U A2 U A3) ^ (B1 U B2 U B3) ^ "C D E" 
         - Find final intersersection between all terms in query
      - Without query expansion
         - perform preprocessing for each word / phrase - setence tokenization, word tokenization, stemming, case folding (see 3a)
         - breakdown phrase to bigrams (if applicable)
         - search for unigram/bigram in dictionary and obtain offset to seek in posting list
            - obtain gap encoded posting list and decode
         - Find intersection between posting list of bigrams (if applicable)
            e.g. for a phrase of "C D E", the search performs "C D" ^ "D E"
         - Find final intersersection between all terms in query
   - Perform scoring with the lnc.ltc ranking scheme (ddd.qqq)
      - Obtain tf-idf weight for query and perform cosine normalization (see 3b)
      - Obtain log_tf weight for documents and perform cosine normalization (see 3c)
      - Apply court weight multiplier, based on the court that the doc_id is associated with. More important courts get a higher multiplier 
   - Rank Results in descending order before writing to file (see 3d)

2b. Handling free text queries: 
   - Perform preprocessing 
      - Query expansion to find all its terms' synonyms using the WordNet database
      - Perform tokenization and sanitization of query (see 3a)
      - For each word: setence tokenization, word tokenization, stemming, case folding
   - Perform scoring with the lnc.ltc ranking scheme (ddd.qqq)
      - Obtain tf-idf weight for query and perform cosine normalization (see 3b)
      - Obtain log_tf weight for documents and perform cosine normalization (see 3c)
      - Apply court weight multiplier, based on the court that the doc_id is associated with. More important courts get a higher multiplier 
   - Rank results in descending order before writing to file (see 3d)

--FURTHER DESCRIPTION OF STEPS--

3a. Tokenizing and Sanitizing the Query:
   - Tokenize the given query.
   - For each term in the query, remove leading and trailing punctuation such as commas and periods.
   - Return a tokenized and sanitized query.

3b. Convert Query to Vector:
   - Create a dictionary from the query with keys being the terms and values being their occurrences in the query.
   - Read the number of documents from the memory, denoted as N.
   - Iterate through every key in the dictionary and update its corresponding value using the given formula: (1+log(tf))*log(N/df)
   - Return a query vector.

3c. Calculating the Score:
   - Initialize the dictionary to store documents and their corresponding scores.
   - Iterate through each term in the query.
   - For each term, do the following steps:
     - Load the posting list from memory using the offset.
     - Iterate through every document in the posting list. For each document, do the following steps:
       - Update the document score in the dictionary using the given formula: {dictionary}[doc_id] = w(t,d)*w(t,q), where w(t,d) = 1+log({term\_frequency}) and w(t,q) is the value of the key term from the query vector.
   - After the for loop terminates, we get the dictionary keeping track of unnormalized scores for all documents.
   - To do normalization, we load the document length created during the indexing phase from memory. We take the unnormalized score of the document ID and divide it by the corresponding document length to obtain the normalized score.
   - At this stage, we successfully calculate the normalized score for all document IDs for the given query.

3d. Return Documents sorted by Highest Score:
   - The algorithm for this is straightforward, and the steps are explained properly in the code and functions.
   - The detail will not be covered here because it is not part of the requirements.
   - If two documents have the same score, the document with the smaller ID will be ranked higher in the output result.

Remarks: This section below will discuss how our searching implementation of free text queries and boolean queries adapts to obtain the optimal score for F2 and MAF2.

1. Free text search approaches:
+ Approach 1.0: Perform query expansion without special treatment for terms in orinal query.
   The result of this approach turns out to be bad due to a couple of reasons. Firstly, we conducted query expansion using Wordnet and in many cases, Wordnet return a list of synonyms which are not consist and align with the context given in the original query. More importantly, some of synonyms accidentially posses higher weight than terms in original query, as a result, the irrelavant docs appear in early in the returned result, whereas the relevant ones appear much later in the result.
+ Approach 2.0: Switch off query expansion implementation:
   To tackle the issues pointed in the previous approach, we experimented with switching off the query expansion and as a result, the relevant docs appear much early in the returned result. However, the number of docs in the output was also significantly fewer as oppose to when query expansion is on.
+ Approach 3.0: Perform query expansion with special treatment for terms in original query
   To address both issues discovered in the first two approaches, we decided to continue using query expansion and performance additional steps to make sure the original terms appearing in the query should be given more priority. What we did was after we converted the query into the vector with weight for each terms, we update the terms weight accordingly such that weights for terms in original query will be adjusted, given the formula: new_weight=old_weigth*10, while the weights for all other terms that do not appear in original query remain unchanged. 
   => With this approach, we managed to gain the better performance through the improved scores of F2 and MAF2. 

2. Boolean query approaches:
- The process of determining which search method (bool search or free text search) to apply is not straightforward.
   - Initially, we used the simple rule, where bool search was applied to all queries with the keyword "AND". Hoewver, we soon realised that there are cases of inaccurate documents returned or no documents returned at all (0 F2 score).
   - To tackle the issue of no documents being returned at all, we decided that free text search would be beneficial, given that it imposes less stringent conditions and more documents could be returned.
   - The heuristic of counting number of "AND" inside a query, as well as the number of documents returned from bool search were selected as follows:
      - We believed that if the number of "AND" keywords was greater than 1, chances of returning a relevant document was low with the increasing amount of conditions. We explored the usage of query expansion with wordnet, but it did not improve our F2 score.
         - Additionally, we felt that it would be reasonable if such queries, which are longer in nature, are treated as free text queries.
      - The number of documents returned from bool queries, 100, was selected as an addditional criteria. This is due to an assumption that we make about performing bool search.
         - We assume that bool search should return a small amount of documents, as the query is meant to return precise information. If the query return a large number of documents, free text search would be preferred as it has the potential to return documents with higher relevance with the less stringent conditions. 
- We decided to not include query expansion into the final submission as we did not find the trade-off between computational cost and evaluation score (mean F2) to be worth it.
   - For boolean queries, a search using q3.txt on our local machine returned the following:
      - Without query expansion, a mean F2 score of 0.5594541910331383, with 0:00:00.458365 time taken
      - With query expansion, a mean F2 score of 0.565126050420168, with 0:00:13.366596 time taken
   - Due to a significant increase in time taken for queries without significant improvement to F2 score, we decided to opt out of performing query expansion.
- Using intersection in bigrams
   - For any phrase that we need to search for in boolean queries, we break down the phrase into bigrams, and look for doc_ids that appear in the intersection of the respective posting list of each bigram
   - This is important as the phrase in the query is meant to be exact, and we need to ensure that only documents that contain all bigrams are returned.
- Using Union in process of obtaining relevant doc_ids in wordnet
   - As mentioned above, we perform an intersection between each word/phrase for the boolean query (A ^ B ^ "C D")
   - However, when we use wordnet to expand the query, we perform (A1 U A2 U A3) ^ (B1 U B2 U B3) ^ "C D"
   - We decided to go with Union as these synonyms are meant for the original term, and in doing so would expand the total number of documents that represented the initial term.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

In order to implement Indexing and Searching tasks, I have created a couple of files for storing intermediarty data.

index.py: Contain logic for carrying out the indexing implementation.
search.py: Contain logic for performing searching implementation for boolean and free text queries.
config.py: Contains constants and common variables that are used in the indexing and seraching process.
bool_search.py: Contain the logic for performing search on boolean queries
free_text_search.py: Contain the logic for performing search on free text queries. 
dictionary.txt: A file to store the dictionary on the hard disk.
postings.txt: A file to store posting lists on the hard disk.
number_of_documents.txt: Stores the number of documents in the collection after the indexing phase for idf calculation.
length_documents.txt: Stores the dictionary with the key being the document ID and the value being the corresponding length of the document vector.
dict_docid_to_court.txt: Store the dictionary with the key being the document id and values being corresponding court information from court field
Dictionary.py: A class defined to manage dictionary operations, storage, writing to the hard disk, and loading from the hard disk to memory for searching.
PostingList.py: A class defined to manage PostingList objects in a standardized and organized manner for operations such as writing out posting lists to the hard disk, and reading in a posting list for a specific term from the hard disk to memory for searching.
README.txt: Provides additional information about the assignment, such as algorithm and steps elaboration, submitted files, student declaration, references, etc.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0290532J, A0233054R, A0214947X certify that we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] We, A0290532J, A0233054R, A0214947X did not follow the class rules regarding homework
assignment, because of the following reason:

This part is not applicable to us because we adhered strictly to the course policy, assignment guidelines, and class rules in order to complete this assignment.

We suggest that we should be graded as follows:

Code correctness, readability, and scalability
Adherence to submission instructions and guidelines
Accurate application and implementation of concepts and algorithms covered in lectures.

== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>

Learning pickle: 
1. https://docs.python.org/3.7/library/pickle.html

NLTK Documentation:
2. https://www.nltk.org/

Removing of Chinese Japanese and Korean words
3. https://stackoverflow.com/questions/43418812/check-whether-a-string-contains-japanese-chinese-characters

Previous HW assignments
4. We referenced some portions of our code from previous assignments to implement certain functions. (E.g. ranking and scoring of vectors via lnc.ltc scheme)