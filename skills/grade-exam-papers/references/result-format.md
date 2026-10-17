# JSON结果与命令

使用UTF-8 JSON，顶层含 `schema_version:1`、`title`、`rubric_source`、`pages`、`questions`，可加 `notes` 字符串数组。改变结论的识别疑点必须反映到状态，不能只藏在备注。

`rubric_source` 为 `none / user / official / suggested`；official仅在实际有正式细则时使用。单题可覆盖该字段。

## 页面

`pages`每项含唯一 `id`（如p001）和 `path`。path是本地图片；相对路径基于grading.json所在目录，不是技能目录或shell目录。可加source、source_page、width、height保留原始映射。合并prepare生成的pages.json时调整相对路径或改成绝对路径。

## 题目

| 字段 | 约定 |
|---|---|
| id | 唯一题号字符串，保留原子题号 |
| status | correct、partial、incorrect、unanswered、pending、not_provided |
| prompt | 实际识别题干，不清楚写[看不清] |
| student_steps | 有序数组，每项含text、page，可加bbox；多行跨页放同一题 |
| reference_answer | 独立求解或核验后的答案字符串，可为空并说明 |
| analysis | 判断理由、条件、给分点与未确定事项 |
| first_error | null，或含step_index、reason、correction的对象；step_index从0开始引用student_steps |
| score | 数字或null；pending/not_provided必为null |
| max_score | 正数或null；有score时必须有满分且0≤score≤max_score |
| regions | 含page、bbox的数组；没可靠坐标则为空 |
| topic | 可选知识点字符串 |
| scoring_notes | 可选评分说明字符串 |
| rubric_source | 可选，覆盖顶层 |

bbox统一为完整准备后图片的归一化 `[x0,y0,x1,y1]`，左上为原点，0≤x0<x1≤1，0≤y0<y1≤1。例如1200×1600图上区域[120,320,720,640]对应[0.1,0.2,0.6,0.4]。裁剪图上的坐标须先换回完整图。page只可引用pages里的ID。没有可指认的已写错误时，first_error可为null，例如缺少结论的partial。

## 调用

```bash
python <skill-dir>/scripts/exam_tool.py prepare input.pdf image.png --out work/pages --dpi 160
python <skill-dir>/scripts/exam_tool.py validate work/grading.json
python <skill-dir>/scripts/exam_tool.py export work/grading.json --out output --pdf
```

prepare依输入顺序、PDF原页序输出；PDF需要PyMuPDF，图片需Pillow。export读取AI实际写出的识别批改结果，不做OCR、不调用模型、不解题。--pdf需要PyMuPDF。

## 输出与统计

- report.html：自包含中文报告与嵌入标注图。输入文字全部转义，不执行试卷中的HTML。公式以文本或LaTeX源码呈现。
- results.json：原批改数据、重新计算的statistics和导出文件清单；不信任输入旧统计。
- annotated-p001.png等：完整页面，英文短标签如X #2，对应报告中“标注#2”。不可靠坐标留空并在报告说明。
- annotated-paper.pdf：可选，按页序合并的标注原卷，不是讲解排版报告。
- judged = correct + partial + incorrect + unanswered；pending与not_provided不进入正确率分母。分母0时正确率null。
- earned_scored与possible_scored仅累加有分数的题；complete_total仅在所有题都已明确判断且都有分数时给出，否则null。即使分数完整，也披露建议评分来源。
- unanswered只表示确认空白，不等于未提供；无细则时不能默认0/100。

没有执行环境时按此逻辑提供聊天版结论，不模拟生成文件与链接。
