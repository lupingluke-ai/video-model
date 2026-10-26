# 派发给 Agent 的提示词

把下面的提示词原样发给任意一个能在这台 Mac 上运行命令的 Agent（Claude Code、Codex、Kimi CLI 等）。把 `Txx_xxx` 换成具体任务卡文件名。

## 单个任务

```
你在 ~/Documents/personal/video-model 目录工作。
先完整阅读 AGENTS.md，再按它列出的顺序阅读 docs/ 下的文档，然后执行 tasks/T02_xiaobo.md 这个任务。
严格遵守 AGENTS.md 的硬性规则，只修改任务卡"拥有的文件"里列出的路径。
开始时先运行 T00 环境自测；完成后运行任务卡里的全部验收命令，打开生成的预览图亲自检查外观，
写好 tasks/reports/T02.md，并把 tasks/STATUS.md 里你的任务改成"待审"。
遇到无法解决的问题，把问题写进报告，不要绕过规则。
```

## 一个 Agent 带多个子 Agent 并行

```
你在 ~/Documents/personal/video-model 目录工作，担任这个项目的协调者。
先完整阅读 AGENTS.md 和 tasks/STATUS.md。
1. 自己运行一次 T00 环境自测。
2. 为 T01–T07 各启动一个子 Agent，并行执行。给每个子 Agent 的指令是：
   "你在 ~/Documents/personal/video-model 工作。先读 AGENTS.md 和 docs/ 下全部文档，然后执行 tasks/<任务卡>。
    只修改任务卡里'拥有的文件'列出的路径。完成后写报告、更新 STATUS.md 你那一行为'待审'。"
3. 子 Agent 全部结束后，逐个检查它们的验收结果（tasks/reports/validation/*/report.md）和预览图；
   有 FAIL 的让对应子 Agent 修正，直到全部 PASS。
4. 然后自己执行 tasks/T08_assemble.md。
5. 最后汇总：每个任务的状态、三角面数、已知问题，以及 T08 里测得的单帧渲染时间和一期全片渲染时间估算。
```

## 返工

```
你在 ~/Documents/personal/video-model 目录工作。先读 AGENTS.md。
任务 T02 已完成第一版，审核意见如下：<粘贴意见>。
请修改 assets/build/build_xiaobo.py（以及任务卡里你拥有的其他文件），重新运行全部验收，
更新 tasks/reports/T02.md 的"修改记录"一节，并把 STATUS.md 改回"待审"。
```
