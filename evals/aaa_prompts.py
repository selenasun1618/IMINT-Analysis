
ZERO_SHOT_PROMPT = """
Would you guess this image contains an anti-aircraft artillery (AAA) site?
If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer. Here is the image:
{{ item.image_url }}
"""

FEW_SHOT_PROMPT = """
Would you guess this image contains an anti-aircraft artillery (AAA) site?
If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer.

Here are some examples:

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/Site_38.97576_125.88714_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/AAA_38.95560_125.60874_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/AAA_L_39.00099_125.41421_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/Site_39.96523_124.64042_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/Site_39.08243_125.89374_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/Site_39.23018_125.92079_0.5km.png?raw=true
Answer: yes

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_38.29403_125.21576_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_39.46983_126.80245_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_41.17677_125.45686_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_37.93857_127.46437_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_38.12172_125.69937_0.5km.png?raw=true
Answer: no

Image: https://github.com/selenasun1618/IMINT-Images/blob/main/aaa_train_combined/AAA_39.90886_124.04146_0.5km.png?raw=true
Answer: no

Now classify this image:
{{ item.image_url }}
"""