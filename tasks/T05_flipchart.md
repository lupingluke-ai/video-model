# T05 翻页挂图

## 拥有的文件

`assets/build/build_flipchart.py`、`assets/build/flipchart_draw.py`、`assets/build/flipchart_demo.py`、`assets/flipchart.blend`、`library/fonts/`（若新增字体）、`library/LICENSES.md`（只追加）、`tasks/reports/T05.md`、`tasks/reports/validation/flipchart/`

## 先读

`docs/01_show_bible.md`（挂图一节）、`docs/02_conventions.md`、`docs/04_rig_interface.md`（挂图一节）、`contracts/flipchart.json`。

## 造型规格（米，底部 z = 0，正面朝 -Y）

- **画架** `FC_Easel`：木质三脚架，两条前腿 + 一条后腿，顶部高约 1.75；前腿间有一根托板横档（z ≈ 0.75）。MAT_Walnut、MAT_Brass 五金。
- **画板** `FC_Board`：0.72 × 0.97 的薄板，下沿搁在横档上，略向后倾约 8°。
- **纸页** `FC_Page_00` … `FC_Page_09`：每页 0.70 × 0.95，细分成可以弯曲的网格（约 12 × 16 段），逐页叠在画板前面（**页间隔 2 毫米**，00 在最外面）。MAT_Paper。上沿有一根夹条 `FC_Clamp`。
- **马克笔筒** `FC_MarkerCup`：挂在画架右侧，里面插三支笔（ink / orange / teal 三色笔帽）。

## 翻页

每页自定义属性 `flip`（0–1）。旋转轴是页面上沿：`flip` 驱动绕上沿的旋转（0 → 贴在画板上，1 → 翻过顶部垂到画板背后，约 200°）；同时用"简单形变 / 弯曲"修改器让纸在翻动中途弯起来，弯曲量 = sin(π × flip) × 系数。内容空对象 `FC_Page_NN_Content` 放在该页左上角，挂在该页上，随页翻动。

## 书写函数（flipchart_draw.py）

纸面坐标：以 `FC_Page_NN_Content` 为原点，+X 向右、-Z 向下，单位米（页面范围 x 0–0.70，z 0 到 -0.95）。所有内容离自己的纸面 0.5 毫米（小于页间隔，所以不会穿到上一页），避免闪烁。颜色只用色板 `ink`、`orange`、`teal`。

```python
def write_text(page, text, x, z, size, color="ink", t_start=1, t_end=None, font=None) -> list:
    """逐字出现的手写文字。每个字一个文字对象（或转成曲线 / 网格），在 t_start 到 t_end 之间依次出现
    （每个字有 3 帧的"写出"动画：从左到右的擦除式显现，或从 0 缩放到 1 加轻微抖动）。"""

def draw_path(page, points, color="teal", width=0.006, t_start=1, t_end=30, wobble=0.0015, seed=0) -> object:
    """手绘线条：points 为纸面坐标折线 [(x, z), ...]，做成带倒角的曲线，用 bevel_factor_end 从 0 到 1 实现逐笔画出；
    wobble 给线条加一点手抖（固定种子）。"""

def draw_shape(page, kind, x, z, w, h, color="orange", t_start=1, t_end=20, seed=0) -> object:
    """kind ∈ {"arrow", "circle", "underline", "box", "check"}，基于 draw_path。"""

def flip_page(page, t_start, frames=18) -> int:
    """给该页 flip 属性打 0→1 的关键帧（缓入缓出），返回结束帧。"""
```

`page` 是页号整数 0–9。

**字体**：中文必须用支持中文的可商用字体（推荐 SIL OFL 授权的手写风格字体，例如"霞鹜文楷 LXGW WenKai"或 Google Fonts 上的 Long Cang、Ma Shan Zheng；以字体自带的授权文件为准）。放进 `library/fonts/`，在 `library/LICENSES.md` 记录来源和授权。如果你无法下载，在报告里标明"需要人工放入字体"，先用 Blender 自带字体写英文和数字完成其余部分。

## 演示（flipchart_demo.py）

新建场景放入挂图，正面相机。第 0 页：第 1–40 帧写标题"三个步骤"，第 40–100 帧画三个方框和两个箭头组成的流程图，第 100–120 帧用 orange 圈出第二个方框；第 130 帧开始翻到第 1 页，第 1 页写一行字。每 3 帧渲一张 540p 到 `tasks/reports/validation/flipchart/demo/`。

## 验收

```bash
bash tools/blender.sh assets/build/build_flipchart.py
bash tools/validate.sh assets/flipchart.blend contracts/flipchart.json
bash tools/blender.sh assets/build/flipchart_demo.py
```

- [ ] 验收 PASS，三角面 ≤ 15,000（不含书写内容）
- [ ] 演示图里文字逐字出现、线条逐笔画出、翻页时纸有弯曲且内容跟着翻
- [ ] 内容和纸面之间没有闪烁；下面几页的内容不会从上一页透出来
- [ ] 中文字体可用（或在报告里标明需要人工放入字体）
