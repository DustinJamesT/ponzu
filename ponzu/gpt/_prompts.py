


# 


def loadSummaryPrompt(word_count = 300, detail = 'concise'): 

  if 'detail' in detail or 'detailed' in detail:
    word_count = 500

  word_count = str(word_count)

  prompt = f"""You are a brilliant analyst at an investment fund who writes summaries of text for superiors with hyper relavent details and does not exceed target word count. Write a summary of the following text in prose that flows. Do not exclude relavent details:

    Level of Details: {detail}
    Target Word Count: {word_count}

    """
  
  prompt += """Text: {text}"""
  
  return prompt 