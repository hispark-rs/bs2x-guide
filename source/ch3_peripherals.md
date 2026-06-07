# 第 3 章 外设与基址

来源：`fbb_bs2x` SDK。BS21 的 UART/TIMER/GPIO/I2C/SPI/PWM/DMA/RTC/TRNG/WDT/TCXO 是与 WS63
**同版本化 IP**（UART v151 / TIMER v150 / GPIO v150），寄存器**逐位相同**，仅基址 + 实例数 + IRQ 不同。
因此 `bs2x-pac` 的寄存器块复用自 `WS63.svd`（见 `bs2x-svd`）。

## 3.1 已建模外设（`bs2x-pac` 实例）

| 外设 | 基址 | 实例 | IRQ |
|---|---|---|---|
| GLB_CTL_M | `0x5700_0000` | 全局控制（时钟/复位） | （汇聚 BT/GADC/NFC/USB 等） |
| GPIO0-4 | `0x5701_0000` / `_4000` / `_8000` / `_C000` / `0x5702_0000` | 5 bank × 32 脚 | GPIO_0=34, GPIO_1=35 |
| ULP_GPIO | `0x5703_0000` | 低功耗 GPIO | ULP_GPIO=33 |
| UART0-2 | `0x5208_1000` / `0x5208_0000` / `0x5208_2000` | UART_L0/H0/L1 | 39 / 41 / 42 |
| TIMER | `0x5200_2000` | TIMER0-3（+0x100/通道） | 53-56 |
| WDT | `0x5200_3000` | 看门狗 | — |
| TCXO | `0x5700_0200` | 自由计数器 | — |
| I2C0-1 | `0x5208_3000` / `0x5208_4000` | 最多 2 | 62 / 63 |
| SPI0-2 | `0x5208_7000` / `_8000` / `_9000` | SPI_M0/MS1/MS2 | 59 / 60 / 61 |
| PWM | `0x5209_0000` | 12 通道 | PWM_0=71, PWM_1=72 |
| DMA / SDMA | `0x5207_0000` / `0x520A_0000` | M_DMA(8ch) / S_DMA(4ch) | SDMA M_SDMA=57 |
| RTC | `0x5702_4000` | 4 个 | RTC_0-3 = 49-52 |
| TRNG/SEC | `0x5200_9000` | 安全/随机数 | SEC=70 |

## 3.2 BS21 专属外设（随连接性补全）

WS63 没有、待补进 `BS2X.svd` 的：**USB 2.0、NFC、PDM、QDEC、KEYSCAN、13-bit GADC**，
以及 GLB_CTL_A/D、PMU1/PMU2_CMU、ULP_AON、FUSE 等电源/时钟控制块。

## 3.3 M1 用到的子集

里程碑 1 的 `blinky` 只用 GPIO0 引脚 0（`0x5701_0000`），`uart_hello` 只用 UART0（`0x5208_1000`）；
两者均不初始化时钟树、不触发中断，故 QEMU `-M bs21` 仅需 GPIO + UART 模型 + 内存 + 吸收器即可跑通。
