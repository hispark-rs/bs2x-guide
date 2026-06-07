# 第 4 章 中断

来源：`fbb_bs2x` SDK `chip_core_irq.h` / `vectors.h`。BS21 的本地中断核架构与 WS63 **完全相同**。

## 4.1 LOCI 本地中断架构

HiSilicon「HimiDeer」核：

- `LOCAL_INTERRUPT0 = 26`（`BCPU_INT0_ID = 26`）。
- **mie 类**：IRQ **26-31**（6 个），由标准 RISC-V `mie` 位使能 + 向量化 `mtvec` 投递。
- **custom LOCI 类**：IRQ **≥32**，由自定义 CSR `locie0~2` 使能（`LOCIEN_IRQ_NUM=32`），
  自定义 CSR 投递（mcause 可超 31）。
- 优先级：`LOCIPRI_IRQ_NUM=8`、`LOCIPRI_IRQ_BITS=4`、`LOCIPRI_DEFAULT_VAL=0x11111111`、`PRITHD`。
- 异常上下文含 `ccause`（WS63 的 `0xFC2` 自定义 CSR）。

CSR 原始地址（`LOCIEN 0xBE0-2` / `LOCIPD 0xBE8-A` / `LOCIPCLR 0xBF0` / `LOCIPRI 0xBC0-CF` / `PRITHD 0xBFE`）
与 WS63 极高概率相同 → `hisi-riscv-hal` 的 `interrupt.rs` + QEMU LOCI intc + target/riscv LOCI 投递补丁原样复用。

> 注意：BS21 的 26-31 是 **BT/ADC**（`BT_INT0/1`、`GADC_DONE/ALARM`），不像 WS63 那里是 TIMER；
> BS21 的 TIMER 落在 LOCI 区（53-56）。

## 4.2 BS21 IRQ 映射（节选，完整见 `bs2x-pac` 的 `ExternalInterrupt`）

| IRQ | 名称 | | IRQ | 名称 |
|---|---|---|---|---|
| 26-27 | BT_INT0/1 | | 53-56 | TIMER_0-3 |
| 28-29 | GADC_DONE/ALARM | | 57 | M_SDMA |
| 33 | ULP_GPIO | | 59-61 | SPI_M_S_0 / _1 / SPI_M |
| 34-35 | GPIO_0/1 | | 62-63 | I2C_0/1 |
| 39/41/42 | UART_0/1/2 | | 70 | SEC |
| 49-52 | RTC_0-3 | | 71-72 | PWM_0/1 |
| 44/46 | PDM / KEY_SCAN | | 87-89 | TSENSOR / QDEC / USB |

完整映射（含 BT_BB、NFC、PMU、ULP 唤醒等，到 `BUTT_IRQN`≈89）由 `bs2x-pac::interrupt::ExternalInterrupt`
枚举给出，并经 `rt` 特性生成 `device.x` 中断向量表。
