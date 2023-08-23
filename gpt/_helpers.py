


# ==================================================
# -- Ingestion Helpers
# ==================================================

def checkYoutubeLink(link): 
  # -- TODO: add more robust youtube link checking https://github.com/royca/yt-gpt/blob/master/ytgpt.py
  # -- check if youtube link
  if 'youtube.com' in link or 'youtu.be' in link:
    return True
  else:
    return False
  
def combineDocText(docs):
  doc_text = ''
  for doc in docs:
    doc_text += doc.page_content + ' \n '

  return doc_text
  


