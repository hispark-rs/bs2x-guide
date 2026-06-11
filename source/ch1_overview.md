# 第 1 章 芯片概览

## 1.1 身份

- `fbb_bs2x` = 星闪（SparkLink/NearLink）**BS20 / BS21E / BS22** 方案（LiteOS）。`bs2x` 是公共驱动目录，
  `bs20/bs21e/bs22` 是 SKU。本指南的「BS21」≈ **BS21E**。
- 规格：CPU **64 MHz**、FLASH **1 MB**、RAM **128 KB（BS20）/ 160 KB（BS21E·BS22）**、
  SLE 1K/2K/4K、**USB 支持**、**无 Wi-Fi**（仅 BT/BLE 5.4 + SLE/GLE）。
- 主控：HiSilicon RISC-V32 + 硬浮点（编译器 `cc_riscv32_musl_fp`），自定义核 **「linx131」**
  —— WS63 的 `xlinx`/`riscv31` 的同族变体。**单核**——经对照 SDK 核实,BS21 只有应用核：
  `platform_core.h` 的 `slave_cpu_t { SLAVE_CPU_BT, SLAVE_CPU_MAX_NUM }` 是一个**零 `.c` 引用的死枚举**
  （早期曾误读为「BT 从核」,后已纠正）；BLE/SLE 的 **host 与 controller 都作为 LiteOS 任务跑在应用核上**,
  无独立 BT 核、无核间 IPC。运行时出现的 `core:2` 复位是 **APPS_CORE**(应用核)而非 BT 核。Rust 栈目标即此应用核。

## 1.2 ISA 与工具链

BS21 应用核为 **RV32IMFC_Zicsr**（I/M/F/C，ilp32f 硬单浮点，无 A 原子，无 MMU），与 WS63 一致。
故 M1 直接复用 `ws63` Rust 工具链（`riscv32imfc-unknown-none-elf`），无需新建 target。

`linx131` 自定义压缩 ISA（同 WS63 的 xlinx 思路，占用 C 扩展编码空间）只有厂商 C 固件用到；
标准 RV32IMFC 的 Rust 固件**不需要**它，故 M1 的 `-M bs21` QEMU 不含自定义 ISA 解码器。

## 1.3 中断核架构

与 WS63 **完全相同**的 HiSilicon「HimiDeer」LOCI 本地中断（`vectors.h` 核对）：
`RISCV_SYS_VECTOR_CNT=26`、mie 类 6 个（IRQ 26-31）、custom LOCI 类（IRQ≥32，`LOCIEN_IRQ_NUM=32`）、
`LOCIPRI_IRQ_NUM=8`/`LOCIPRI_IRQ_BITS=4`、异常上下文含 `ccause`（0xFC2）。
→ `hisi-riscv-hal` 的 `interrupt` 模块 + QEMU LOCI intc 原样复用。详见[第 4 章](ch4_interrupts.md)。
