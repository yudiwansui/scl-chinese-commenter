#!/usr/bin/env python3
"""
SCL 自动中文注释工具 v2
用法: python scl_commenter.py <输入目录或文件> [输出目录]
v2 新增: 项目函数块注释 + 全参数词典 + 设备类型识别
"""

import sys
import os
import re
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# 项目函数块词典 (你们项目的标准库)
# ═══════════════════════════════════════════════════════════════════

FB_DICT = {
    "JS_Control_MC":           "输送机正转控制",
    "JS_Control_BF":           "输送机反转控制",
    "JS_Control_INV":          "移栽输送机控制",
    "JS_Control_2KM":          "双接触器电机控制",
    "MC_DB":                   "电机控制数据块",
    "Overstep":                "超边报警检测",
    "SQ_Check":                "光电自检",
    "AbnormalControl":         "异常控制处理",
    "YV_UpDn_Control":         "升降控制",
    "YV_Door_Control":         "门控制",
    "YV_STOP_Control":         "阻挡控制",
    "2YV_DW_Control":          "双阀升降控制",
    "Cross_Control":           "交叉控制",
    "IonFanControl":           "离子风机控制",
    "GET_GW":                  "取货",
    "PUT_GW":                  "放货",
    "LTF":                     "提升机控制",
    "Area_Safety":             "区域安全控制",
    "MainCtrl":                "主控制器",
    "NetDiagnostic":           "网络诊断",
    "Driver_IO_Insert":        "驱动IO接入",
    "CB_Contal":               "断路器控制",
    "OP_CB_Control":           "操作断路器",
    "EnergyInstrumentation":   "能源仪表",
    "IO_Monitoring":           "IO监控",
    "INFO_Change":             "信息变更",
    "Create_Clean_INFO":       "信息清理",
    "YV_UpDn_DIR":             "升降方向控制",
    "JS_BatteryJack":          "电池顶升控制",
    "ROB_control":             "机器人控制",
    "Robot_CV":                "机器人输送",
    "HMI_INFOR":               "HMI信息交互",
    "AutooilerControl":        "自动注油器",
    "SRM_Control":             "堆垛机控制",
    "SRM_CV_Ctrl":             "堆垛机输送",
}


# ═══════════════════════════════════════════════════════════════════
# 参数词典 (你们项目的命名约定)
# ═══════════════════════════════════════════════════════════════════

PARAM_DICT = {
    # ── 设备/工位 ──
    "Equipment":               "当前站台",
    "EquipmentINFO":           "信息站台",
    "NextEquipment":           "下一站台",
    "NextEquipmentINFO":       "下一站台信息",
    "Equipment_RF":            "正转目标站台",
    "Equipment_BF":            "反转目标站台",
    "OP_Num":                  "工位号",
    "VirtuallyEquipment":      "虚拟站台",
    "LTF_Equipment":           "提升机站台号",
    "AlarmEquipment":          "报警站台号",
    "Station1":                "工位1",
    "Station2":                "工位2",
    "ZD_Num":                  "止挡编号",

    # ── 模式/命令 ──
    "Modle":                   "模式(1=标准)",
    "Mode":                    "模式",
    "IN":                      "入库标志",
    "IsIn":                    "是否在库内",
    "Allow_IN":                "允许入库",
    "Req_IN":                  "请求入库",
    "Cross":                   "交叉标志",
    "AUTO":                    "自动模式",
    "AUTO_SA":                 "自动/手动旋钮",

    # ── 操作命令 ──
    "ocmdAuto":                "自动命令",
    "ocmdManl":                "手动命令",
    "ocmdFwd":                 "正转命令",
    "ocmdRev":                 "反转命令",
    "ocmdLow":                 "低速命令",
    "ManulRF":                 "手动正转",
    "ManulBF":                 "手动反转",
    "ManulUp":                 "手动上升",
    "ManulDn":                 "手动下降",
    "ManulRF_Ban":             "手动正转禁止",
    "ManulBF_Ban":             "手动反转禁止",
    "Manual_Condition":        "手动条件",

    # ── 限位/到位 (SQ) ──
    "SQ_A1":                   "本站台到位光电",
    "SQ_A2":                   "下一站台到位光电",
    "SQ_D1":                   "D1工位到位",
    "SQ_SA1":                  "SA1入库口到位",
    "SQ_S":                    "托盘保护光电",
    "SQ_SH":                   "超高检测光电",
    "SQ_SE1":                  "升降到位1",
    "SQ_SE2":                  "升降到位2",
    "SQ_SE3":                  "升降到位3",
    "SQ_SRGV":                 "提升机到位",
    "SQ_Next":                 "下一站台信息传递光电",
    "SQNext_A1":               "下一站台A1到位",
    "SQ_Protect":              "保护光电",
    "SQ_Protect1":             "保护光电1",
    "SQ_Protect2":             "保护光电2",
    "SQ_Check":                "到位检测",

    # ── 光电阻挡 (SP) ──
    "SP_0":                    "原点光电",
    "SP_O":                    "出口光电",
    "SP_H":                    "高位光电",
    "SP_L":                    "低位光电",
    "SP_BH":                   "阻挡高位光电",
    "SP_SC1":                  "特殊光电1",
    "SP_SW1":                  "特殊光电2",
    "SP_KHZ_Open":             "开合光电(开)",
    "SP_KHZ_Close":            "开合光电(关)",

    # ── 光电传感器 (PX) ──
    "PX_H":                    "高位",
    "PX_L":                    "低位",
    "PX_BH":                   "阻挡高位",
    "PX_BL":                   "阻挡低位",
    "PX_LBEX":                 "顶升伸出",
    "PX_LBRE":                 "顶升缩回",
    "PX_TD":                   "防呆(磁开推出到位)",
    "PX_BL1":                  "阻挡1",

    # ── 脉冲传感器 (ML) ──
    "ML_BT1":                  "微动开关1",
    "ML_BT2":                  "微动开关2",
    "ML_TD":                   "方向检测(托盘正反)",

    # ── 电磁阀 (YV) ──
    "YV_UP":                   "上升阀",
    "YV_Up":                   "上升阀",
    "YV_DN":                   "下降阀",
    "YV_Down":                 "下降阀",
    "YV_TD":                   "通道阀",
    "YV_LBEX":                 "顶升伸出阀",
    "YV_OUT":                  "输出阀",
    "YV_ZD":                   "阻挡输出",
    "YV_STOP":                 "阻挡阀",
    "YV_Door":                 "门阀",
    "YV_LBEX":                 "侧推",
    "YV_LBEX =>":              "侧推输出",

    # ── 放行条件 ──
    "ConditionRF":             "正转允许条件",
    "ConditionBF":             "反转允许条件",
    "Send_Condition_RF":       "正转发货条件",
    "Send_Condition_bF":       "反转发货条件",
    "ConditionRun":            "运行条件",
    "Run_Condition":           "运行条件",
    "UP_Condition":            "上升条件",
    "DN_Condition":            "下降条件",
    "BW_Condition":            "反向条件",
    "Add_Condition":           "附加条件",
    "Add_ConditionNoBan1":     "放行豁免条件1",
    "Add_ConditionNoBan2":     "放行豁免条件2",
    "Add_Codition1":           "附加条件1(拼写)",
    "Add_Codition2":           "附加条件2(拼写)",
    "AddRunCondition":         "附加运行条件",
    "OtherCondition":          "其他条件",

    # ── 速度 ──
    "LSpeed_Add":              "低速附加",
    "LSpeed_Condition":        "低速条件",

    # ── 按钮/安全 ──
    "Btn_Emergency":           "急停按钮",
    "Btn_Start":               "启动按钮",
    "EStop":                   "急停信号",
    "Reset":                   "复位信号",
    "RESET":                   "复位信号",
    "btn":                     "按钮",
    "backup11":                "复位备份标志",

    # ── 断路器/继电器 ──
    "QF":                      "断路器",
    "QF_CV":                   "变频器断路器已合闸",
    "KA_OUT":                  "继电器输出",
    "KM_I":                    "接触器输入",
    "SV660F_PZD":              "变频器过程数据",

    # ── 状态 ──
    "Finish":                  "完成信号",
    "Finish_ACK":              "完成确认",
    "Fault":                   "故障信号",
    "Scapegoat":               "替身信号/防呆",
    "Trip7":                   "跳闸信号",
    "SQ_Check":                "光电自检信号",
    "First":                   "首站标志",
    "RUN_CW":                  "正转运行",
    "RUN_CCW":                 "反转运行",

    # ── 货物信息 ──
    "GoodsEnd":                "货物终点站",
    "Goodstype":               "货物类型",
    "PH_A":                    "相位A",
    "PT":                      "预设时间",

    # ── 其他 ──
    "S7_Optimized_Access":     "优化访问",
    "X45":                     "故障位45",
    "X54":                     "故障位54",

    # ── 块属性 ──
    "ExternalAccessible":      "外部可访问",
    "ExternalVisible":         "外部可见",
    "ExternalWritable":        "外部可写",

    # ── 状态/显示 ──
    "Status_Display":          "状态显示",
    "Run_Direction":           "运行方向",
    "Load":                    "负载",
    "RunMark":                 "运行标记",
    "DriveBan":                "驱动禁止",
    "NoTask":                  "无任务",
    "Task":                    "有任务",
    "stAuto":                  "自动状态",
    "stManl":                  "手动状态",
    "Select":                  "选择模式",
    "ErrorCode":               "错误码",
    "EquipmentType":           "设备类型(1输送/2顶升/3移栽/4提升/5提升机/6旋转)",
    "FW_LowSpeed":             "正转低速",
    "BW_LowSpeed":             "反转低速",
    "Ari_H":                   "高位",

    # ── 故障位 ──
    "X1":                      "故障位1",
    "X7":                      "故障位7",
    "X8":                      "故障位8",
    "X9":                      "故障位9",
    "X59":                     "故障位59",

    # ── 跳闸/检测 ──
    "SQ_CheckTrip1":           "跳闸检测1",
    "Overstep_PH":             "超边相位",

    # ── 堆垛机 ──
    "SRM_Num":                 "堆垛机号",
    "DOCK":                    "站台号",

    # ── 抱闸 ──
    "ML_BT":                   "抱闸",

    # ── 返回值/块 ──
    "RET_VAL_1":               "返回值",
    "SRCBLK":                  "源数据块",

    # ── BLKMOV 参数 ──
    "area_src":                "源区域",
    "dbNumber_src":            "源DB号",
    "byteOffset_src":          "源字节偏移",
    "area_dest":               "目标区域",
    "dbNumber_dest":           "目标DB号",
    "byteOffset_dest":         "目标字节偏移",
    "count":                   "字节数",
    "DSTBLK":                  "目标数据块(BLKMOV)",

    # ── 方向/运行状态 ──
    "Direction_Swith":         "方向切换",
    "RF_RUNNING":              "正转运行中",
    "BF_RUNNING":              "反转运行中",
    "bForward":                "正转使能",
    "bReverse":                "反转使能",
    "bSystemOK":               "系统就绪",
    "bTaskOK":                 "任务就绪",
    "bCanTransfer":            "可输送",
    "NextTaskNum":             "下一任务号",
    "NextGoodsEnd":            "下一货物终点",
    "CurrentTaskNum":          "当前任务号",
    "CurrentGoodsEnd":         "当前货物终点",
    "Get_Put":                 "取放货操作",
    "TaskNum":                 "任务号",
    "Btn_LED":                 "按钮指示灯",
    "SafetySignal_NUM":        "安全信号数",
    "RESETMAINT":              "复位维护",
    "EquipmentStatusColors":   "设备状态颜色",

    # ── 急停 ──
    "ESOP1":                   "急停1",
    "ESOP2":                   "急停2",
    "ESMAINT":                 "急停指示",
    "ESMAINT_HL1":             "急停灯1",
    "FaultMAINT_HL1":          "故障灯1",
    "HL_Y1":                   "黄灯1",
    "HL_G1":                   "绿灯1",
    "HL_R1":                   "红灯1",
    "HA1":                     "蜂鸣器1",

    # ── 断路器映射 ──
    "CB":                      "断路器",
    "CB1":                     "断路器1号",
    "CB2":                     "断路器2号",
    "CB3":                     "断路器3号",
    "CB4":                     "断路器4号",
    "CB5":                     "断路器5号",
    "Timer_DB":                "定时器DB",
    "GetPut_1":                "取放货模式",
    "RUN":                     "运行信号",

    # ── HMI 子项 ──
    "HMI_Ready":               "HMI就绪",
    "HMI_Auto":                "HMI自动",
    "Ready":                   "就绪",
    "AUTO":                    "自动",
    "Fault":                   "故障",
    "safetyMap":               "安全地图弹出",
    "Silence_SB":              "消音按钮",
    "Silence_Bit":             "消音标志",
    "N_TRIG1":                 "下降沿暂存",
    "PMH":                     "触摸屏站台号",
    "backup12":                "备份字12",
    "RESET":                   "复位",
}


# ═══════════════════════════════════════════════════════════════════
# 设备类型前缀识别 (用于扫描代码中的信号标签)
# ═══════════════════════════════════════════════════════════════════

DEVICE_PREFIX = {
    "PX":  "光电传感器",
    "SP":  "光电阻挡",
    "SQ":  "限位/到位",
    "ML":  "脉冲/传动传感器",
    "YV":  "电磁阀",
    "LC":  "漏缆/计数",
    "EMS": "急停",
    "SB":  "按钮",
    "SA":  "选择开关",
    "MC":  "电机控制",
    "QF":  "断路器",
    "KA":  "继电器",
    "KM":  "接触器",
    "SV":  "变频器",
    "LTF": "提升机",
    "WCS": "仓储控制系统",
    "HMI": "触摸屏",
    "EMS": "急停信号",
    "SB":  "按钮",
    "SA":  "选择开关",
    "HL":  "指示灯",
    "HA":  "蜂鸣器",
    "MCP": "主控面板",
    "SBMCP": "主控面板按钮",
    "NTI": "堆垛机",
    "CB":  "断路器",
    "SRM": "堆垛机",
    "INV": "变频器",
    "IO_": "IO模块",
    "MC_": "电机IO",
    "HLOP": "指示灯(OP)",
    "HLMCP": "指示灯(主控)",
    "KMMCP": "接触器(主控)",
}


# ═══════════════════════════════════════════════════════════════════
# 信号后缀词典 (解码信号标签的含义)
# ═══════════════════════════════════════════════════════════════════

SIGNAL_SUFFIX = {
    # 位置
    "A1":      "到位A1",
    "A2":      "到位A2",
    "D1":      "到位D1",
    "SA1":     "入库口到位",
    "S":       "出库口到位",
    "SH":      "超高",
    "SH1":     "超高检测",
    "SE1":     "升降到位1",
    "SE2":     "升降到位2",
    "SE3":     "升降到位3",
    "SRGV":    "提升机到位",
    "Next":    "下游到位",

    # 光电状态
    "H":       "高位",
    "L":       "低位",
    "BH":      "高位阻挡",
    "BH1":     "高位阻挡1",
    "BL":      "低位阻挡",
    "BL1":     "低位阻挡1",
    "O":       "出口",
    "0":       "原点",
    "SC1":     "特殊1",
    "SW1":     "特殊2",
    "KHZ_Open":  "开合开",
    "KHZ_Close": "开合关",
    "LBEX":    "侧推动作",
    "LBRE":    "顶升缩回",
    "TD":      "通道检测",

    # 抱闸/脉冲
    "BT1":     "微动1",
    "BT2":     "微动2",

    # 电磁阀
    "UP":      "上升",
    "DN":      "下降",
    "Down":    "下降",
    "Up":      "上升",
    "H1":      "上升",
    "STOP":    "阻挡",
    "ZD":      "阻挡",
    "LBEX":    "侧推动作",
    "Door":    "门",
    "OUT":     "输出",

    # 特殊
    "MA":      "自动/手动",
    "FB_FW":   "正转旋钮",
    "FB_BW":   "反转旋钮",
    "HL_UP":   "手动升",
    "HL_DN":   "手动降",
    "_R":      "复位",
    "1":       "",
    "2":       "",
    "Protect1": "保护1",
    "Protect2": "保护2",
    "Protect":  "保护",
    "S1":      "镜反超边保护",
    "S2":      "对射超边保护",
    "S1_1":    "检测1-1",
    "PZD":     "过程数据",
    "1_Q":     "确认灯",
    "Q":       "输出",

    # 三色灯
    "HLY":     "黄灯",
    "HLG":     "绿灯",
    "HLR":     "红灯",
    "HA":      "蜂鸣器",

    # 指示灯
    "ESMAINT_HL":  "急停指示",
    "FaultMAINT_HL": "故障指示",
    "SILENCEMAINT_HL": "消音指示",
    "ESMAINT":   "急停指示",
    "FaultMAINT": "故障指示",
    "SILENCEMAINT": "消音指示",

    # 更多传感器后缀
    "S3":      "到位3",
    "SE":      "升降到位",
    "FW":      "正转",
    "BW":      "反转",
    "FB_FW":   "正转旋钮",
    "FB_BW":   "反转旋钮",
    "HL_UP":   "手动升",
    "HL_DN":   "手动降",
    "MA":      "自动/手动",
    "OPN":     "开门",
    "CLS":     "关门",
    "ST":      "状态",
    "RUN":     "运行",
    "ALM":     "报警",
    "RST":     "复位",
    "HL":      "灯",
    # HL_UP means HL+UP → 灯上升
    "UP":      "上升",
    "DN":      "下降",
    "SBR":     "系统复位",
    "SB1":     "启动按钮",
    "SB2":     "停止按钮",
    "BZ":      "蜂鸣器",
}


def decode_signal(tag: str) -> str:
    """解码信号标签: PX2043_BL1 -> 2043工位阻挡电眼(低位阻挡1)"""
    tag = tag.strip('"')
    # 匹配 前缀+数字+_后缀 模式
    m = re.match(r'^([A-Z]{2,4})(\d+)(?:_(.*))?$', tag)
    if not m:
        return ""

    prefix = m.group(1)
    station = m.group(2)
    suffix = m.group(3) or ""

    parts = []
    # 前缀 -> 设备类型
    if prefix in DEVICE_PREFIX:
        parts.append(DEVICE_PREFIX[prefix])
    else:
        parts.append(prefix)

    # 站台号
    parts.append(station)

    # 后缀解码
    if suffix:
        suffix_parts = suffix.split("_")
        decoded = []
        for sp in suffix_parts:
            if sp in SIGNAL_SUFFIX and SIGNAL_SUFFIX[sp]:
                decoded.append(SIGNAL_SUFFIX[sp])
            elif sp in SIGNAL_SUFFIX:
                pass  # empty string = skip
            else:
                decoded.append(sp)
        if decoded:
            parts.append("/".join(decoded))

    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
# 表达式模式解码 (拆解布尔条件中的子表达式)
# ═══════════════════════════════════════════════════════════════════

EXPR_PATTERNS = [
    # INFOR 数据
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.TaskNum\s*=\s*0', r'\1#无任务'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.TaskNum\s*<>\s*0', r'\1#有任务'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.TaskNum\s*=\s*(\d+)', r'\1#任务号=\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*>\s*(\d+)', r'\1#货物终点>\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*<\s*(\d+)', r'\1#货物终点<\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*>=\s*(\d+)', r'\1#货物终点>=\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*<=\s*(\d+)', r'\1#货物终点<=\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*=\s*(\d+)', r'\1#货物终点=\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*<>\s*(\d+)', r'\1#货物终点≠\2'),
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*>\s*(\d+)\s*AND', r'\1#货物终点>\2'),  # partial
    (r'"INFOR"\.M\[(\d+)\]\.DATA\.GoodsEnd\s*<\s*(\d+)\s*AND', r'\1#货物终点<\2'),  # partial
    # Motor_Control
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.First\s*=\s*(\d+)', r'\1#首站=\2'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.Send_Condition_RF', r'\1#正转发货'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.Send_Condition_BF', r'\1#反转发货'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_A1', r'\1#A1到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_D1', r'\1#D1到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_S1', r'\1#S1到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_SA1', r'\1#SA1到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_A2', r'\1#A2到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.SQ_D2', r'\1#D2到位'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.Task', r'\1#有任务'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.NoTask', r'\1#无任务'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.DriverBan', r'\1#驱动禁止'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.FW_LowSpeed', r'\1#正转低速'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Button\.ocmdManl', r'\1#手动'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Button\.ocmdAuto', r'\1#自动'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Button\.ocmdFwd', r'\1#正转按钮'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Button\.ocmdRev', r'\1#反转按钮'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Status\.stAuto', r'\1#自动状态'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Status\.Run_Direction\s*=\s*(\d+)', r'\1#运行方向=\2'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.ManulBF_Ban', r'\1#手动反转禁止'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.Station_H', r'\1#高位状态'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.Station_L', r'\1#低位状态'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Control\.ManulRF', r'\1#手动正转'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Status\.Fault', r'\1#故障'),
    (r'"Motor_Control"\.M\[(\d+)\]\.Status\.ErrorCode', r'\1#错误码'),
    (r'"Motor_Control"\.M\[(\d+)\]\.ErrorCode\.%X(\d+)', r'\1#故障位X\2'),
    # 提升机 LTF
    (r'"LTF(\d+)"\.Station\s*=\s*(\d+)', r'提升机在\2#位'),
    (r'"LTF(\d+)"\.Get_Stn\s*=\s*(\d+)', r'提升机取货->\2#'),
    (r'"LTF(\d+)"\.Put_Stn\s*=\s*(\d+)', r'提升机放货->\2#'),
    (r'"LTF(\d+)"\.Condition\[(\d+)\]\.Send_RF', r'提升机\1正转发货\2'),
    (r'"LTF(\d+)"\.Condition\[(\d+)\]\.Get_RF', r'提升机\1取货发车\2'),
    (r'"LTF(\d+)"\.Condition\[(\d+)\]\.Send_BF', r'提升机\1反转发货\2'),
    (r'"LTF(\d+)"\.Condition\[(\d+)\]\.Get_BF', r'提升机\1取货发车\2'),
    # 简单信号标签 (PX/SP/SQ/YV 等)
    (r'"([A-Z]{2,4}\d+(?:_\w+)*)"', lambda m: decode_signal(m.group(1)) or m.group(1)),
    # MC_DB 电机块
    (r'"MC_DB(\d+)"\.BatteryJackDB\.bCylinder_DSDX_Low', r'MC\1#气缸低位'),
    # WCS STATUS
    (r'"WCS_STATUS"\.M\[(\d+)\]\.ErrorCode\.MBL_HomeFault', r'\1#原位故障'),
    (r'"STATUS"\.M\[(\d+)\]\.ErrorCode\.%X(\d+)', r'\1#故障位X\2'),
    # HMI
    (r'"HMI_Control"\.OP\[(\d+)\]\.(\w+)\.backup(\d+)', r'HMI工位\1.\2.备份\3'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.(\w+)\.RESET', r'HMI工位\1.\2.复位'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.(\w+)\.Fault', r'HMI工位\1.\2.故障'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.ManulRF', r'HMI工位\1手动正转'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.ManulBF', r'HMI工位\1手动反转'),
    (r'"SBMCP(\d+)_R"', r'工位\1总复位'),
    # STATUS patterns
    (r'"STATUS"\.M\[(\d+)\]\.ErrorCode\.%X(\d+)', r'\1#故障位X\2'),
    (r'"STATUS"\.M\[(\d+)\]\.Fault', r'\1#故障'),
    (r'"STATUS"\.M\[(\d+)\]\.RESET_TRIG', r'\1#复位触发'),
    (r'"STATUS"\.M\[(\d+)\]\.Select', r'\1#选择'),
    (r'"STATUS"\.M\[(\d+)\]\.ErrorCode', r'\1#错误码'),
    (r'"STATUS"\.M\[(\d+)\]\.WarnCode\.%X(\d+)', r'\1#警告位X\2'),
    (r'"STATUS"\.M\[(\d+)\]\.Run_Direction\s*=\s*(\d+)', r'\1#运行方向=\2'),
    # Timer
    (r'"Timer"\.M\[(\d+)\]', r'计时器\1'),
    (r'"Timer_INFO"\.M\[(\d+)\]', r'信息计时\1'),
    # FireDoor
    (r'"FireDoor_DB"\.M\[(\d+)\]\.(\w+)', r'防火门\1.\2'),
    # CylinderRunTime
    (r'"CylinderRunTime"\.M\[(\d+)\]\.(\w+)', r'气缸计时\1.\2'),
    # Area Safety
    (r'"Area_Safety_DB"\.OP\[(\d+)\]\.SafetySignal\[', r'安全区\1#信号['),
    (r'"Date_TO_Safety"\.OP\[(\d+)\]\.(\w+)', r'安全写\1.\2'),
    (r'"Date_From_Safety"\.OP\[(\d+)\]\.(\w+)', r'安全读\1.\2'),
    # NTI_SRM (stacker crane)
    (r'"NTI_SRM_1"\."#"\[(\d+)\]"\."NTI_SRM"\.STA_No\[(\d+)\]\.%X(\d+)', r'堆垛机\1站台\2位X\3'),
    (r'"NTI-XXX"\.M\[(\d+)\]\.Input\.RF_Get', r'\1#取货信号'),
    (r'"NTI-XXX"\.M\[(\d+)\]\.Output\.RF_Get', r'\1#取货命令'),
    # CB (circuit breaker)
    (r'"CB"\."(\w+)"\[(\d+)\]\.(\w+)', r'断路器\1\2.\3'),
    # IO
    (r'"IO_String"\.(\w+)\[(\d+)\]\.(\w+)', r'IO字\1\2.\3'),
    (r'"MC_IO"\.M\[(\d+)\]\.(\w+)', r'电机IO\1.\2'),
    (r'"INV_IO"\.M\[(\d+)\]\.(\w+)', r'变频IO\1.\2'),
    (r'"INV_IO"\.M_LIFT\[(\d+)\]\.(\w+)', r'变频IO升降\1.\2'),
    # HMI Control patterns
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.Ready', r'HMI\1#就绪'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.AUTO', r'HMI\1#自动'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.Fault', r'HMI\1#故障'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.safetyMap', r'HMI\1#安全地图'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.Silence_SB', r'HMI\1#消音按钮'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.Silence_Bit', r'HMI\1#消音标志'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.N_TRIG1', r'HMI\1#下降沿'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.PMH', r'HMI\1#站台号'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.backup12\.%X(\d+)', r'HMI\1#备份X\2'),
    (r'"HMI_Control"\.OP\[(\d+)\]\.HMI_Control\.backup11', r'HMI\1#备份11'),
    # MainCtrl_DB
    (r'"MainCtrl_DB"\."(\w+)"', r'主控.\1'),
    # Simple signals
    (r'"([A-Z]{2,4}\d+(?:_\w+)*)"', lambda m: decode_signal(m.group(1)) or m.group(1)),
    # Simple values
    (r'\b(\d+)\b', r'\1'),
    (r'\bTRUE\b', '真'),
    (r'\bFALSE\b', '假'),
]


def decode_expression(expr: str) -> str:
    """将布尔表达式拆解为中文描述"""
    # 按 AND/OR 分割
    parts = re.split(r'\s*\b(AND|OR)\b\s*', expr)
    result_parts = []

    for part in parts:
        part = part.strip()
        if part in ('AND', 'OR'):
            op_cn = '且' if part == 'AND' else '或'
            result_parts.append(op_cn)
            continue

        if not part or part in ('(', ')'):
            continue

        # 去掉外层括号和 NOT
        inner = part
        prefix = ''
        was_parens = False
        while inner.startswith('(') and inner.endswith(')'):
            inner = inner[1:-1].strip()
            was_parens = True
        # 不成对括号
        inner = inner.strip('()')
        while inner.startswith('NOT '):
            inner = inner[4:].strip()
            prefix = '非' + prefix

        # 如果括号内有 AND/OR，递归解析
        if was_parens and (' AND ' in inner or ' OR ' in inner):
            translated = decode_expression(inner)
            result_parts.append(prefix + translated)
            continue

        # 匹配模式
        matched = False
        # 第一轮：精确全匹配
        for pattern, replacement in EXPR_PATTERNS:
            if callable(replacement):
                continue  # callable 跳过全匹配
            m = re.fullmatch(pattern, inner)
            if m:
                result_parts.append(prefix + m.expand(replacement))
                matched = True
                break

        if not matched:
            # 第二轮：宽松搜索匹配（所有模式）
            for pattern, replacement in EXPR_PATTERNS:
                m = re.search(pattern, inner)
                if m:
                    if callable(replacement):
                        translated = replacement(m)
                    else:
                        translated = m.expand(replacement)
                    result_parts.append(prefix + translated)
                    matched = True
                    break

        if not matched:
            result_parts.append(part)

    return ' '.join(result_parts)


# ═══════════════════════════════════════════════════════════════════
# SCL 指令词典
# ═══════════════════════════════════════════════════════════════════

INSTRUCTION_DICT = {
    "FUNCTION_BLOCK": "功能块",
    "FUNCTION": "功能",
    "ORGANIZATION_BLOCK": "组织块",
    "DATA_BLOCK": "数据块",
    "BEGIN": "程序开始",
    "END_FUNCTION_BLOCK": "功能块结束",
    "END_FUNCTION": "功能结束",
    "END_ORGANIZATION_BLOCK": "组织块结束",

    "VAR": "局部变量",
    "VAR_INPUT": "输入变量",
    "VAR_OUTPUT": "输出变量",
    "VAR_IN_OUT": "输入输出变量",
    "VAR_TEMP": "临时变量",
    "VAR_STAT": "静态变量",
    "VAR_CONSTANT": "常量",
    "END_VAR": "变量声明结束",

    "IF": "条件判断",
    "ELSIF": "否则如果",
    "ELSE": "否则",
    "END_IF": "条件结束",
    "CASE": "多分支选择",
    "END_CASE": "多分支结束",
    "FOR": "循环",
    "END_FOR": "循环结束",
    "WHILE": "条件循环",
    "END_WHILE": "循环结束",
    "REPEAT": "重复循环",
    "END_REPEAT": "循环结束",
    "RETURN": "返回",

    "TON": "接通延时定时器",
    "TOF": "断开延时定时器",
    "TP": "脉冲定时器",
    "TONR": "保持型定时器",
    "CTU": "加计数器",
    "CTD": "减计数器",
    "CTUD": "加减计数器",

    "R_TRIG": "上升沿检测",
    "F_TRIG": "下降沿检测",
    "SR": "置位优先",
    "RS": "复位优先",

    "MOVE": "传送",
    "CONV": "类型转换",
    "ADD": "加法",
    "SUB": "减法",
    "MUL": "乘法",
    "DIV": "除法",
    "MOD": "取模",
    "ABS": "绝对值",
    "SCALE_X": "缩放",
    "NORM_X": "归一化",
    "SEL": "二选一",
    "MAX": "取最大值",
    "MIN": "取最小值",
    "LIMIT": "限幅",
}


def match_fb_name(call_name: str) -> str:
    """匹配函数块名称，返回中文描述"""
    for key, desc in FB_DICT.items():
        if key in call_name:
            return desc
    return ""


def get_param_comment(param_name: str) -> str:
    """获取参数名的中文注释"""
    if param_name in PARAM_DICT:
        return PARAM_DICT[param_name]
    return ""


def get_device_label(tag: str) -> str:
    """识别设备标签前缀，返回设备类型"""
    # 匹配 PX2043_BL1, SQ2036_A1 这类
    m = re.match(r'("?)([A-Z]{2,4})(\d+)', tag.strip('"'))
    if m:
        prefix = m.group(2)
        if prefix in DEVICE_PREFIX:
            return DEVICE_PREFIX[prefix]
    return ""


def get_instruction_comment(code: str) -> str:
    """识别 SCL 指令并返回中文注释（跳过基础控制流关键字）"""
    cleaned = re.sub(r'//.*$', '', code).strip()
    cleaned = re.sub(r"'.*?'", '', cleaned)
    cleaned = re.sub(r'".*?"', '', cleaned)

    skip_basic = {"END_VAR", "BEGIN", "DO", "TO", "BY", "OF",
                  "THEN", "IF", "ELSE", "ELSIF", "END_IF",
                  "CASE", "END_CASE", "FOR", "END_FOR",
                  "WHILE", "END_WHILE", "REPEAT", "END_REPEAT",
                  "RETURN", "=", ":=", "AND", "OR", "NOT", "XOR",
                  ">", "<", ">=", "<=", "<>", "S", "R",
                  "AT", "RETAIN", "VAR", "VAR_INPUT", "VAR_OUTPUT",
                  "VAR_TEMP", "VAR_STAT", "VAR_CONSTANT", "VAR_IN_OUT",
                  "BOOL", "INT", "REAL", "DINT", "WORD", "DWORD",
                  "BYTE", "LREAL", "SINT", "UINT", "UDINT", "LINT",
                  "STRING", "WSTRING", "TIME", "DATE", "TOD",
                  "ARRAY", "STRUCT", "REF_TO"}

    tokens = re.findall(r'[A-Za-z_]\w*', cleaned)
    comments = []
    for token in tokens:
        upper = token.upper()
        if upper in INSTRUCTION_DICT and upper not in skip_basic:
            comments.append(INSTRUCTION_DICT[upper])

    return " | ".join(comments) if comments else ""


def is_blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("//"):
        return True
    if stripped.startswith("(*") and stripped.endswith("*)"):
        return True
    return False


def annotate_line(line: str, indent: int) -> list:
    """对单行代码生成行内参数注释"""
    result = []

    # 跳过注释行和空行
    stripped = line.strip()
    if is_blank_or_comment(line) or stripped in ("BEGIN", "END_VAR",
        "END_REGION", "END_FUNCTION_BLOCK", "END_FUNCTION",
        "END_ORGANIZATION_BLOCK"):
        return result

    # 函数块实例化调用（如 "JS_Control_MC"(Equipment := 2043, ...）
    fb_call = re.match(r'^(\s*)"(\w[\w.]*)"\s*\(', line)
    if fb_call:
        fb_name = fb_call.group(2)
        indent_str = fb_call.group(1)
        # 去掉版本号后缀
        base_name = re.sub(r'V\d+\.\d+$', '', fb_name)
        desc = match_fb_name(base_name)
        if desc:
            result.append(f"{indent_str}// [{desc}]\n")
        # 同行的第一个参数也注释
        first_param = re.match(r'^\s*"\S+"\s*\(\s*(\w+)\s*:=\s*(.+?),?\s*$', stripped)
        if first_param:
            pname = first_param.group(1)
            pval = first_param.group(2).strip()
            cn = get_param_comment(pname)
            if cn:
                sig = decode_signal(pval) if re.match(r'^"[A-Z]{2,4}\d+[^"]*"$', pval) else ""
                extra = f" -> {sig}" if sig else ""
                result.append(f"{indent_str}  // {cn}{extra}\n")
        return result

    # 参数赋值行: ParamName := Value, (也匹配 "ParamName" 引号形式)
    param_assign = re.match(r'^(\s+)"?(\w+)"?\s*:=\s*(.+?),?\s*$', line)
    if param_assign:
        leading = param_assign.group(1)
        pname = param_assign.group(2)
        pval = param_assign.group(3).strip()
        cn = get_param_comment(pname)
        if cn:
            # 信号解码 (简单单值)
            sig = decode_signal(pval) if re.match(r'^"[A-Z]{2,4}\d+[^"]*"$', pval) else ""
            # 表达式解码 (含 AND/OR 的条件值)
            if not sig:
                sig = decode_expression(pval)
            extra = f": {sig}" if sig and sig.strip() not in ('0','1','真','假') else ""
            result.append(f"{leading}// {cn}{extra}\n")
        return result

    # 输出参数: ParamName => Value,
    out_param = re.match(r'^(\s+)(\w+)\s*=>\s*(.+?),?\s*$', line)
    if out_param:
        leading = out_param.group(1)
        pname = out_param.group(2)
        pval = out_param.group(3).strip()
        cn = get_param_comment(pname)
        if cn:
            sig = decode_signal(pval) if re.match(r'^"[A-Z]{2,4}\d+[^"]*"$', pval) else ""
            if not sig:
                sig = decode_expression(pval)
            extra = f": {sig}" if sig and sig.strip() not in ('0','1','真','假') else ""
            result.append(f"{leading}// {cn}{extra}\n")
        return result

    # 引号变量赋值: "VarName" := expr, (如 "SQ_Check" := "SQ1021_ST")
    quoted_var = re.match(r'^(\s*)"(\w+)"\s*:=\s*(.+?),?\s*$', line)
    if quoted_var:
        leading = quoted_var.group(1)
        pname = quoted_var.group(2)
        cn = get_param_comment(pname)
        if cn:
            pval = quoted_var.group(3).strip()
            sig = decode_signal(pval) if re.match(r'^"[A-Z]{2,4}\d+[^"]*"$', pval) else ""
            if not sig: sig = decode_expression(pval)
            extra = f": {sig}" if sig and sig.strip() not in ('0','1','真','假') else ""
            result.append(f"{leading}// {cn}{extra}\n")
        return result

    # 简单赋值: var := expr; (也匹配 "DB".M[N].Field := )
    simple_assign = re.match(r'^(\s*)(?:".+?"\.\S+\.)?#?(\w+)\s*:=', line)
    if simple_assign:
        vname = simple_assign.group(2)
        cn = get_param_comment(vname)
        if cn:
            leading = simple_assign.group(1)
            # 提取值部分并解码
            code_part = re.sub(r'//.*$', '', stripped).rstrip(',;')
            expr = re.sub(r'^\s*(?:".+?"\.\S+\.)?\w+\s*:=\s*', '', code_part)
            decoded = decode_expression(expr)
            if decoded and decoded != expr and decoded.strip() not in ('0','1','真','假',''):
                result.append(f"{leading}// {cn}: {decoded}\n")
            else:
                result.append(f"{leading}// {cn}\n")
        return result

    return result


def process_scl_file(input_path: str, output_path: str = None, verbose: bool = True):
    with open(input_path, 'r', encoding='utf-8-sig', errors='replace') as f:
        lines = f.readlines()

    # Merge continuation lines (TIA Portal wraps long params across lines)
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        # If this is a param assignment with no comma (ignoring trailing //) before end, merge
        code_part = re.sub(r'//.*$', '', stripped).rstrip()
        if re.match(r'\s{3,}\w+\s*:=', line) and not code_part.endswith(',') and not code_part.endswith(';'):
            j = i + 1
            while j < len(lines):
                nextline = lines[j]
                # Only merge if next line is indented continuation (starts with . or spaces)
                # Only merge if next line looks like a continuation (not a new param :=)
                next_stripped = re.sub(r'//.*$', '', nextline).strip()
                if re.match(r'\s{6,}[\.\w"\']', nextline) and not re.search(r':=', next_stripped):
                    line = line.rstrip('\n\r') + ' ' + next_stripped
                    j += 1
                else:
                    break
            merged.append(line)
            i = j
        else:
            merged.append(line)
            i += 1
    lines = merged

    result_lines = []
    block_name = os.path.splitext(os.path.basename(input_path))[0]

    result_lines.append(f"// {'='*60}\n")
    result_lines.append(f"// 文件: {block_name}\n")
    result_lines.append(f"// 自动中文注释 by scl_commenter v2\n")
    result_lines.append(f"// {'='*60}\n\n")

    in_var_section = False
    network_num = 0

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        # ── POU 声明 ──
        pou_match = re.match(
            r'^\s*(FUNCTION_BLOCK|FUNCTION|ORGANIZATION_BLOCK|DATA_BLOCK)\s+',
            stripped, re.IGNORECASE)
        if pou_match:
            pou_type = pou_match.group(1).upper()
            cn = INSTRUCTION_DICT.get(pou_type, pou_type)
            result_lines.append(f"// {'='*50}\n")
            result_lines.append(f"// {cn}: {block_name}\n")
            result_lines.append(f"// {'='*50}\n")
            result_lines.append(line)
            continue

        # ── REGION 标签 ──
        region_match = re.match(r'^\s*REGION\s+(.+)', stripped, re.IGNORECASE)
        if region_match:
            label = region_match.group(1).strip()
            result_lines.append(f"\n// ── {label} ──\n")
            result_lines.append(line)
            continue

        # ── 变量区 ──
        var_section_match = re.match(
            r'^\s*(VAR_INPUT|VAR_OUTPUT|VAR_IN_OUT|VAR_TEMP'
            r'|VAR_STAT|VAR_CONSTANT|VAR_GLOBAL)\b',
            stripped, re.IGNORECASE)
        if var_section_match:
            in_var_section = True
            result_lines.append(f"\n// ── {INSTRUCTION_DICT.get(var_section_match.group(1).upper(), '')} ──\n")
            result_lines.append(line)
            continue

        if re.match(r'^\s*VAR\b', stripped, re.IGNORECASE):
            in_var_section = True
            result_lines.append(f"\n// ── 局部变量 ──\n")
            result_lines.append(line)
            continue

        if re.match(r'^\s*END_VAR\b', stripped, re.IGNORECASE):
            in_var_section = False
            result_lines.append(line)
            result_lines.append("\n")
            continue

        # ── 变量声明行 ──
        if in_var_section and not is_blank_or_comment(line):
            var_decl = re.match(r'^(\s*)(\w+)\s*(AT\s+%\S+)?\s*:\s*(\S.*?);', stripped)
            if var_decl:
                varname = var_decl.group(2)
                cn = get_param_comment(varname)
                if cn:
                    result_lines.append(f"{var_decl.group(1)}// {cn}\n")
                result_lines.append(line)
                continue

        # ── END_VAR / END_REGION 之后加空行 ──
        if re.match(r'^\s*END_(REGION|FUNCTION_BLOCK|FUNCTION|ORGANIZATION_BLOCK)\b',
                     stripped, re.IGNORECASE):
            result_lines.append(line)
            continue

        # ── 控制流结构 ──
        if not is_blank_or_comment(line):
            has_section = False
            if re.match(r'^\s*IF\b', stripped, re.IGNORECASE):
                network_num += 1
                result_lines.append(f"\n// [网络{network_num}] 条件判断 ------\n")
                has_section = True
            elif re.match(r'^\s*ELSIF\b', stripped, re.IGNORECASE):
                result_lines.append(f"// ── 否则如果 ──\n")
                has_section = True
            elif re.match(r'^\s*ELSE\b', stripped, re.IGNORECASE):
                result_lines.append(f"// ── 否则 ──\n")
                has_section = True
            elif re.match(r'^\s*END_IF\b', stripped, re.IGNORECASE):
                result_lines.append(f"// ── 条件结束 ──\n")
                has_section = True
            elif re.match(r'^\s*CASE\b', stripped, re.IGNORECASE):
                network_num += 1
                result_lines.append(f"\n// [网络{network_num}] 多分支选择 ------\n")
                has_section = True
            elif re.match(r'^\s*END_CASE\b', stripped, re.IGNORECASE):
                result_lines.append(f"// ── 多分支结束 ──\n")
                has_section = True
            elif re.match(r'^\s*FOR\b', stripped, re.IGNORECASE):
                network_num += 1
                result_lines.append(f"\n// [网络{network_num}] 循环 ------------──\n")
                has_section = True
            elif re.match(r'^\s*WHILE\b', stripped, re.IGNORECASE):
                network_num += 1
                result_lines.append(f"\n// [网络{network_num}] 条件循环 ------────\n")
                has_section = True
            elif re.match(r'^\s*REPEAT\b', stripped, re.IGNORECASE):
                network_num += 1
                result_lines.append(f"\n// [网络{network_num}] 重复循环 ------────\n")
                has_section = True
            elif re.match(r'^\s*RETURN\b', stripped, re.IGNORECASE):
                result_lines.append(f"// ── 返回 ──\n")
                has_section = True

            # 函数块调用注释
            if not has_section:
                fb_annotations = annotate_line(line, indent)
                result_lines.extend(fb_annotations)

                # 指令注释（TON/CTU/MOVE等）
                instr_cn = get_instruction_comment(stripped)
                if instr_cn and not fb_annotations:
                    result_lines.append(f"{' ' * indent}// {instr_cn}\n")

        result_lines.append(line)

        # 表达式解码已合并到 annotate_line 的参数注释中，此处不需要
        pass

    # 写入
    if output_path is None:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}.scl"

    # Clean and write
    content = ''.join(result_lines)
    # Strip ALL BOM characters (anywhere in file)
    content = content.replace('\ufeff', '')
    # Strip (*...*) block comments (SCL compiler can choke on these)
    content = re.sub(r'\(\*.*?\*\)', '', content, flags=re.DOTALL)
    # Remove TITLE/AUTHOR/FAMILY/VERSION metadata (ExternalSource import rejects these)
    content = re.sub(r'\n\s*(?:TITLE|AUTHOR|FAMILY|VERSION)\s*[:=][^\n]*', '', content)
    # Replace non-ASCII chars that SCL compiler rejects
    replacements = {
        # Box drawing -> ASCII
        '\u2500': '-', '\u2502': '|', '\u2550': '=', '\u2551': '|',
        '\u256d': '+', '\u256e': '+', '\u256f': '+', '\u2570': '+',
        '\u250c': '+', '\u2510': '+', '\u2514': '+', '\u2518': '+',
        '\u2554': '+', '\u2557': '+', '\u255a': '+', '\u255d': '+',
        '\u252c': '+', '\u2534': '+', '\u251c': '+', '\u2524': '+',
        # Arrows -> ASCII
        '\u2192': '->', '\u2190': '<-', '\u2191': '^', '\u2193': 'v',
        # CJK punctuation -> ASCII (SCL compiler rejects these)
        '\u3001': ',',   # 、
        '\u3002': '.',   # 。
        '\u3000': ' ',   # fullwidth space
        '\uff01': '!',   # fullwidth !
        '\uff1f': '?',   # fullwidth ?
    }
    for old, new in replacements.items():
        content = content.replace(old, new)

    # Write as UTF-8 with BOM (same encoding as GenerateSource output)
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)

    return {
        'input': input_path,
        'output': output_path,
        'lines_in': len(lines),
        'lines_out': len(result_lines),
        'networks': network_num,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python scl_commenter.py <输入目录或SCL文件> [输出目录]")
        print("\n示例:")
        print("  python scl_commenter.py FB_Motor.scl")
        print("  python scl_commenter.py D:\\scl_export\\ D:\\scl_注释版\\")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if input_path.is_file():
        out = None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out = str(output_dir / f"{input_path.stem}.scl")
        stat = process_scl_file(str(input_path), out)
        print(f"[OK] {stat['input']}")
        print(f"  -> {stat['output']}")
        print(f"  行数: {stat['lines_in']} -> {stat['lines_out']}")
        print(f"  网络段: {stat['networks']}")

    elif input_path.is_dir():
        scl_files = list(input_path.rglob("*.scl")) + list(input_path.rglob("*.SCL"))
        if not scl_files:
            print(f"[ERR] 未找到 .scl 文件: {input_path}")
            sys.exit(1)

        out_dir = output_dir or Path(str(input_path) + "_注释版")
        out_dir.mkdir(parents=True, exist_ok=True)

        total = 0
        for scl_file in scl_files:
            try:
                rel = scl_file.relative_to(input_path)
                out_dir_target = out_dir / rel.parent
                out_dir_target.mkdir(parents=True, exist_ok=True)
                out = str(out_dir_target / f"{scl_file.stem}.scl")
                stat = process_scl_file(str(scl_file), out, verbose=False)
                print(f"[OK] {scl_file.name}: {stat['lines_in']}行->{stat['lines_out']}行, {stat['networks']}段")
                total += 1
            except Exception as e:
                print(f"[ERR] {scl_file.name}: {e}")

        print(f"\n总计: {total}/{len(scl_files)} 个文件")
        print(f"输出: {out_dir}")
    else:
        print(f"[ERR] 路径不存在: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
