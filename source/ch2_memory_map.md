# 第 2 章 内存图

来源：`fbb_bs2x` SDK `platform_core.h`，与 `bs21-examples` 的 `memory.x`、`hisi-riscv-qemu` 的 `bs21.c` 一致。

## 2.1 主内存区

| 区域 | 基址 | 大小 | 说明 |
|---|---|---|---|
| BOOTROM | `0x0000_0000` | 32 KB | 掩膜 ROM 窗（secure-libc/printf/timing/watchdog 驻留） |
| ROM | `0x0000_8000` | ~480 KB | ROM 符号延伸到 ~`0x4_0000` |
| ITCM | `0x0008_0000` | 512 KB | 指令 TCM（顶部切出 DTCM） |
| DTCM | `0x000F_0000` | 64 KB | 数据 TCM |
| **L2RAM** | `0x0010_0000` | **160 KB** | 主系统 RAM（BS21E/BS22；BS20 为 128 KB） |
| **FLASH（XIP）** | `0x1000_0000` | **1 MB** | QSPI NOR 闪存，代码 XIP 入口 |

对比 WS63：外设空间在 `0x4400_0000`；BS21 在 **`0x5200_0000`（M_CTL）+ `0x5700_0000`（GLB/PMU/GPIO/RTC）**。

## 2.2 M1 链接布局

`-kernel` 直载：代码（`.text`/`.rodata`）在 FLASH（`0x1000_0000` XIP），数据/BSS/栈在 L2RAM（`0x0010_0000`）。
复位 PC = `0x1000_0000`。栈顶 = L2RAM 顶（`0x0012_8000`）。

```
PROGRAM (rx) : ORIGIN = 0x10000000, LENGTH = 1M     # .text/.rodata XIP
SRAM    (rwx): ORIGIN = 0x00100000, LENGTH = 0x28000 # .data/.bss/stack/heap
```

启动握手（同 WS63）：`hisi-riscv-rt` 启动代码在设置 `mtvec` 前会解引用 `a0`（上一启动级传入的启动参数块指针）。
`-kernel` 直载无上一级，故 QEMU `bs21.c` 在复位时把 `a0` 指向清零的 L2RAM，使「启动原因」读为 0（正常启动）。

## 2.3 其它窗口（QEMU 吸收）

- M_CTL 外设：`0x5200_0000`/16 MB
- GLB/PMU/GPIO/RTC：`0x5700_0000`/16 MB
- riscv31 核私有外设总线（FlashPatch + SCS）：`0xE000_0000`（同 WS63）
