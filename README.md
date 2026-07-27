# TIA SCL 中文注释工具 v2.0

一键给西门子博途 SCL 代码添加中文注释：**导出 → 注释 → 导回 → 编译**，全自动。

> 200+ 工控领域词典 · 信号标签解码 · 表达式拆解 · 离线运行 · 无需 API

## 效果预览

```pascal
// [输送机正转控制]
  // 当前站台
"JS_Control_MC"(Equipment := 2043,
               // 下一站台: 2046
               NextEquipment := 2046,
               // 正转发货条件: 2040#正转发货
               Send_Condition_RF := "Motor_Control".M[2040].Control.Send_Condition_RF,
               // 正转允许条件: 2043阻挡1 且 2044空闲
               ConditionRF := "PX2043_BL1" AND "SP2044_L",
               // 本站台到位光电: 2043#A1到位
               SQ_A1 := "Motor_Control".M[2043].Control.SQ_A1,
               // 下一站台信息传递光电: 2046#A1到位
               SQ_Next := "Motor_Control".M[2046].Control.SQ_A1);
```

## 功能

- **参数注释**：`Equipment` → `当前站台`，`ConditionRF` → `正转允许条件`
- **信号解码**：`"PX2043_BL1"` → `光电传感器2043低位阻挡1`
- **表达式拆解**：`"INFOR".M[2041].DATA.TaskNum = 0` → `2041#无任务`
- **控制流标记**：`IF...THEN` → `[网络1] 条件判断`
- **函数块识别**：`"JS_Control_MC"` → `[输送机正转控制]`
- **多 PLC 支持**：自动遍历项目中所有 PLC
- **分组保留**：自动记住块在项目树中的文件夹位置
- **块号保留**：导入后块号不变

## 环境要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Windows | 10 / 11 | |
| TIA Portal | V20 | 其他版本未测试 |
| TIA Openness API | V20 | [西门子官网下载](https://support.industry.siemens.com/) |
| Python | 3.10+ | 仅用标准库，无需 pip install |

## 快速开始

### 1. 安装 TIA Openness DLL

从西门子官网下载 TIA Portal Openness API，将 `Siemens.Engineering.dll` 放到：

```
C:\Users\<你的用户名>\TIA_Openness\Siemens.Engineering.dll
```

或者设置环境变量：

```cmd
set TIA_OPENNESS_DLL=D:\path\to\Siemens.Engineering.dll
```

### 2. 运行

```
1. 打开博途，加载项目
2. 双击 "一键运行.bat"
3. 等待完成
```

就是这么简单。

## 脚本说明

| 文件 | 作用 |
|------|------|
| `一键运行.bat` | 启动器，双击执行 |
| `tia_pipeline.ps1` | 核心引擎：导出 SCL → 导入回博途 → 编译 |
| `scl_commenter.py` | 注释引擎：自动添加中文注释 |

## 自定义词典

编辑 `scl_commenter.py`：

- `PARAM_DICT` — 参数名 → 中文
- `SIGNAL_SUFFIX` — 信号后缀 → 含义
- `DEVICE_PREFIX` — 设备前缀 → 类型
- `EXPR_PATTERNS` — 表达式模式 → 解码表达式
- `FB_DICT` — 函数块名 → 用途

匹配你的项目命名习惯后，覆盖率可达 **99%+**。

## 工作原理

```
tia_pipeline.ps1 (PowerShell)
  ├─ TIA Openness API → 调用 GenerateSource 导出 SCL
  ├─ 调用 Python scl_commenter.py 添加注释
  ├─ TIA Openness API → ExternalSource 导入 + 编译
  └─ 自动恢复分组和块号
```

## 限制

- 仅支持 SCL 语言块（FC / FB / OB）
- 不支持 LAD / FBD / STL / GRAPH / SFC
- 混合语言块（SCL + LAD）会被跳过
- 需要博途 UI 运行中（不能无头模式）
- 首次使用需点"允许访问"弹窗

## 免责声明

> ⚠️ **这是一个早期原型项目，处于开发阶段。**

- 目前仅在 **TIA Portal V20 + Windows 10/11** 环境测试通过
- 其他博途版本（V17/V18/V19/V21）**未经测试**，可能存在兼容性问题
- 导入操作会**替换**项目中的原有块，使用前请**备份项目**
- 本项目不包含西门子 TIA Openness API 组件，用户需自行从官方渠道获取
- **生产环境使用前请充分验证**，作者不对因使用本工具导致的任何项目损坏或生产事故承担责任

## License

MIT

## 致谢

- [tiaopen-mcp](https://github.com/eponce00/tiaopen-mcp) — TIA Openness 集成参考
- 西门子 TIA Portal Openness API
