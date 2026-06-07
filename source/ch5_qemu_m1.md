# 第 5 章 QEMU `-M bs21` 与里程碑 1

## 5.1 里程碑 1（已达成）

**M1 = BS21 的 `blinky` + `uart_hello` 在 `qemu-system-riscv32 -M bs21` 上端到端启动。**

- `bs21_uart_hello`：在 UART0（`0x5208_1000`）打印横幅 + tick 计数。
- `bs21_blinky`：翻转 GPIO0（`0x5701_0000`）引脚 0，0 条非法指令陷阱。

关键洞察：BS21 的 Rust 固件只用标准 RV32IMFC、不调掩膜 ROM，故 `-M bs21` **不需要** linx131 自定义 ISA 解码器，
**也不需要** ROM 拦截（那些随连接性推后）。

## 5.2 `-M bs21` 机器（`hisi-riscv-qemu`）

`bs21.c` 复用 `ws63.c` 的设备模型（同版本 IP，经 `hisi_riscv31.h` 暴露）：CPU（RV32IMFC）、BS21 内存图、
自定义 UART×3、一个 GPIO bank、TIMER、TCXO、LOCI 中断控制器 + 自定义 CSR、两个 MMIO 窗吸收器。
`-M ws63` / `-cpu ws63` 的机器/设备符号保持不变（WS63 自己的芯片）。

## 5.3 复现

```bash
# 1) 构建 BS21 固件（独立 workspace，chip-bs21 HAL + bs2x-pac + BS21 memory.x）
cargo build --manifest-path bs21-examples/Cargo.toml

# 2) 构建带 -M bs21 的 QEMU
cd hisi-riscv-qemu && ./scripts/build.sh

# 3) M1 验收
WS63_RS=/path/to/hisi-riscv-rs ./scripts/bs21-smoke-test.sh
# => BS21 SMOKE TEST: PASS
```

## 5.4 后续（随连接性）

linx131 自定义 ISA 解码、ROM 拦截、全外设对齐（USB/NFC/PDM/QDEC/KEYSCAN/13-bit GADC、64 MHz 时钟树）、
BLE/SLE 厂商 blob、`BS2X.svd` 外设补全。
