ZERO_SHOT_PROMPT = """

Double fences are shown from the satellite view as two parallel lines. They are different from roads, railways, and other linear features.

There's usually double fences around nuclear power plants, and at some point along the fence, there's usually a gate, which looks rectangular from a satellite view.

A subtle feature of double fences is that they also have a shadow under the fence (which appears as a darker line on a satellite image), which is not present in other linear features.

Does this image contain double fences?
If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer. Here is the image:
{{ item.image_url }}
"""

FEW_SHOT_PROMPT = """

Double fences are shown from the satellite view as two parallel lines. They are different from roads, railways, and other linear features.

There's usually double fences around nuclear power plants, and at some point along the fence, there's usually a gate, which looks rectangular from a satellite view.

A subtle feature of double fences is that they also have a shadow under the fence (which appears as a darker line on a satellite image), which is not present in other linear features.

Here are some examples:

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/df_train/Ling_ao-1_M310_22.60184_114.55039_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/no_df_train/XIAN_34.43031_108.93112_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/df_train/Tianwan-2_VVER1000_34.68743_119.46293_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/no_df_train/HANGZHOU_30.25766_120.47546_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/df_train/MOX_hot_cell_39.74185_116.03290_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/no_df_train/BEIJING_39.68776_116.12418_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/df_train/Plant_404_production_reactor_40.22247_97.35570_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/no_df_train/TIANJIN_39.07973_116.62684_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/df_train/Shidao_Bay_CAP1400_36.96356_122.51725_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/no_df_train/HANGZHOU_30.15644_120.23214_0.5km.png?raw=true
Answer: no

Does this image contain double fences?
If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer. Here is the image:
{{ item.image_url }}
"""