



from ..twitter import twitter

from ._api import (loadLLM,
                   addTextToVectorStore_api,
                   retrieveCompressedDocs_api)

from ._actions import (summarizeText,
                       chatVectorstore,
                       generateTextLLM)

from ._chains import (generationChain,
                      simpleLlmFunction)

from ._helpers import (combineDocText,)

from ._prompts import (loadSummaryPrompt,)

class GPT():
    
  def __init__(self):

    # -- gpt memory 
    self.vectorstore = None 
    self.conversations = {} # -- TODO - have multiple conversations / chat histories
    self.chat_history = []
    self.text_model = ''
    self.model = loadLLM(temp=0.6, model='')

    # -- internalize twitter class
    self.twitter = twitter.Twitter()

    # -- general variables
    self.verbose = False

  # ==================================================
  # -- Vectorization
  # ==================================================

  def vectorizeText(self, text, metadata = dict(), return_vectorstore = False):
    vectorstore = addTextToVectorStore_api(self.vectorstore, text) if len(metadata) == 0 else addTextToVectorStore_api(self.vectorstore, text, metadata = metadata)
    
    if return_vectorstore:
      return vectorstore
    
    self.vectorstore = vectorstore


  def chatVectorstore(self, query, model = 'chat'): 
    answer, memory = chatVectorstore(self.vectorstore, query, model = model, memory = self.chat_history, return_memory=True)
    self.chat_history = memory

    return answer
  
  def retrieveCompressedDocs(self, query, vectorstore = None, similarity_threshold = 0.76, combine_text = True):
    vectorstore = self.vectorstore if vectorstore == None else vectorstore

    docs = retrieveCompressedDocs_api(vectorstore, query, similarity_threshold = similarity_threshold)

    if combine_text:
      docs = combineDocText(docs)

    return docs

  # ==================================================
  # -- Summarization
  # ==================================================
  
  def summarizeText(self, text, summary_detail = None, word_count = 0, prompt_template = '', temp = 0.2, chuck_size=1000, overlap=0, chain_type="map_reduce"): 
    # -- load prompt text
    prompt = None

    if summary_detail != None or word_count != 0:
      prompt = loadSummaryPrompt(word_count=word_count, detail=summary_detail) 

    if prompt_template != '':
      prompt = prompt_template

    # -- generate summary
    summary = summarizeText(text, prompt, temp = temp, chuck_size=chuck_size, overlap=overlap, chain_type=chain_type)

    return summary


  # ==================================================
  # -- Chains
  # ==================================================

  def generateTextLLM(self, prompt_template, inputs, model = '', max_runs = 3, temp = 0.4, output_parser = None):
    # -- initialize chain
    text = generateTextLLM(prompt=prompt_template, inputs=inputs, model = model, max_runs = max_runs, temp = temp, output_parser = output_parser)
    return text
  
  def generationChain(self, prompt, input_variables, model = '', temp = 0.3, output_key = 'text', output_parser = None):
    # -- initialize chain
    chain = generationChain(prompt, input_variables, model = model, temp = temp, output_key = output_key, output_parser = output_parser)
    return chain
  

  def generateTextLLMContext(self, prompt_function, inputs, vectorstore = None, context_query = '', model = '', max_runs = 3, temp = 0.4, similarity_threshold = 0.76):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = context_query, vectorstore = vectorstore, similarity_threshold = similarity_threshold, combine_text=True)

    inputs['context'] = '' if 'context' not in inputs.keys() else inputs['context']
    inputs['context'] += docs

    prompt, inputs, output_parser = prompt_function(inputs)

    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=max_runs, temp=temp, output_parser=output_parser, model=model)
    
    return output
  
  def generationChainContext(self, prompt_function, inputs, vectorstore = None, context_query = '', model = '', temp = 0.3, output_key = 'text', similarity_threshold = 0.76):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = context_query, vectorstore = vectorstore, similarity_threshold = similarity_threshold, combine_text=True)

    inputs['context'] = '' if 'context' not in inputs.keys() else inputs['context']
    inputs['context'] += docs

    prompt, inputs, output_parser = prompt_function(inputs)

    # -- initialize chain
    chain = self.generationChain(prompt, input_variables = list(inputs.keys()), model = model, temp = temp, output_key = output_key, output_parser = output_parser)
    
    return chain
  
  def simpleLlmFunction(self, schema, model = 'chat', temp = 0):
    chain = simpleLlmFunction(schema, model = model, temp = temp)
    return chain


  # ==================================================
  # -- Tools
  # ==================================================



  # ==================================================
  # -- Actions
  # ==================================================