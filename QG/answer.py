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
from haystack.document_stores import ElasticsearchDocumentStore
from haystack.utils import clean_wiki_text, convert_files_to_docs, fetch_archive_from_http
from haystack.nodes import BM25Retriever
from haystack.nodes import FARMReader
from haystack.pipelines import ExtractiveQAPipeline


#
# wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.9.2-linux-x86_64.tar.gz -q
# tar -xzf elasticsearch-7.9.2-linux-x86_64.tar.gz
# chown -R daemon:daemon elasticsearch-7.9.2

DEBUG = False
USE_LOCAL_MODELS = False


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
    doc_dir = str("./data/"+file)
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



def answerYesNoQuestion(question):
    answer ####

    return answer

if __name__ == "__main__":

    # ignore sterr and stdout
    if DEBUG == False:
        sys.stderr = open('/dev/null', 'w')


    if (len(sys.argv) == 2):
        txt_input_file = sys.argv[1]
        questionFile = sys.argv[2]
        with open(txt_input_file) as filePath:
            files = filePath.readlines()   # here assume we are given filePath,  ask do we need to generate .txt files from these path.


        file = "set1" # example 
        with open(questionFile) as f:
            questions = f.readlines()
            cnt = 1
            answers = []
            for i in range(len(questions)):
                if isYesNoQuestion(questions[i]) :
                    answer = answerYesNoQuestion(questions[i])###
                    answers.append(answer)
                else:
                    answer = answerWHQuestion(questions[i],file)  ### need to edit file folder here, file is a folder contains .txt files
                    answers.append(answer)


    ############## get the output format #################
            print("***************************")
            # print("A1 ", answers[1])
            # print("A2 ", answers[2])
            # print("A3 ", answers[3])
            for i in range(len(answers)):
                print("A{}".format(i), answers[i])
    else:
        print("Error: This script requires two arguments: (1) textfile.txt (2) number of questions to generate")


