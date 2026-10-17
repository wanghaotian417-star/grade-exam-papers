# 试卷识别与批改 Skill

面向具备视觉理解能力的AI助手：识别图片、手写作业和多页PDF，保留完整推导，逐题检查、定位首错、按依据评分，并生成原图标注与批改报告。

[![下载此 Skill](./docs/assets/download-skill.svg)](https://raw.githubusercontent.com/wanghaotian417-star/grade-exam-papers/main/dist/grade-exam-papers-v1.0.0.zip)

[技能包 v1.0.0](https://raw.githubusercontent.com/wanghaotian417-star/grade-exam-papers/main/dist/grade-exam-papers-v1.0.0.zip) · [使用说明](./docs/USAGE.md) · [AI技能入口](./skills/grade-exam-papers/SKILL.md)

## 使用

下载ZIP，与试卷一起交给支持文件读取和视觉理解的AI，让它解压并读取 `grade-exam-papers/SKILL.md`，按照技能进行批改。支持导入Skill的平台也可直接导入完整目录。当前AI完成识别与学科判断，配套脚本完成页面准备、校验和导出；不强制配置额外模型API。

## 功能

- 保留同题多行与跨页推导，逐步检查而非只对最后答案。
- 定位首个实质错误，解释原因并给出修正方法。
- 按已有评分细则给过程分；建议细则明确标注，不编造官方标准。
- 区分确认空白、识别不清与未提供的区域，材料不足时待确认。
- 输出自包含HTML报告、JSON结果、标注PNG和可选标注试卷PDF。

重点适配数学；其他学科需可靠题意与评分依据。生成文件需要Python执行环境，纯文字模型不能仅凭技能获得看图能力。识别效果取决于照片清晰度与宿主AI能力。

## 文件分层

| 目录/文件 | 职责 |
|---|---|
| `skills/grade-exam-papers/` | 可安装技能，含规则、参考资料、模板和脚本 |
| `skills/grade-exam-papers/scripts/exam_tool.py` | 命令入口 |
| `skills/grade-exam-papers/scripts/exam_grader/` | 页面处理、数据校验、统计和导出模块 |
| `docs/` | 用户说明、代码架构与鸣谢 |
| `tests/` | 自动化功能验证，不包含真实学生试卷 |
| `tools/` | 可复现打包脚本 |
| `dist/` | 可直接下载的技能ZIP与SHA-256校验值 |
| `requirements.txt` | 本地工具运行依赖 |

## 本地验证与打包

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tools/build_release.py
```

详见[代码架构](./docs/ARCHITECTURE.md)。配套脚本不执行OCR或调用AI模型；AI须先完成真实识别和批改，再写入结构化结果。

## 鸣谢

感谢 **[jetlane](https://github.com/jetlane) 及 [math-paper-grading](https://github.com/jetlane/math-paper-grading) 项目的贡献者** 分享数学试卷智能批改项目，为“图片识别 → AI批改 → 原图标记”的功能设计提供启发。

本技能的工作流与本地工具独立编写，并增加完整过程保留、首错分析、评分依据与识别疑点处理。[完整鸣谢](./docs/ACKNOWLEDGMENTS.md)也保留在可下载技能包内。

## 许可证

按仓库选定的 [MIT License](./LICENSE) 发布；技能下载包内也包含同一许可证。
