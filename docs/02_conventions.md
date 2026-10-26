# 02 技术约定

## 坐标与单位

- 单位：米。Z 轴朝上。
- 角色和道具的**正面朝 -Y**（默认面对镜头方向）。
- 每个资产的根对象位于原点 (0, 0, 0)，资产的最低点落在 z = 0（站在地面上）。在房间里摆放时只需移动、旋转根对象。
- 帧率 30 fps。动作从第 1 帧开始。

## 文件

| 类型 | 位置 |
| --- | --- |
| 生成脚本 | `assets/build/build_<asset>.py` |
| 运行时函数库（管线会调用） | `assets/build/<asset>_motion.py` 等，见各任务卡 |
| 资产产物 | `assets/<asset>.blend`（道具统一在 `assets/props.blend`） |
| 动作库 | 动作保存在各自资产的 .blend 里（`use_fake_user = True`） |
| 资产自己生成的贴图、测试图片序列 | `assets/textures/`（只放脚本生成的原创图片） |
| 验收报告 | `tasks/reports/validation/<asset>/`（由验收脚本生成） |
| 任务报告 | `tasks/reports/Txx.md` |

.blend 保存时用 `_common.save()`（压缩、相对路径）。不要把图片打包进 .blend，外部文件放在 `library/` 下用相对路径引用。

## 命名

- 每个资产一个顶层集合，名字是资产前缀：小波 `XB`、滚滚 `GG`、机械臂 `ARM`、挂图 `FC`、电视 `TV`、道具 `PROPS`（每个道具一个子集合 `PROP_<id>`）、房间 `ROOM_SET`。
- 对象、骨骼、材质、动作都以资产前缀开头（`XB_Head`、`XB_FaceGlass`、`XB_idle`）。共享材质以 `MAT_` 开头，来自 `config/style.json`。
- 骨骼左右用 `.L` / `.R` 后缀。角色面朝 -Y，所以**角色自己的左边是 +X（`.L`），右边是 -X（`.R`）**。设定里说"右侧"一律指角色自己的右侧（-X）。
- 只用 ASCII 字母、数字、下划线和点。

## 角色的统一模式

小波、滚滚、机械臂都遵循同一个模式，管线靠它驱动：

1. **一个骨架对象**（`XB_Rig` / `GG_Rig` / `ARM_Rig`）是根，位于原点。
2. **所有零件都是硬质网格，用"骨骼父级"绑在骨骼上**（`parent_type = 'BONE'`），不刷权重。
3. **所有可动画参数都是骨架对象上的自定义属性**（例如 `XB_Rig["mouth_open"]`），用 `_common.add_prop()` 创建（带最小 / 最大值，可做库覆盖）。
4. **材质、灯光、形态键通过驱动器读取这些属性**（`_common.drive()`）。所以动画只需要给一个对象打关键帧。
5. **每个动作只作用于骨架对象**（骨骼变换 + 自定义属性），命名 `<前缀>_<动作名>`，设置 `use_fake_user = True`。
6. **静止姿态（骨架的 rest pose）**：小波双臂自然下垂、天线半伸；滚滚正立；机械臂收起成 `ARM_home` 姿态。T 字形或水平伸直的 rest pose 会让包围盒超出契约。
7. **保存前**：把骨架当前动作设为 `XB_idle` / `GG_idle` / `ARM_home`，`scene.frame_set(1)`，再保存。验收脚本在第 1 帧测量包围盒。
8. **父子关系**：资产里每个对象都必须直接或间接挂在根对象下（骨骼父级也算），因为组装时只移动根。验收脚本会检查。骨骼父级用 `_common.parent_to_bone()`，对象父级用 `_common.set_parent()`，两者都保持世界位置不变。

## Blender 5.2 API 注意事项（已在本机验证或需要注意）

- Eevee 的引擎标识符是 `BLENDER_EEVEE`（4.2–4.4 叫 `BLENDER_EEVEE_NEXT`）。用 `_common.eevee_id()`。
- `Material.use_nodes` 和 `World.use_nodes` 已弃用（运行会打印警告，6.0 移除）。5.x 新建的材质自带节点树；`_common` 已处理。
- 无界面模式下 `bpy.ops.mesh.primitive_*_add` 可以正常使用（基准测试已验证）。
- 动作是分层动作（slotted actions，4.4 起）。用 `keyframe_insert()` 打关键帧，系统会自动建槽位；不要依赖旧的 `action.fcurves` 接口。需要直接访问 F 曲线时，用 `bpy_extras.anim_utils.action_get_channelbag_for_slot(action, slot)`。
- 给骨架做多个动作时：先 `rig.animation_data_create()`，然后每做一个动作，先 `rig.animation_data.action = bpy.data.actions.new("XB_xxx")`，打完关键帧后设 `use_fake_user = True`，再做下一个。最后把骨架的当前动作设为 `XB_idle`。
- 自定义属性的范围用 `id.id_properties_ui(name).update(min=..., max=...)`（`_common.add_prop` 已封装）。
- 颜色类向量属性（如 `face_color`）创建时传 3 个浮点数的列表，加 `subtype="COLOR"`；驱动器读取单个分量时，路径写成 `["face_color"][0]`（`_common.drive(..., source_index=0)`）。
- `_common.studio_preview()` 会临时添加相机和灯光并在结束后删除。**先 `save()` 再调用预览**，否则预览灯光会被存进资产。
- 驱动器表达式尽量写成 Blender 的"简单表达式"：变量、数字、四则运算、比较、`a if 条件 else b`、`min`/`max`/`abs` 等少数数学函数，例如 `v*0.3`、`1.0 if abs(v-1) < 0.5 else 0.0`。简单表达式不需要开启 Python 自动运行，在任何环境都能算。验收脚本会把非简单表达式标为警告，把无效驱动器标为错误。
- `_common.drive()` 读取颜色分量时传 `source_index`；目标是向量（如灯光颜色）而不传 `index` 时，传 `source_index="each"` 会把三个分量一一对应驱动。
- `face_color` 等颜色属性存的是**线性 RGB**（用 `_common.rgb('teal')` 取值），不是 sRGB 十六进制。

## 三角面预算

在渲染细分级别下统计（验收脚本会自动统计）：

| 资产 | 上限 |
| --- | --- |
| 小波 | 60,000 |
| 滚滚 | 20,000 |
| 机械臂 | 20,000 |
| 挂图（不含书写内容） | 15,000 |
| 电视 | 15,000 |
| 每个道具 | 5,000（11 个合计 55,000） |
| 房间（不含角色） | 600,000 |

## 渲染默认值

见 `config/style.json` 的 `render`：Eevee，1920×1080，30 fps，最终 64 采样，预览 960×540、16 采样，色彩管理 AgX，输出 PNG。用 `_common.setup_render(scene, preview=True/False)` 统一设置。
