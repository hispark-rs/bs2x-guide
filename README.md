# bs2x-guide

HiSilicon **BS21 / BS2X**（BLE 5.4 + SLE/星闪 NearLink，无 Wi-Fi）系列 SoC 的用户指南，
是 `bs2x-pac` / `hisi-riscv-hal`(`chip-bs21`) / `hisi-riscv-qemu`(`-M bs21`) 这套 Rust + QEMU
工具链的配套文档。与 [`ws63-guide`](https://github.com/hispark-rs/ws63-guide) 对等。

真值源：HiSilicon `fbb_bs2x` C SDK（以 csdk 为唯一标准）。

## 构建（Sphinx + MyST）

```bash
uv sync
uv run sphinx-build -b html . _build/html
```

## 内容

- `index.rst` — Sphinx 根 + 目录树。
- `source/preface.md` — 前言 / 真值源 / 与 WS63 的关系。
- `source/ch1_overview.md` — 芯片身份、ISA、中断核。
- `source/ch2_memory_map.md` — 内存图 + M1 链接布局。
- `source/ch3_peripherals.md` — 外设与基址（已建模 + 专属）。
- `source/ch4_interrupts.md` — LOCI 本地中断 + BS21 IRQ 映射。
- `source/ch5_qemu_m1.md` — `-M bs21` 机器 + 里程碑 1 复现。

> 版本 00，随连接性逐步补全。
