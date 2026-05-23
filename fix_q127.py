import sys
sys.path.insert(0, 'src')

with open('src/exam/questions.py', 'r') as f:
    content = f.read()
exec(compile(content, 'questions.py', 'exec'))

for q in QUESTIONS:
    if q['id'] == 127:
        q['options'] = {
            'A': '\u2460\u2461\u2462\uff0c\u2463\u2464\u2465',
            'B': '\u2460\u2464\u2465\uff0c\u2461\u2462\u2463',
            'C': '\u2460\u2461\u2463\uff0c\u2462\u2464\u2465',
            'D': '\u2460\u2462\u2464\uff0c\u2461\u2463\u2465'
        }
        q['analysis'] = '\u89c2\u5bdf\u53d1\u73b0\uff0c\u9886\u9898\u56fe\u5f62\u5747\u51fa\u73b0\u9ed1\u7403\u4e0e\u767d\u7403\uff0c\u4e14\u6bcf\u5e45\u56fe\u5747\u6709\u4e24\u4e2a\u9ed1\u7403\u548c\u4e24\u4e2a\u5957\u5708\u767d\u7403\u3002\u5c06\u4e24\u4e2a\u9ed1\u7403\u8fde\u7ebf\uff0c\u4e24\u4e2a\u5957\u5708\u767d\u7403\u8fde\u7ebf\uff0c\u89c2\u5bdf\u53d1\u73b0\uff0c\u56fe\u2460\u2461\u2463\u4e2d\u9ed1\u7403\u8fde\u7ebf\u4e0e\u5957\u5708\u767d\u7403\u8fde\u7ebf\u4e92\u76f8\u5782\u76f4\uff0c\u56fe\u2462\u2464\u2465\u4e2d\u4e92\u76f8\u5e73\u884c\u3002\u6545\u6b63\u786e\u7b54\u6848\u4e3aC\u3002'
        break

code = '"""广铁就业题库 - 完整题库"""\n\nfrom typing import Any\n\n'
code += 'QUESTIONS: list[dict[str, Any]] = [\n'
for q in QUESTIONS:
    code += '    {\n'
    for key in ('id', 'type', 'question_type', 'question', 'answer', 'analysis', 'score'):
        val = q.get(key)
        if isinstance(val, str):
            code += f'        "{key}": {repr(val)},\n'
        elif isinstance(val, (int, float)):
            code += f'        "{key}": {val},\n'
    opts = q.get('options')
    if opts is None:
        code += '        "options": None,\n'
    else:
        code += '        "options": {\n'
        for k, v in opts.items():
            code += f'            {repr(k)}: {repr(v)},\n'
        code += '        },\n'
    img = q.get('image')
    if img:
        code += f'        "image": {repr(img)},\n'
    code += '    },\n'
code += ']\n'

with open('src/exam/questions.py', 'w', encoding='utf-8') as f:
    f.write(code)

exec(compile(code, 'questions.py', 'exec'))
q127 = [q for q in QUESTIONS if q['id'] == 127][0]
print('=== 验证ID 127 ===')
print('A:', q127['options']['A'])
print('B:', q127['options']['B'])
print('C:', q127['options']['C'])
print('D:', q127['options']['D'])
print('答案:', q127['answer'])
print('A!=C:', q127['options']['A'] != q127['options']['C'])