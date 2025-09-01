ZERO_SHOT_PROMPT_WITH_EXPLANATIONS = """

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

FEW_SHOT_PROMPT_WITH_EXPLANATIONS = """

Double fences are shown from the satellite view as two parallel lines. They are different from roads, railways, and other linear features.

There's usually double fences around nuclear power plants, and at some point along the fence, there's usually a gate, which looks rectangular from a satellite view.

A subtle feature of double fences is that they also have a shadow under the fence (which appears as a darker line on a satellite image), which is not present in other linear features.

Here are some examples:

Example 1 (Double fences present):
Image: https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_train/Ling_ao-1_M310_22.60184_114.55039_0.5km.png?raw=true
Answer: {"double_fences_present": "yes", "explanation": "checkpoint where double fencing seen by the enclosed dark gray band originates"}

Example 2 (No double fences):
Image: https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/no_df_train/XIAN_34.43031_108.93112_0.5km.png?raw=true
Answer: {"double_fences_present": "no", "explanation": "urban area with roads and buildings but no visible double fencing structures or parallel lines characteristic of security perimeters"}

Example 3 (Double fences present):
Image: https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_train/Tianwan-2_VVER1000_34.68743_119.46293_0.5km.png?raw=true
Answer: {"double_fences_present": "yes", "explanation": "gate seen as two dark lines cutting across the entrance/exit road, extending in both directions to cast segmented shadows"}

Example 4 (No double fences):
Image: https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/no_df_train/HANGZHOU_30.25766_120.47546_0.5km.png?raw=true
Answer: {"double_fences_present": "no", "explanation": "residential and commercial area with typical urban infrastructure but no security fencing or parallel line structures"}

Example 5 (Double fences present):
Image: https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_train/MOX_hot_cell_39.74185_116.03290_0.5km.png?raw=true
Answer: {"double_fences_present": "yes", "explanation": "conspicuous checkpoint where double fencing seen as two dark, straight, parallel lines turning rigid corners breaks, then continues to extend around the complex"}

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
