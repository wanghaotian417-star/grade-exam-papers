# 文件与代码分层

## 技能层

SKILL.md定义操作流程与交付口径；references保存结果协议、数学检查点与来源鸣谢；assets保存结构模板和图标；agents保存平台展示信息。技能目录可独立安装。

## 代码层

| 模块 | 责任 | 依赖方向 |
|---|---|---|
| scripts/exam_tool.py | 解析命令行，分派prepare/validate/export，处理错误与退出码 | 调用业务模块 |
| exam_grader/preparation.py | 图片方向与透明背景处理、PDF渲染、源文件/页码映射 | common |
| exam_grader/validation.py | JSON结构、页面引用、坐标、首错索引与评分一致性；统计分母 | common |
| exam_grader/reporting.py | 原图标注、HTML转义、嵌入图像、JSON与PDF导出 | common、validation |
| exam_grader/common.py | 状态常量、JSON读写、可选依赖加载与基础图片转换 | 标准库、Pillow/PyMuPDF |

准备页面后，AI负责视觉识别、独立解题及逐步批改，并输出grading.json；validate检查协议，export读取已校验的数据生成交付物。代码不承担AI识别或学科判断。

## 验证与发布层

- tests使用临时目录和合成页面，检查跨页保留、正确率分母、局部得分、无效数据拒绝、HTML转义、标注位置及PDF导出。
- tools/build_release.py按排序与固定ZIP时间戳打包，仅纳入完整技能目录，剔除缓存文件，生成SHA-256；同样输入生成同样字节。
- dist保存给用户和AI直接下载的ZIP；开发文档、测试不混入安装包。
- requirements.txt列出运行依赖；README提供下载入口与目录导航。

## 修改与复核

修改行为后运行 `python -m unittest discover -s tests -v`。修改技能规则或代码后重新执行 `python tools/build_release.py`，保证dist与源码一致。通过ZIP的SHA-256校验文件确认下载完整性。

真实试卷和生成报告属于运行数据，不放进公开仓库。work、output、inputs和.env已列入.gitignore；发布前仍检查提交文件列表，不把测试通过等同于任意手写试卷的识别准确率。
