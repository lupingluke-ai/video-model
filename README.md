# 小波深夜电台 · 3D 资产

这个文件夹是《小波深夜电台》的全部 3D 资产和生成脚本。资产由 Agent 按任务卡用脚本生成。

- 给 Agent 看的总入口：`AGENTS.md`
- 派发任务的提示词：`tasks/PROMPTS.md`
- 进度：`tasks/STATUS.md`
- 本机渲染实测：`docs/05_render_benchmark.md`

## 快速开始（人工）

在终端里：

```bash
cd ~/Documents/personal/video-model
bash tools/blender.sh tools/selftest.py --tag manual   # 环境自测，结果在 tests/results/selftest_manual.json
```

然后把 `tasks/PROMPTS.md` 里的提示词发给 Agent。T01–T07 可以同时交给不同 Agent，T08 最后做。

## 目录

```
AGENTS.md            Agent 总说明（规则、环境、任务图、完成标准）
config/style.json    色板、材质、灯光初始值、渲染设置、面数预算（唯一的颜色来源）
docs/                设定、约定、房间布局、接口、渲染实测
contracts/           每个资产的接口契约（验收脚本按它检查）
tasks/               任务卡 T00–T08、状态表、提示词、报告
assets/build/        生成脚本；_common.py 是公共库
assets/              生成出来的 .blend
tools/               blender.sh（运行脚本）、validate.sh（验收）、selftest.py
tests/               基准测试与自测
library/             动作、表情、音效、字体等外部资源及授权记录
```
