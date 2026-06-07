# 前言

本指南描述 HiSilicon **BS21 / BS2X** 系列 SoC —— 一颗 BLE 5.4 + SLE/星闪（NearLink）的连接芯片
（**无 Wi-Fi**），用于 `bs2x-pac`、`hisi-riscv-hal`（`chip-bs21` 特性）、`hisi-riscv-qemu`
（`-M bs21` 机器）这套 Rust + QEMU 工具链。

## 真值源

- **`/root/fbb_bs2x`** —— HiSilicon 官方 `fbb_bs2x` C SDK（BS20 / BS21E / BS22 SKU；`bs2x` 为公共驱动层）。
  本指南所有寄存器/地址/中断/启动事实**以该 SDK 为唯一标准**。
- **`bs2x-svd/BS2X.svd`** —— 由上述事实整理的 CMSIS-SVD，经 svd2rust 生成 `bs2x-pac`。

## 与 WS63 的关系

BS21 与 WS63 同属 HiSilicon **「HimiDeer」riscv31 核**：

- **相同(直接复用)**：LOCI 本地中断架构（mie 26-31 + 自定义 LOCI ≥32）、自定义 CSR、
  UART v151 / TIMER v150 / GPIO v150 等版本化 IP 寄存器块、单应用核启动思路。
- **不同(按芯片)**：主频（64 MHz vs 240 MHz）、连接性（BLE/SLE vs Wi-Fi）、内存图、
  外设集（新增 USB/NFC/PDM/QDEC/KEYSCAN/13-bit GADC）、外设基址、IRQ 号。

因此 Rust 栈把「芯片中立」部分统一为 `hisi-riscv-*`（hal/rt/qemu），「按芯片」部分保留
`bs2x-*`（pac/svd/guide）与 `ws63-*`。

## 里程碑

**M1（已达成）**：BS21 的 `blinky` + `uart_hello`（标准 RV32IMFC、`--features chip-bs21`）
在 `qemu-system-riscv32 -M bs21` 上端到端启动。详见[第 5 章](ch5_qemu_m1.md)。
