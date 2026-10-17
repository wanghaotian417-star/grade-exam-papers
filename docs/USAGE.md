# 使用说明

## 交给AI使用

1. 从仓库首页的“直接下载技能包”取得ZIP。
2. 将ZIP和试卷图片/PDF交给有视觉与文件读取能力的AI。
3. 要求解压、读取SKILL.md，并按技能识别和批改。若平台可安装Skill，导入完整grade-exam-papers目录后调用该技能。
4. 有标准答案、题目分值或评分细则时一并提供。不提供分值时默认仅判题，不假定每题100分。

支持本地技能发现的Codex环境可将完整grade-exam-papers目录放入技能目录，再使用 `$grade-exam-papers` 发起任务。不要只复制SKILL.md或exam_tool.py，否则会缺少引用资料或代码模块。

## 输入与输出

输入可为单张图片、多张图片或多页PDF；图片以Pillow可读取格式为限，不保证HEIC支持。拍摄时保留题干、图形和完整答题区域。识别不清会标为待确认，不等于错误。

默认输出逐题判断、完整步骤、首错原因与修正。具备Python执行能力时可另输出HTML、JSON、标注图片及PDF。HTML公式以可读文本/LaTeX源码展示；PDF是带标注的原卷，不是讲解排版稿。

## 本地工具

在仓库根目录安装依赖：

```bash
python -m pip install -r requirements.txt
python skills/grade-exam-papers/scripts/exam_tool.py prepare paper.pdf --out work/pages
```

AI实际查看页面、完成批改后，按[JSON协议](../skills/grade-exam-papers/references/result-format.md)写work/grading.json，再执行：

```bash
python skills/grade-exam-papers/scripts/exam_tool.py validate work/grading.json
python skills/grade-exam-papers/scripts/exam_tool.py export work/grading.json --out output --pdf
```

页面清单中的相对路径在合并到grading.json时须调整；所有坐标基于准备后的完整页面。输出目录必须为空，以避免覆盖已有文件。没有可靠坐标时留空，不能编造错误位置。

脚本不会看图解题、不会调用模型，也不会自行上传试卷；识别与批改依赖宿主AI。没有执行环境时仍可获得聊天版批改。
