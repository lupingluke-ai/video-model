# T00 环境自测

**每个 Agent 开工前都要跑一次。** 只写带自己任务号的输出：`tests/selftest/<tag>/`、`tests/results/selftest_<tag>*`。

## 步骤

1. 确认项目根目录是 `~/Documents/personal/video-model`，并且存在 `AGENTS.md`、`config/style.json`、`assets/build/_common.py`。
2. 运行：
   ```bash
   bash tools/blender.sh tools/selftest.py --tag T02     # 换成你的任务号
   ```
3. 打开 `tests/results/selftest_<tag>.json`，确认 `"status": "PASS"`，五个步骤（build / parenting / save / preview / validate）都是 `ok`。
4. 打开 `tests/results/selftest_<tag>_previews/ST_threequarter.png`，应该看到一个奶油色圆角方块，正面有一块青绿色发光屏幕。

## 如果失败

- 找不到 Blender：用 `BLENDER=/实际路径/Blender bash tools/blender.sh ...`。
- 你的运行环境不能直接执行 macOS 程序（例如你在 Linux 虚拟机或沙盒里）：停下来，在报告里说明，请人工在本机终端运行上面的命令，或者在 Blender 的 Python 控制台里执行：
  ```python
  import subprocess, os; d = os.path.expanduser('~/Documents/personal/video-model'); subprocess.Popen([bpy.app.binary_path, '-b', '--factory-startup', '-y', '-P', d + '/tools/selftest.py', '--', '--tag', 'T02'])
  ```
- 其他报错：把 `tests/results/selftest_<tag>.json` 的 `error` 字段贴进你的任务报告。
