# T07 道具库

## 拥有的文件

`assets/build/build_props.py`、`assets/props.blend`、`assets/textures/logo_placeholder.png`、`tasks/reports/T07.md`、`tasks/reports/validation/props/`

## 先读

`docs/01_show_bible.md`（道具一节）、`docs/02_conventions.md`、`docs/04_rig_interface.md`（道具一节）、`contracts/props.json`。

## 目标

11 个原创通用道具，供机械臂抓放。全部不带真实品牌、文字商标或可识别的商业产品外形。

## 道具清单（米，每个道具底部在其根对象局部 z = 0）

| id | 描述 | 尺寸 | 配色建议 | grip_width |
| --- | --- | --- | --- | --- |
| chip | 方形芯片：深色封装 + 两侧黄铜引脚 + 顶面一个青绿圆点 | 0.06 × 0.06 × 0.012 | ink、brass、teal | 0.06 |
| server | 迷你机柜：竖长圆角盒，正面几道横槽和两颗小指示灯 | 0.05 × 0.04 × 0.08 | cream、ink、teal 灯 | 0.05 |
| stopwatch | 秒表：圆盘表身 + 顶部按钮 + 表盘刻度和指针（几何体） | 直径 0.05，厚 0.015 | brass、cream | 0.05 |
| block | 积木块：圆角立方体，表示时长或数量，可复制堆叠 | 0.04 | mustard | 0.04 |
| question | 问号方块：圆角立方体，正面凸起一个问号图形（几何体） | 0.05 | cream + orange 问号 | 0.05 |
| trophy | 奖杯：杯身 + 两个把手 + 底座 | 0.05 × 0.04 × 0.09 | brass、walnut 底座 | 0.035 |
| pricetag | 价格牌：带圆孔的吊牌形状 + 一根细绳，牌面留空 | 0.07 × 0.004 × 0.04 | cream、orange 边 | 0.005 |
| logo_tile | logo 牌：圆角方牌，正面是可替换的贴图 | 0.06 × 0.012 × 0.06（立起放） | walnut 底、贴图面 | 0.012 |
| coin | 硬币：带凸边的圆片，正面一个原创电波图案 | 直径 0.035，厚 0.005 | brass | 0.035 |
| bulb | 灯泡：玻璃泡 + 黄铜螺口，内部灯丝可发光 | 直径 0.05，高 0.08 | 玻璃、brass、amber 发光 | 0.05 |
| docs | 文件堆：3–4 张略错开的纸 + 一个回形针 | 0.07 × 0.09 × 0.01 | cream | 0.01 |

## 结构要求

- 顶层集合 `PROPS`，每个道具一个子集合 `PROP_<id>`。
- 每个道具的根空对象 `PROP_<id>`，几何体和抓取点都挂在它下面（验收会检查每个对象都挂在自己的根下）。抓取点空对象 `PROP_<id>_grab` 的高度 = max(道具高度 / 2, 0.022) 米，水平位置在道具中心。0.022 是因为机械臂的抓取点在指尖上方 2 厘米，低于这个高度指尖会插进桌面。
- 根对象上用 `_common.add_prop` 加 `grip_width`（范围 0.005–0.1）。
- 在 props.blend 里把道具沿 X 轴间隔 0.15 米排开（便于预览），并把每个子集合的 `instance_offset` 设为对应根对象的位置。
- `logo_tile` 的材质命名 `PROP_LogoMat`，正面贴图节点命名 `PROP_Logo_Image`。默认贴图由脚本生成：一张 512×512 的原创占位图（奶油底 + 青绿电波图形），保存为 `assets/textures/logo_placeholder.png`。
- 每个道具 ≤ 5,000 三角面。

## 验收

```bash
bash tools/blender.sh assets/build/build_props.py
bash tools/validate.sh assets/props.blend contracts/props.json
```

- [ ] 验收 PASS
- [ ] 预览图里 11 个道具都能一眼认出是什么，风格统一（圆润、复古、色板内配色）
- [ ] 报告里附每个道具的三角面数和 grip_width
