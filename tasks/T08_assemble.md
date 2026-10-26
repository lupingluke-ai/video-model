# T08 组装舞台与整体调光

**依赖：T01–T07 全部为"完成"或"待审"。**

## 拥有的文件

`assets/build/build_stage.py`、`assets/stage.blend`、`tasks/reports/T08.md`、`tasks/reports/validation/stage/`

## 先读

全部 docs，以及 T01–T07 的报告（尤其是 T01 的灯光参数和各资产的已知问题）。

## 目标

把所有资产以**链接 + 库覆盖**的方式放进房间，得到一个可以直接拍的舞台文件。资产文件本身不复制、不修改；以后改了资产，重跑本脚本即可更新舞台。

## 步骤

1. 新建空场景，顶层集合 `STAGE`。
2. 链接 `assets/room.blend` 里的 `ROOM_SET` 集合；隐藏 `PROXIES` 子集合。
3. 链接 `XB`、`GG`、`ARM`、`FC`、`TV` 集合，分别为它们创建库覆盖：`override_hierarchy_create(scene, view_layer, do_fully_editable=True)`。不加 `do_fully_editable=True` 的话，FC_Root、TV_Root、纸页等会成为"系统覆盖"，不能移动也不能打关键帧。同时用 `bpy.data.libraries.load(path, link=True)` 显式链接各资产的动作（`data_to.actions`），带假用户的动作不会随集合自动进来。
4. 按标记点放置：XB → MARK_Host，GG → MARK_Pet_Bed，ARM → MARK_Arm_Base，FC → MARK_Flipchart，TV → MARK_TV（位置和朝向都和标记点一致）。
5. **不要把 `PROPS` 整个链接进场景**（那样 11 个道具都会出现在房间中心）。用 `libraries.load(link=True)` 只加载需要的 `PROP_<id>` 集合，在新集合 `STAGE_PROPS` 下为每个道具建一个集合实例空对象：MARK_Slot_A / B / C 各放一个（例如 chip、stopwatch、logo_tile），MARK_Prop_Source 放一个 block。
6. 各角色设为待机：XB_idle、GG_idle、ARM_home；小波 face_expr 0、screen_on 1。
7. 整体调光检查：在舞台里看 7 个机位的画面，把灯光调整**建议**（灯名 + 新参数）写进报告，由 T01 回写到 room.blend；本任务不修改灯光（房间是链接进来的，灯光数据不可编辑）。
7a. 需要每期替换内容的材质（`TV_ScreenMat`、`PROP_LogoMat`）在舞台里做本地化（`make_local()`），这样管线可以换图。
7b. 验证驱动器跟着覆盖走：把小波 `face_expr` 设为 1、`face_color` 设为琥珀色，渲一张 CAM_HostClose，确认脸和面光都变成琥珀色，然后恢复。
8. 保存 `assets/stage.blend`。
9. 用最终设置（1080p、64 采样、开体积雾）渲染 7 个机位各一张，放进 `tasks/reports/validation/stage/final/`，记录每个机位的单帧耗时。

## 验收

```bash
bash tools/blender.sh assets/build/build_stage.py
bash tools/validate.sh assets/stage.blend contracts/stage.json
```

- [ ] 验收 PASS（7 个机位都渲出预览）
- [ ] 7b 的琥珀色测试图里脸和面光颜色正确
- [ ] 7 张最终画面：角色都站在正确位置、没有悬空或穿进家具；小波的屏幕脸是主讲画面的焦点
- [ ] 改一个资产的生成脚本并重跑后，重跑 `build_stage.py` 舞台能自动更新
- [ ] 报告里有 7 个机位的单帧耗时，以及据此推算的一期（4 分钟、7200 帧）全片渲染时间
