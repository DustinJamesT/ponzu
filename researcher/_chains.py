
# -- TBD need to figure out how to handle context and inputs for chains (really agent tools in future)

from ..gpt._chains import (generationChain,)

from ._prompts import (loadEditorPlanPrompt,
                       )

# ==================================================
# -- Single Function LLM Chains 
# ==================================================
def titleChainLLM(text): 
  pass 

def editorNotesChainLLM(original_text, objective, context = '', word_count = 0, model = ''): 
  # -- generates notes based off an editing objective like condense, expand, or rephrase
  
  # ---- define prompt
  prompt, inputs, output_parser = loadEditorPlanPrompt(objective=objective, original_text=original_text, context=context, word_count=word_count)

  # -- load chain + execute 
  chain = generationChain(prompt_template=prompt, inputs=list(inputs.keys()), max_runs=3, temp=0.3, output_parser=output_parser, model=model)
  
  return chain

def incorporateNotesChainLLM(text): 
  # -- generates notes based off an editing objective like condense, expand, or rephrase
  pass 

# ==================================================
# -- Tagging Chains (Functions)
# ==================================================
def tagSectionChainFn(sections, llm): 
  schema = {  
      "properties": {
         "section": {
              "type": "string",
              "enum": sections,
              "description": "section title referenced in a user query",
          },
      },
      "required": ["section"],
  }

  chain = create_tagging_chain(schema, llm)


# ==================================================
# -- Sequential Chains  
# ==================================================





# ==================================================
# -- Router Chains  
# ==================================================