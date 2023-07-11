import os 
import datetime
from mdutils.mdutils import MdUtils

from ..gpt._helpers import (checkYoutubeLink,)
from ..gpt._api import (loadYoutubeLoader,)



# ==================================================
# -- Ingestion Helpers
# ==================================================
def standardizeLinkListFormat(link_list): 
  if len(link_list) == 0:
    raise ValueError('No links provided')
  
  # -- handle single link
  if type(link_list) == str and 'http' in link_list:
    link_list = [{'title': '', 'links': [link_list]}]

  # -- convert single list to list of lists (standardize format for processing multiple link sets)
  if type(link_list[0]) == str and 'http' in link_list[0]:
    #link_list = [{'title': '', 'links': link_list}]
    link_list_ = []

    for link in link_list:
      link_list_.append({'title': '', 'links': [link]})

    link_list = link_list_

  # -- TODO should only return valid links


  return link_list

def combineSourcesText_(link_list, twitter_client): 
  # link_list is a list of dicts with keys: 'title', 'links', 'raw_text' [{'title': '', 'links': ['link1', 'link2']}, {'title': '', 'links': ['link1', 'link2']}
  for link_set in link_list:
    raw_text = ''

    for link in link_set['links']:

      if 'https://' in link or 'http://' in link:
        if not checkYoutubeLink(link): 
          text_ = twitter_client.getUrlText(link)
          header = " \n\n --- URL Text --- \n Source URL: " + link + "\n\n " + 'Text: '

          raw_text += header + text_ + "\n\n"

      else:
        # -- assume link is just a string of text
        raw_text += " \n\n --- Section Text --- \n Text: " + link 

    if 'text' in link_set.keys():
      link_set['text'] += raw_text
    else:
      link_set['text'] = raw_text

  return link_list

def combineAllSourceText_(source_objects, key = 'text', connector = '\n'):
  text = ''

  for source_object in source_objects:
    text += connector + source_object[key]

  return text


def extractYoutubeLinks_(source_objects):

  for link_set in source_objects: 
    text = ''

    for link in link_set['links']:
      if checkYoutubeLink(link):
        transcript_ = loadYoutubeLoader(link)
        transcript = transcript_[0].page_content

        if type(transcript) != str:
          print('Error loading youtube transcript.')
          print('Link: ' + link)
          print(type(transcript))
          print(transcript)

        text += transcript

    if 'text' in link_set.keys():
      link_set['text'] += text
    else:
      link_set['text'] = text
        
  return source_objects

# ==================================================
# -- Writer Helpers
# ==================================================
def restructureOutline_(outline): 
  outline = [{'section_title': title, 'section_description': desc} for title, desc in zip(outline.section_titles, outline.section_descriptions)]

  return outline

def createMarkedownFile_(summary_objects, file_name = 'summary.md', output_dir = '', title_key = 'title', summary_key = 'summary'):
  # -- add .md extension if it doesn't exist
  if file_name[-3:] != '.md':
    file_name += '.md'
  
  # -- add output directory to file name
  filepath = os.path.join(output_dir, file_name) if output_dir != '' else file_name

  # -- create markdown file
  mdFile = MdUtils(file_name=filepath, title=file_name[:-3].capitalize())

  # -- generate today as string
  today = datetime.datetime.today().strftime('%b %d, %Y')
  date_text = 'Generated Date: ' + today
  mdFile.new_line(date_text, bold_italics_code='i')
  mdFile.write('  \n')

  # -- add summary text
  for summary_object in summary_objects:
    
    # -- convert tags to text 
    tags = ''
    if 'tags' in summary_object.keys():
      if 'label' in summary_object['tags'].keys():
        for tag in summary_object['tags']['label']:
          tags += tag + ', '

        tags = tags[:-2]

    # -- remove first space if it exists from summary text
    if summary_object[summary_key][0] == ' ':
      summary_object[summary_key] = summary_object[summary_key][1:]
    
    # -- generate markdown block 
    mdFile.new_header(level=3, title=summary_object[title_key], style = 'atx', add_table_of_contents="n") if title_key in summary_object.keys() else None
    mdFile.new_line(tags, bold_italics_code='i') if len(tags) > 0 else None
    mdFile.new_paragraph(summary_object[summary_key])
    mdFile.write('  \n')

    # -- convert links to text
    if 'links' in summary_object.keys():
      source_line = 'Sources: '
      for i, link in enumerate(summary_object['links']):
        i = str(i)
        source_line += f'[{i}] '
        source_line += mdFile.new_inline_link(link=link) 
        source_line += ', '
      
      source_line = source_line[:-2]
      mdFile.new_line(source_line, bold_italics_code='i')

      mdFile.write('  \n')

  # -- save file
  mdFile.create_md_file()

  return file_name