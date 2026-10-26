# T06 复古电视

## 拥有的文件

`assets/build/build_tv.py`、`assets/build/tv_media.py`、`assets/build/tv_demo.py`、`assets/tv.blend`、`assets/textures/tv_idle.png`、`assets/textures/tv_test_seq/`、`tasks/reports/T06.md`、`tasks/reports/validation/tv/`

## 先读

`docs/01_show_bible.md`（电视一节）、`docs/02_conventions.md`、`docs/04_rig_interface.md`（电视一节）、`contracts/tv.json`。

## 造型规格（米，底部 z = 0，正面朝 -Y）

- **机身** `TV_Body`：0.56 宽 × 0.42 深 × 0.46 高的圆角箱体，两侧和顶面胡桃木（MAT_Walnut），正面面板奶油色或深色，四只短腿（总高含腿不超过 0.52）。
- **屏幕** `TV_Screen`：4:3，0.42 × 0.315，略外凸的曲面（细分平面加轻微球面形变），正面右侧留出旋钮区。UV 0–1 铺满屏幕，U 向右、V 向上，不能拉伸。
- **旋钮** `TV_Knob_1` / `TV_Knob_2`：黄铜圆柱旋钮，带刻度纹。
- **天线** `TV_Antenna`：顶部一对细长的 V 形天线，含天线总高不超过 0.85。
- **推进终点** `TV_PushTarget`：空对象，位于屏幕中心正前方，朝向屏幕（局部 -Z 指向屏幕，和相机约定一致）。加自定义属性 `lens_mm = 35`。距离按 35 mm 镜头、36 mm 传感器、`sensor_fit = 'HORIZONTAL'` 计算：让 16:9 画面的宽度刚好等于屏幕宽度的 95%（这样画面完全落在屏幕内），约 0.388 米。

## 屏幕材质 TV_ScreenMat

节点链：图像纹理节点（**节点名必须是 `TV_Media`**）→ 乘以 `glow` → 叠加扫描线（沿 V 方向的细条纹，强度 `scanline`）→ 乘以暗角（到 UV 中心的距离）→ 发光输出；再混一点玻璃反射（低粗糙度）。

`TV_Root` 上的属性：`screen_on`（0–1，0 时全黑；0→1 的过程是一条亮横线从中间上下展开）、`scanline`（默认 0.35）、`glow`（默认 1.0）。用驱动器把这些属性接到材质节点上。

默认图像：脚本里用 `bpy.data.images.new` 生成一张 640×480 的原创测试图（色板颜色的竖条 + 中心一个青绿电波图形），保存到 `assets/textures/tv_idle.png`，作为待机画面。

## 运行时函数（tv_media.py）

```python
def set_media(path, frame_start=1, kind="movie", loop=False, material=None):
    """把 TV_Media 节点的图像换成 path（视频、单张图片或图片序列）。material 为空时用
    bpy.data.materials['TV_ScreenMat']；舞台里该材质是链接的，调用方先本地化再传入。
    视频 / 序列设置 image_user 的 frame_start、frame_duration、use_auto_refresh；单张图片直接替换。"""

def power(frame, on=True, frames=10):
    """给 TV_Root['screen_on'] 打开机（0→1）或关机（1→0）的关键帧。"""
```

## 演示（tv_demo.py）

新建场景放电视和一台相机。用脚本生成 30 帧的原创测试图片序列（一个色块从左移到右），放到 `assets/textures/tv_test_seq/`。演示：第 1–10 帧开机，第 11–40 帧播放序列，再从正常机位推到 `TV_PushTarget`。每 3 帧渲一张 540p 到 `tasks/reports/validation/tv/demo/`。

## 验收

```bash
bash tools/blender.sh assets/build/build_tv.py
bash tools/validate.sh assets/tv.blend contracts/tv.json
bash tools/blender.sh assets/build/tv_demo.py
```

- [ ] 验收 PASS，三角面 ≤ 15,000
- [ ] 演示里屏幕画面清晰、扫描线和暗角可见但不影响看清内容；开机效果是一条横线展开
- [ ] 推进到 `TV_PushTarget` 的那一帧，画面四边都在屏幕范围内
