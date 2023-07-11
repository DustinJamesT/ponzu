


# -- local package imports
from ..gpt.gpt import GPT

# -- local imports
from ._helpers import (standardizeLinkListFormat,
                       combineSourcesText_,
                       combineAllSourceText_,
                       extractYoutubeLinks_,
                       restructureOutline_,
                       createMarkedownFile_)

from ._prompts import (loadSummaryPrompt,
                       loadOutlinePrompt,
                       loadOutlinePlanPrompt,
                       loadExpandPrompt,
                       loadWriterPrompt,
                       loadRewritePrompt,
                       loadRewriteOutlinePrompt,
                       loadEditorPlanPrompt,
                       loadReportFlowPrompt,
                       loadFindSectionPrompt,
                       loadDecideOutlinePrompt,
                       loadCleanRequestPrompt)

from ._actions import (generateOutline_,
                       generateKeyEventOutline_)


class Writer(GPT): 
    
  def __init__(self) -> None:
      super().__init__()

      # -- general variables
      self.knowledge_base = []

      self.report = {
        'title': '' ,
        'topic': '',
        'sections': [], 
        'summary': '',
        'raw_text': '',
        'vectorstore': None,
      }

      self.download_filepath = ''

      self.edit_model = 'chat'
      self.write_model = ''

  # ==================================================
  # -- Knowledge Base Initialization 
  # ==================================================
  def loadSources(self, source_objects, vectorize = True, generate_metadata = False, return_sources = True):
    # -- standardize link list format in to a list of dicts: [{'title': '', 'links': ['link1', 'link2']}, {'title': '', 'links': ['link1', 'link2']}]
    source_objects = standardizeLinkListFormat(source_objects)

    # -- extract any youtube links and get transcript. add transcript to text
    source_objects = extractYoutubeLinks_(source_objects)

    # -- combine text from each link set into a single string stored in the 'text' key of each link set
    source_objects = combineSourcesText_(source_objects, self.twitter)
    
    # -- generate metadata
    if generate_metadata:
      source_objects = self.summarizeKnowledgeBase(source_objects)

    # -- add to knowledge base
    self.knowledge_base += source_objects

    # -- vectorize text for only source objects 
    if vectorize:
      self._vectorizeSources(source_objects = source_objects)
    
    # -- return sources
    if return_sources:
      return source_objects
    
  # ==================================================
  # -- Knowledge Base Actions 
  # ==================================================
  def summarizeKnowledgeBase(self, source_objects = list(), include_title = True):
    # -- load sources if none are provided
    if len(source_objects) == 0:
      source_objects = self.knowledge_base
    else:
      source_objects = self.loadSources(source_objects)

    # -- summarize sources
    for source_object in source_objects:
      source_object['summary'] = self.summarizeText(source_object['text'], summary_detail = 'medium')
      source_object['title'] = self.generateTitle(source_object['summary'])

      source_object['summary'] = source_object['title'] + ' \n ' + source_object['summary'] if include_title else source_object['summary'] 

    
    return source_objects
  
  def _vectorizeSources(self, source_objects = list()):
    # -- load sources if none are provided
    if len(source_objects) == 0:
      source_objects = self.knowledge_base

    # -- vectorize text
    for source_object in source_objects:
      # -- get source object without text key 
      metadata_ = {k: v for k, v in source_object.items() if k != 'text'}
      self.vectorizeText(source_object['text'], metadata=metadata_ )

  # ==================================================
  # -- Report Writer 
  # ==================================================
  def generateReport(self, source_objects = list(), report_topic = '', generate_markdown = False, download_filepath = '', verbose = False):
    self.verbose = verbose

    # -- ingest sources and vectorize
    self._initializeReport(source_objects = source_objects, report_topic = report_topic, summary_detail = 'detailed_report', vectorize = True)

    # -- generate outline: multi phase. generate outline. generate description and bullets. 
    self.generateOutline()

    # -- generate sections: multi phase. 1. initial vector write 2. context share + regen 3. 
    self.generateReportSections()

    # -- edit report: generates notes and hand back to writer? 
    self.editReport()

    # -- generate markdown
    self.generateMarkdown(download_filepath = download_filepath) if generate_markdown else None

  def _initializeReport(self, source_objects = list(), report_topic = '', generate_metadata = False):
    # -- load sources if none are provided
    print('..... loading sources') if self.verbose else None
    source_objects = self.loadSources(source_objects, generate_metadata = generate_metadata) if len(source_objects) > 0 else self.knowledge_base
    report_topic = "An analysis of a topic" if report_topic == '' else report_topic

    # -- combine text 
    raw_text = combineAllSourceText_(source_objects)

    # -- summarize text TODO: do with vectorstore so faster 
    print('..... summarizing combined text') if self.verbose else None
    #summary = self.summarizeText(raw_text, summary_detail = summary_detail)
    summary = self.generateSummary(topic=report_topic, word_count=300)

    # -- generate title
    print('..... generating title') if self.verbose else None
    text_ = f"Report Topic: {report_topic} \n\n Source Material Summary: {summary}"
    title = self.generateTitle(text_)

    # -- add to report
    self.report['title'] = title
    self.report['topic'] = report_topic
    self.report['summary'] = summary
    self.report['raw_text'] = raw_text

    return self.report
  
  def generateOutline(self, source_objects = list(), report_topic = '', text_model = '', print_outline = False):
    # -- load sources if none are provided
    source_objects = self.knowledge_base if len(source_objects) == 0 else source_objects

    # -- initialize report if none exists
    print('... initializing report') if self.verbose else None
    self._initializeReport(source_objects = source_objects, report_topic=report_topic) if len(self.report['raw_text']) == 0 else None

    # ---- generate outline 
    print('... generating outline') if self.verbose else None
    #section_objects = self.generateSectionObjects() # -- can't get parsing to work
    section_data = generateOutline_(self.model, self.report['summary'], objective_topic = self.report['topic'])
    section_objects = restructureOutline_(section_data)

    print('..... expanding descriptions') if self.verbose else None
    for section in section_objects:
      section['section_description'] = section['section_description'] + ' plan: ' + self.generateSectionPlan(objective = 'Provided is a description of a section of a report. Expand the text to include relavent details someone would need to know to actually write this section.', original_text = section['section_description'])
      section['target_word_count'] = 400

    self.report['sections'] = section_objects

    if print_outline:
      self.printOutline()
  
   
  def generateReportSections(self, model = '', advanced = False):
    # -- generate initial sections text 
    print('... generating section text') if self.verbose else None
    for section in self.report['sections']:
      print('..... section: ' + section['section_title']) if self.verbose else None
      objective = section['section_title'] + ' ' + section['section_description']
      section['text'] = self.generateSectionText(objective = objective, word_count = section['target_word_count'], model=model)
  
  def generateSectionText(self, objective, word_count = 300, model = ''):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = objective, vectorstore = self.vectorstore, similarity_threshold = 0.76, combine_text=True)

    # ---- define prompt
    prompt, inputs, output_parser = loadWriterPrompt(objective=objective, context=docs, word_count=word_count)

    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=5, temp=0.3, output_parser=output_parser, model=model)
   
    return output
  
  def generateKeyEventsOutline(self, source_objects = list(), report_topic = 'a round up of key events', model = ''):
    # -- load sources if none are provided
    source_objects = self.knowledge_base if len(source_objects) == 0 else source_objects

    # -- initialize report if none exists
    print('... initializing report') if self.verbose else None
    self._initializeReport(source_objects = source_objects, report_topic=report_topic, generate_metadata = True) if len(self.report['raw_text']) == 0 else None

    # -- make sure knowledge base populated 
    if len(self.knowledge_base) == 0:
      raise ValueError('Knowledge base is empty. Please load sources before generating a report.')

    # -- make sure knowledge base summarized
    if 'summary' not in self.knowledge_base[0].keys():
      self.summarizeKnowledgeBase()
    
    # -- combine text TODO - test title vs summary (can include both in summarizeKnowledgeBase)
    connector = '\n\n -- NEW SOURCE -- \n\n'
    raw_text = combineAllSourceText_(self.knowledge_base, key = 'summary', connector=connector) 

    # -- find key events (titles and descriptions)?
    objective = "A list of key events and their descriptions."
    key_events = generateKeyEventOutline_(self.model, raw_text = raw_text, objective_topic = objective)
    section_objects = restructureOutline_(key_events) 

    print('..... expanding descriptions') if self.verbose else None
    objective = 'Provided is a description of a section of a report. Expand the text to include relavent details someone would need to know to actually write this section.'
    for section in section_objects:
      section['section_description'] = section['section_description'] + ' plan: ' + self.generateSectionPlan(objective = objective, original_text = section['section_description'])
      section['target_word_count'] = 400

    self.report['sections'] = section_objects

  def clearReport(self):
    self.report = {
      'title': '',
      'topic': '',
      'sections': [], 
      'summary': '',
      'raw_text': '',
      'vectorstore': None,
    }
  

  def editReport(self, model = None):
    print('... editing report') if self.verbose else None

    model = self.text_model if model == None else model

    # -- full report: looks across sections to remove redundancies and make flow
    self._editAcrossSections()

    # -- add analysis to sections
    for section in self.report['sections']:
      pass

    # -- generic edits 
    for section in self.report['sections']:
      print('..... editing section: ' + section['section_title']) if self.verbose else None
      section['text'] = self._editSectionSimple(section)

    # -- full report (again)
    self._editAcrossSections()


  def _editAcrossSections(self):
    print('..... cross section flow edit') if self.verbose else None
    report_text = combineAllSourceText_(self.report['sections'])

    # -- full report edit: edits to remove redundancies and make flow
    for section in self.report['sections']:
      inputs = {'report_text': report_text, 'section_text': section['text']}

      prompt, inputs, output_parser = loadReportFlowPrompt(inputs)
      editor_plans = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.4, output_parser=output_parser, model=self.edit_model)
    
      query = section['section_title'] + ' \n ' + section['section_description']
      section['text'] = self._incorporateEditorPlans(section['text'], editor_plans = editor_plans, context = '', query = query)

      report_text = combineAllSourceText_(self.report['sections'])
    

  def _editSectionSimple(self, section_object):
    
    editor_objectives = [
      'Edit the text to explain new terms and complex topics from first principles.',
      "Sound like a crypto industry insider who is an expert on the topic. Remove words like blockchain technology in favor of the term crypto.",
      "Insert strategic rationalizations for key points.",
      "Make the text more engaging and interesting to read.",
      "Remove any sensational language and over promises.",
      "Make the text relatable through analogies and metaphors.",
      "Make the text is written from an objective thrid party perspective.",
    ]

    for objective in editor_objectives:
      query = section_object['section_title'] + ' \n ' + section_object['section_description']
      section_object['text'] = self.editText(section_object['text'], objective = objective, query = query)

    return section_object['text']



  # ==================================================
  # -- Report Functions TODO -- move most of this to own file 
  # ==================================================

 
  





  def generateMarkdown(self, download_filepath = ''):
    # -- validate download filepath
    if download_filepath == '':
      download_filepath = self.download_filepath

    # -- generate markdown
    createMarkedownFile_(self.report['sections'], file_name = self.report['title'], output_dir = download_filepath, title_key = 'section_title', summary_key = 'text')


  def printOutline(self):
    print(self.report['title'])
    print('-------------------')
    print(' ')
    for section in self.report['sections']:
      print(section['section_title'])
      print('-- Description: ' +section['section_description'])
      print('-- Word count: ' + str(section['target_word_count'])) 
      print('-------------------')
  
  def generateKeyEventsOutline(self, model = ''):
    # -- make sure knowledge base populated 
    if len(self.knowledge_base) == 0:
      raise ValueError('Knowledge base is empty. Please load sources before generating a report.')

    # -- make sure knowledge base summarized
    if 'summary' not in self.knowledge_base[0].keys():
      self.summarizeKnowledgeBase()
    
    # -- combine text TODO - test title vs summary (can include both in summarizeKnowledgeBase)
    connector = '\n\n -- NEW SOURCE -- \n\n'
    raw_text = combineAllSourceText_(self.knowledge_base, key = 'title', connector=connector) 

    # -- find key events (titles and descriptions)?
    objective = "A list of key events and their descriptions."
    key_events = generateKeyEventOutline_(self.model, raw_text = raw_text, objective_topic = objective)
    section_objects = restructureOutline_(key_events) 

    print('..... expanding descriptions') if self.verbose else None
    objective = 'Provided is a description of a section of a report. Expand the text to include relavent details someone would need to know to actually write this section.'
    for section in section_objects:
      section['section_description'] = section['section_description'] + ' plan: ' + self.generateSectionPlan(objective = objective, original_text = section['section_description'])
      section['target_word_count'] = 400

    self.report['sections'] = section_objects


                                          
    # -- check if list and return 

  # ==================================================
  # -- Chain Tools  
  # ==================================================
  def generateFromPrompt(self, prompt_function, inputs, query): 
  
    # -- load chain + execute 
    output = self.generateTextLLMContext(prompt_function=prompt_function, inputs=inputs, vectorstore=self.vectorstore, context_query = query)
   
    return output
  
  def simpleChainFromPrompt(self, prompt_function, inputs, query): 
  
    # -- load chain + execute 
    chain = self.generationChainContext(prompt_function=prompt_function, inputs=inputs, vectorstore=self.vectorstore, context_query = query)
   
    return chain


  # ==================================================
  # -- Text Tools  
  # ==================================================
  def _incorporateEditorPlans(self, orginal_text, editor_plans, context = '', query = ''):
    prompt = loadRewritePrompt
    inputs = {'objective': editor_plans, 'original_text': orginal_text, 'context': context}
    query = orginal_text if query == '' else query

    # -- load chain + execute 
    text = self.generateTextLLMContext(prompt_function=prompt, inputs=inputs, vectorstore=self.vectorstore, context_query = query, max_runs=3, temp=0.4, model=self.write_model)

    return text
  

  def editText(self, text, objective = '', query = '', section = None):
    print('..... editing text') if self.verbose else None

    objective = "Make the text more concise and clear." if objective == '' else objective
    query = "Original Text Section Title: " + section['section_title'] + ' \n ' + query if section != None else query

    # -- generate editor plans
    prompt = loadEditorPlanPrompt
    inputs = {'objective': objective, 'original_text': text, 'context': ''}
    query = text if query == '' else query

    editor_plans = self.generateTextLLMContext(prompt_function=prompt, inputs=inputs, vectorstore=self.vectorstore, context_query = query, max_runs=3, temp=0.4, model=self.edit_model)

    print('..... generated plans. starting edits') if self.verbose else None
    # -- incorporate editor plans
    text = self._incorporateEditorPlans(text, editor_plans, context = query, query = query)

    return text
  
  

  def generateTitle(self, text, prompt_template = ''):
    # -- default prompt template
    prompt_template_ = """Generate a report title for the following text: 

    Text: {text}
    
    Title: """

    # -- set inputs 
    prompt_template = prompt_template_ if prompt_template == '' else prompt_template
    inputs = {'text': text}

    output = self.generateTextLLM(prompt_template, inputs = inputs, max_runs = 3, temp = 0.4, output_parser = None)
    
    if type(output) == list:
      output = output[0]
    
    if type(output) == dict:
      output = output['text'] if 'text' in output.keys() else None
      output = output['title'] if 'title' in output.keys() else None

    return output
  
  def generateSummary(self, topic = '', word_count = 300, model = ''):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = topic, vectorstore = self.vectorstore, similarity_threshold = 0.76, combine_text=True)

    # ---- define prompt
    prompt, inputs, output_parser = loadSummaryPrompt(topic = topic, context = docs, word_count=word_count)
    
    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.4, output_parser=output_parser, model=model)
   
    return output
  
  def expandTextWithContext(self, objective = 'expand the text', original_text = '', word_count = 0, model = ''):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = original_text, vectorstore = self.vectorstore, similarity_threshold = 0.76, combine_text=True)

    # ---- define prompt
    prompt, inputs, output_parser = loadExpandPrompt(objective=objective, original_text=original_text, context=docs, word_count=word_count)

    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.3, output_parser=output_parser, model=model)
   
    return output
  
  def generateSectionPlan(self, objective = 'expand the text', original_text = '', word_count = 0, model = ''):
    # ---- get context 
    docs = self.retrieveCompressedDocs(query = original_text, vectorstore = self.vectorstore, similarity_threshold = 0.76, combine_text=True)

    # ---- define prompt
    prompt, inputs, output_parser = loadOutlinePlanPrompt(objective=objective, original_text=original_text, context=docs, word_count=word_count)

    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.3, output_parser=output_parser, model=model)
   
    return output
  

  
  # -- TODO: Output parse not working at all
  def generateSectionObjects(self, report_summary = '', model = ''):
    query = self.report['topic'] + ' ' + self.report['summary'] if report_summary == '' else report_summary

    # ---- get context
    docs = self.retrieveCompressedDocs(query = query, vectorstore=self.vectorstore, similarity_threshold = 0.76, combine_text=True)
    
    # ---- define prompt
    prompt, inputs, output_parser = loadOutlinePrompt(summary = report_summary, context = docs, topic = self.report['topic'])
    
    # -- load chain + execute 
    output = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.4, output_parser=output_parser, model=model)
   
    section_objects = restructureOutline_(output)
   
    return section_objects
  

  


  # ==================================================
  # -- Chat
  # ==================================================
  def cleanUserInstructions(self, chat):
    print('..... cleaning user request') if self.verbose else None
    inputs={'user_request': chat}
    prompt, inputs, output_parser = loadCleanRequestPrompt(inputs)
    clean_request = self.generateTextLLM(prompt_template=prompt, inputs=inputs, max_runs=3, temp=0.3, output_parser=output_parser, model=self.edit_model)

    return clean_request
  
  def editSectionChat(self, chat):
    print('..... getting targeted section') if self.verbose else None
    
    # -- get section 
    section_object = self.findSection_(chat)
    section_object = self.findSection_(chat) if section_object == None else section_object
    print('..... found section ' + section_object['section_title']) if self.verbose else None

    # -- clean request
    clean_request = self.cleanUserInstructions(chat)
    print('..... cleaned request: ' + clean_request) if self.verbose else None
    
    # -- check if outline or section is requested
    print('..... checking outline or text') if self.verbose else None
    schema = loadDecideOutlinePrompt()
    chain = self.simpleLlmFunction(schema, model = 'chat', temp = 0)

    text_label = chain(chat)

    if type(text_label) == dict:
      text_label = text_label['text']['outline_label']

    print('....... will be editing the ' + text_label ) if self.verbose else None
   
    # -- edit section
    print('..... generating edit instructions + implement') if self.verbose else None
    if text_label == 'outline':

      # -- generate editor plans
      prompt = loadEditorPlanPrompt
      inputs = {'objective': clean_request, 'original_text': section_object['text'], 'context': ''}
      query = section_object['text'] 

      editor_plans = self.generateTextLLMContext(prompt_function=prompt, inputs=inputs, vectorstore=self.vectorstore, context_query = query, max_runs=3, temp=0.2, model=self.edit_model)

      # -- generate new outline text
      prompt = loadRewriteOutlinePrompt
      inputs = {'objective': editor_plans, 'original_text': section_object['section_description'], 'context': ''}
      query = section_object['text'] 

      section_object['section_description'] = self.generateTextLLMContext(prompt_function=prompt, inputs=inputs, vectorstore=self.vectorstore, context_query = query, max_runs=3, temp=0.2, model=self.text_model)
     
    else:
      section_object['text'] = self.editText(section_object['text'], objective = clean_request,  section=section_object)

    return section_object
  
  def findSection_(self, chat):
    # -- get current sections and return matching section object
    sections = [section['section_title'] for section in self.report['sections']]
    schema = loadFindSectionPrompt(sections)
    chain = self.simpleLlmFunction(schema, model = 'chat', temp = 0)

    section = chain(chat)

    section_title = section['text']['section']

    for section_object in self.report['sections']:
      if section_object['section_title'] == section_title:
        return section_object
        

    return None
    


  
  
