#!/usr/bin/env python3

# pip3 install sentencepiece
# pip3 install spacy
# python3 -m spacy download en_core_web_sm
# pip3 install torch
# pip3 install transformers
# pip3 pip3 install --upgrade pip
# pip3 install git+https://github.com/deepset-ai/haystack.git#egg=farm-haystack[colab]

import logging
import sys
from haystack.utils import launch_es
import time
import os

from haystack.utils import convert_files_to_docs
from haystack.nodes import BM25Retriever
from haystack.nodes import FARMReader
from haystack.pipelines import ExtractiveQAPipeline

from nltk.corpus import wordnet
import spacy

#
# wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.9.2-linux-x86_64.tar.gz -q
# tar -xzf elasticsearch-7.9.2-linux-x86_64.tar.gz
# chown -R daemon:daemon elasticsearch-7.9.2

DEBUG = False
USE_LOCAL_MODELS = False
######## get semantic negation for similarity calculation
def Negation(sentence):
  '''
  Input: Tokenized sentence (List of words)
  Output: Tokenized sentence with negation handled (List of words)
  '''
  temp = int(0)
  for i in range(len(sentence)):
      if sentence[i-1] in ['not',"n't"]:
          antonyms = []
          for syn in wordnet.synsets(sentence[i]):
              syns = wordnet.synsets(sentence[i])
              w1 = syns[0].name()
              temp = 0
              for l in syn.lemmas():
                  if l.antonyms():
                      antonyms.append(l.antonyms()[0].name())
              max_dissimilarity = 0
              for ant in antonyms:
                  syns = wordnet.synsets(ant)
                  w2 = syns[0].name()
                  syns = wordnet.synsets(sentence[i])
                  w1 = syns[0].name()
                  word1 = wordnet.synset(w1)
                  word2 = wordnet.synset(w2)
                  if isinstance(word1.wup_similarity(word2), float) or isinstance(word1.wup_similarity(word2), int):
                      temp = 1 - word1.wup_similarity(word2)
                  if temp>max_dissimilarity:
                      max_dissimilarity = temp
                      antonym_max = ant
                      sentence[i] = antonym_max
                      sentence[i-1] = ''
  while '' in sentence:
      sentence.remove('')
  return sentence

def isYesNoQuestion(question):
    s = question.lower()
    prefixes = ['am','is','are',"was","were", "wasn't", "weren't",
                "do","does","did","doesn't","didn't",
                "has","have","hasn't", "haven't","had",
                "can","could","will","would","may","might","shall","must","should"] # reference https://englishstudypage.com/grammar/yesno-questions/
    result = s.startswith(tuple(prefixes))
    return result

def answerWHQuestion(question,file):

    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
    logging.getLogger("haystack").setLevel(logging.INFO)
    launch_es()
    time.sleep(30)
    # Get the host where Elasticsearch is running, default to localhost
    host = os.environ.get("ELASTICSEARCH_HOST", "localhost")
    document_store = ElasticsearchDocumentStore(host=host, username="", password="", index="document")

    #### set document folder

    ###### test
    # keep data as the document file
    doc_dir = str("./data/")
    docs = convert_files_to_docs(dir_path=doc_dir, clean_func=clean_wiki_text, split_paragraphs=False)
    document_store.write_documents(docs)

    retriever = BM25Retriever(document_store=document_store)

    reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)

    pipe = ExtractiveQAPipeline(reader, retriever)


    prediction = pipe.run(
        query=question,
        params={"Retriever": {"top_k": 1}, "Reader": {"top_k": 1}}
    )
    answer = prediction['answers'][0].to_dict()['answer']
    # print(answer)
    return answer

def answerYesNoQuestion(question,file):

    logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
    logging.getLogger("haystack").setLevel(logging.INFO)
    launch_es()
    time.sleep(30)
    # Get the host where Elasticsearch is running, default to localhost
    host = os.environ.get("ELASTICSEARCH_HOST", "localhost")
    document_store = ElasticsearchDocumentStore(host=host, username="", password="", index="document")

    #### set document folder
    doc_dir = str("./data/"+file)
    docs = convert_files_to_docs(dir_path=doc_dir, clean_func=clean_wiki_text, split_paragraphs=False)
    document_store.write_documents(docs)

    retriever = BM25Retriever(document_store = document_store)
    reader = FARMReader(model_name_or_path = "deepset/roberta-base-squad2", use_gpu=True)
    pipe = ExtractiveQAPipeline(reader, retriever)

    prediction = pipe.run(
        query=question,
        params={"Retriever": {"top_k": 1}, "Reader": {"top_k": 1}}
    )

    nlp = spacy.load('en_core_web_sm')
    queryTokens = nlp(question)

    ## get 1st predict score and answer
    score = prediction['answers'][0].to_dict()['score']
    answer = prediction['answers'][0].to_dict()['answer']
    answerTokens = nlp(answer)
    sentence_tokens = [[token.text for token in sent] for sent in answerTokens.sents]

    ### add sentence semantic negation
    negateTokens = Negation(sentence_tokens)
    answerNegateSentence = ' '.join(map(str, negateTokens))
    answerNegate = nlp(answerNegateSentence)

    QAsimilarityNegate = queryTokens.similarity(answerNegate)

    QAsimilarity = queryTokens.similarity(answerTokens)  # need to test the QAsimilarity constrain, current useless

    if ((score >= 0.5) ==True) & ((QAsimilarityNegate >0.15) == True):  ## 0.15 from experiment
        answerYN = "Yes"
    else:
        answerYN = "No"

    return answerYN

if __name__ == "__main__":

    # ignore sterr and stdout
    if DEBUG == False:
        sys.stderr = open('/dev/null', 'w')

    try:
        txt_input_file = sys.argv[1]
        questionFile = sys.argv[2]
        with open(txt_input_file) as filePath:
            files = filePath.readlines()   # here assume we are given filePath,  ask do we need to generate .txt files from these path.


        file = "set1" # example  we need to ask if  questions in questions.txt from one article.txt
        with open(questionFile) as f:
            questions = f.readlines()
            cnt = 1
            answers = []
            for i in range(len(questions)):
                if isYesNoQuestion(questions[i]) :
                    answer = answerYesNoQuestion(questions[i],file)###
                    answers.append(answer)
                else:
                    answer = answerWHQuestion(questions[i],file)  ### need to edit file folder here, file is a folder contains .txt files
                    answers.append(answer)

    ############## get the output format #################
            print("***************************")
            # print("A1 ", answers[1])
            # print("A2 ", answers[2])
            # print("A3 ", answers[3])
            for i in range(len(answers)): # ask professor how many questions will be asked ?
                print("A{}".format(i), answers[i])
    except:
        print("Error: This script requires two arguments: (1) textfile.txt (2) number of questions to generate")



#### code for test the system: python3 QG/answer.py QG/data/pikachu_pokemon.txt test_questions.txt
