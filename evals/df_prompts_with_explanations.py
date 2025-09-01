PROMPT_WITH_GUIDANCE = """

Double fences are shown from the satellite view as two parallel lines. They are different from roads, railways, and other linear features.

There's usually double fences around nuclear power plants, and at some point along the fence, there's usually a gate, which looks rectangular from a satellite view.

A subtle feature of double fences is that they also have a shadow under the fence (which appears as a darker line on a satellite image), which is not present in other linear features.

Does this image contain double fences?
If yes, answer "yes" and provide a detailed explanation of what you observe (e.g., "conspicuous checkpoint where double fencing seen as two dark, straight, parallel lines breaks", "double fencing gate seen by segmented shadows cutting across the entrance/exit road", etc.).
If no, answer "no" and explain why you don't see double fences.

Respond with JSON in this format:
{
  "double_fences_present": "yes" or "no",
  "explanation": "detailed reasoning for your decision"
}

Here is the image:
{{ item.image_url }}
"""

PROMPT = """
Does this image contain double fences?
If yes, answer "yes" and provide a detailed explanation
If no, answer "no" and explain why you don't see double fences

Respond with JSON in this format:
{
  "double_fences_present": "yes" or "no",
  "explanation": "detailed reasoning for your decision"
}

Here is the image:
{{ item.image_url }}
"""