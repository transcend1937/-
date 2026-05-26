with open('src/exam/questions.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_questions = []

# Q1
new_questions.append("    {'id': 126, 'type': '图形推理', 'question_type': '单选', 'question': '请从四个选项中选出最恰当的一项填入问号处，使题干图形呈现一定的规律性。', 'answer': 'B', 'analysis': '观察发现题干图形均为轴对称图形，且对称轴依次逆时针旋转45\u00b0，问号处应选对称轴方向为竖直方向的图形，只有B项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image1.png']},\n")

# Q2
new_questions.append("    {'id': 127, 'type': '图形推理', 'question_type': '单选', 'question': '从所给四个选项中，选择最合适的一个填入问号处，使之呈现一定规律性。', 'answer': 'C', 'analysis': '题干图形均由直线和曲线构成，且所有图形均有1条对称轴，呈顺时针旋转45\u00b0的规律，问号处应选对称轴为左下-右上方向的图形，C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image2.png']},\n")

# Q3
new_questions.append("    {'id': 128, 'type': '图形推理', 'question_type': '单选', 'question': '请选择最适合的一项填入问号处，使右边图形的变化规律与左边图形一致。', 'answer': 'B', 'analysis': '左边一组图均为轴对称图形，且对称轴方向依次顺时针旋转45\u00b0；右边一组图也应遵循此规律，前两个图形对称轴为竖直和水平方向，问号处应对称轴为左上-右下方向，B项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image3.png']},\n")

# Q4
new_questions.append("    {'id': 129, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'B', 'analysis': '题干图形均为对称图形，且每个图形均有且只有1条对称轴，对称轴方向依次顺时针旋转45\u00b0，问号处图形的对称轴应为右上-左下方向，B项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image4.png']},\n")

# Q5
new_questions.append("    {'id': 130, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'A', 'analysis': '观察题干图形，开放图形和封闭图形交替出现，问号处应为开放图形，只有A项为开放图形，B、C、D均为封闭图形。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image6.png']},\n")

# Q6
new_questions.append("    {'id': 131, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'A', 'analysis': '观察题干图形，第一行三个图形均含有正方形，第二行三个图形均含有三角形，第三行前两个图形均含有圆形，所以问号处应含有圆形，只有A项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image7.png']},\n")

# Q7
new_questions.append("    {'id': 132, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'C', 'analysis': '题干图形均为轴对称图形，对称轴方向依次为竖直、水平、竖直、水平交替变化，问号处应为竖直对称轴，C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image9.png']},\n")

# Q8
new_questions.append("    {'id': 133, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'C', 'analysis': '观察发现题干图形均含有封闭区域，封闭区域数依次为4、5、6、7、8，呈递增规律，问号处应选封闭区域数为9的图形，只有C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image10.png']},\n")

# Q9
new_questions.append("    {'id': 134, 'type': '图形推理', 'question_type': '单选', 'question': '请从四个选项中选出最恰当的一项填在问号处，使图形呈现一定的规律性。', 'answer': 'A', 'analysis': '题干图形的部分数依次为1、2、1、2、1，呈交替规律，问号处应选部分数为2的图形，A项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image11.png']},\n")

# Q10
new_questions.append("    {'id': 135, 'type': '图形推理', 'question_type': '单选', 'question': '请从所给的四个选项中，选择最合适的一项填在问号处，使之呈现一定的规律性。', 'answer': 'C', 'analysis': '题干图形均为轴对称图形，第一组图形对称轴为水平方向，第二组前两个图形对称轴为竖直方向，问号处应为竖直对称轴，C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image13.jpeg']},\n")

# Q11
new_questions.append("    {'id': 136, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'A', 'analysis': '观察题干图形，所有图形均由两部分组成，且两部分均为轴对称图形，且两个对称轴呈垂直关系。A项两部分均为轴对称且对称轴垂直，符合规律。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image14.png']},\n")

# Q12
new_questions.append("    {'id': 137, 'type': '图形推理', 'question_type': '单选', 'question': '从所给四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'D', 'analysis': '题干图形均为对称图形，第一组图形对称轴依次顺时针旋转45\u00b0；第二组前两个图形对称轴为竖直和左上-右下方向，问号处应为水平方向对称轴，D项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image15.png']},\n")

# Q13
new_questions.append("    {'id': 138, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选择最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'C', 'analysis': '前两个图形叠加后去除相同部分保留不同部分，即\u201c去同存异\u201d规律，得到第三个图形。第二组应用此规律，C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image16.png']},\n")

# Q14
new_questions.append("    {'id': 139, 'type': '图形推理', 'question_type': '单选', 'question': '根据所给图形的现有规律，选出一个最合理的答案。', 'answer': 'C', 'analysis': '观察题干图形，第一行图形封闭区域数均为1；第二行均为2；第三行前两个图形均为3，问号处应选封闭区域数为3的图形，C项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image17.png']},\n")

# Q15
new_questions.append("    {'id': 140, 'type': '图形推理', 'question_type': '单选', 'question': '从所给的四个选项中，选出最合适的一个填入问号处，使之呈现一定的规律性。', 'answer': 'D', 'analysis': '题干图形均为轴对称图形，且对称轴方向依次顺时针旋转45\u00b0，问号处应选对称轴为右上-左下方向的图形，D项符合。', 'score': 2.5, 'options': {'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D'}, 'image': ['images/docx2/image18.png']},\n")

# Insert after ID 125 line (line 125, 0-indexed)
insert_pos = 126  # after line index 125
for q in reversed(new_questions):
    lines.insert(insert_pos, q)

with open('src/exam/questions.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done! 15 new 图形推理 questions inserted (ID 126-140)")