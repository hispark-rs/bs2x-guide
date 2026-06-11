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

## 3.2 BS21 专属外设（已建模）

WS63 没有、由 `fbb_bs2x` SDK 的 HAL 寄存器头文件派生进 `BS2X.svd` 的：

| 外设 | 基址 | IP | IRQ |
|---|---|---|---|
| GADC（13-bit ADC） | `0x5703_6000` | v153 | GADC_DONE=28, GADC_ALARM=29 |
| KEYSCAN | `0x5208_D000` | v150 | KEY_SCAN_LOW_POWER=38, KEY_SCAN=46 |
| PDM | `0x5208_E000` | v150 | PDM=44 |
| QDEC | `0x5200_0200` | v150 | QDEC=88 |
| **USB**（USB 2.0 OTG，DWC OTG） | `0x5800_0000` | Synopsys DWC | USB=89 |

GADC/KEYSCAN/PDM/QDEC 由 `bs2x-svd/tools/derive_bs2x_specific.py` 解析 `hal_<p>_v<NN>_regs_def.h`
的寄存器块 + 位域生成。**USB** 解析 `dwc_otgreg.h` 的 `#define DOTG_<REG>` 偏移定义,生成 49 个寄存器
（寄存器级,该头无位域分解）。`bs2x-pac` 含 `Gadc`/`Keyscan`/`Pdm`/`Qdec`/`Usb` 类型。
`hisi-riscv-qemu` 的 `-M bs21` 为 USB 窗(`0x5800_0000`)加了吸收器。

## 3.3 仍推后

**NFC**（IRQ 69）在 SDK 的 HAL 树里没有简单寄存器块头（复杂子系统）,暂作 GLB_CTL_M 上的中断保留;
GLB_CTL_A/D、PMU1/PMU2_CMU、ULP_AON、FUSE 等电源/时钟控制块同理逐步补全。

## 3.4 M1 用到的子集

里程碑 1 的 `blinky` 只用 GPIO0 引脚 0（`0x5701_0000`），`uart_hello` 只用 UART0（`0x5208_1000`）；
两者均不初始化时钟树、不触发中断，故 QEMU `-M bs21` 仅需 GPIO + UART 模型 + 内存 + 吸收器即可跑通。

## 3.5 HAL 驱动覆盖与 QEMU 功能验证（全外设已通）

`hisi-riscv-hal`（`chip-bs21`）现在覆盖 **BS2X 全部功能外设**，每个都在 `hisi-riscv-qemu`
的 `-M bs21/bs22/bs20` 上**功能验证**（不仅是寄存器可访问，而是驱动真跑通、读回已知值）。

| 外设 | IP | HAL 模块 | bs2x-pac 是否需改 | QEMU 验证（示例） |
|---|---|---|---|---|
| GPIO | v150 | `gpio` | 否 | blinky:GPIO0 翻转、0 非法指令 |
| UART | v151 | `uart` | 否 | uart_hello 横幅 |
| TIMER / TCXO | v150 | `timer` / `tcxo` | 否 | uart_hello tick 计数 |
| ULP_GPIO | v150 | `ulp_gpio` | 否 | 复用 gpio 块（同 v150） |
| SPI | v151 | `spi` | 否（同 ws63 v151） | spi_loopback:`[0xA5,0x3C,0xFF,0x01]` 环回 |
| PWM | v151 | `pwm` | 否 | pwm_wdt:配置+启动 |
| WDT | v151 | `wdt` | 否 | pwm_wdt:`counter_value()` 回读 timeout |
| GADC（13-bit ADC） | v153 | `gadc` | 否（PAC 已对） | gadc_read:转换读 `0x12345`（18 位符号扩展） |
| KEYSCAN | v150 | `keyscan` | 否 | hid_demo:解码 row2/col1/pressed |
| QDEC | v150 | `qdec` | 否 | hid_demo:有符号 `-5` |
| **I2C** | **v151 DesignWare** | `i2c`（=`i2c_v151.rs`） | **是：SVD 重写**（原是 ws63 v150） | i2c_scan:扫到从机 `0x50`（tx_abrt/addr_7b_noack） |
| **RTC** | **v150** | `rtc`（=`rtc_v150.rs`） | **是：SVD 重写**（原是 ws63 v100） | clock_rng:64 位计数器递增 + cnt_lock 握手 |
| **TRNG** | **v1** | `trng`（=`trng_v1.rs`） | **是：SVD 补控制寄存器**（缺 `trng_ring_en`） | clock_rng:随机数变化 |
| DMA | v151 | `dma`（mem-to-mem） | 否（`Dma0` 走 PAC 基址） | dma_mem:`src→dst` 真拷贝 `dst==src` |
| **PDM**（音频麦克风） | v150 | `pdm` | 否（FIFO 窗 `0x5208_E080` 走裸地址） | hid_demo:从 UP-FIFO 采到 4 个单调 PCM 样本 |
| **USB**（DWC2 OTG） | Synopsys DWC | `usb` | 否（PAC 已含全寄存器） | dma_mem:**设备枚举**→「enumerated at high speed」 |

**两个里程碑级实现:**
- **PDM 全音频采集**:配 CIC/SRC/UP-FIFO + 释放 datapath reset,然后 CPU 轮询 UP-FIFO 数据窗
  (`0x5208_E080`,查 `up_fifo_st@0x30` bit2);状态/数据窗不在 bs2x-pac(只含配置寄存器),故走 BS2X 裸地址。
- **USB 全设备 bring-up**:DWC2 OTG 设备态完整序列——核软复位(GRSTCTL)→强制设备模式(GUSBCFG)→
  GAHBCFG/GINTMSK→DCFG→软连接(清 `DCTL.SFTDISCON`)→等 `GINTSTS.USBRST`+`ENUMDONE`→读 `DSTS.ENUMSPD`。
  描述符/端点传输 + USB 类协议栈在其之上,仍推后(控制器已到枚举态)。

### 关键经验:bs2x-pac 对「异版本 IP」是错的

`BS2X.svd` 当初是从 `WS63.svd` **复制**来的。对**同 IP 版本**的外设(uart/gpio/timer/spi/pwm/wdt/gadc…)
正确;但对 **bs2x 用了不同 IP 版本**的外设是**错的**——它把 ws63 的 IP 描述在了 bs2x 的地址上:
- i2c:bs2x v151(DesignWare `ic_*`)vs ws63 v150(自研 `i2c_*`)——完全两个控制器;
- rtc:bs2x v150(64 位计数器 + `cnt_lock`)vs ws63 v100(32 位);
- trng:缺控制寄存器(`trng_ring_en`)。

这些必须**先重写 `BS2X.svd` 里那个外设块 → `bs2x-svd/regen.sh` 重生成 `bs2x-pac` → 再写驱动**。
「能编译过 `chip-bs21`」是必要不充分:驱动还可能含 ws63 硬编码的 MMIO 地址(如 SPI 的 CLDO_CRG 时钟初始化
`0x4400_11xx`,编译器看不出来)——故每个新使能的驱动都要 (1) grep `0x44xx`/`0x57xx` 字面量、(2) 在 QEMU 上真跑。

### 逐外设移植配方（可复用模板）

1. 用 agent 从 `fbb_bs2x` SDK 抽寄存器图 + 最小时序;
2. 若 bs2x-pac 错（异版本 IP）→ 重写 `BS2X.svd` 里该外设块 + `bs2x-svd/regen.sh`;
3. 写驱动（IP 不同就独立模块,lib.rs `#[path]` 按芯片选,都暴露成同一 `hal::<p>`);
4. QEMU 模型写进 `ws63.c` + `ws63_create_<p>()`(声明在 `hisi_riscv31.h`),在三台 bs2x 机器映射;
5. 写 `examples/bs21`+`bs20` 示例 + 冒烟断言。

提交链自底向上:`bs2x-svd → bs2x-pac → hisi-riscv-hal → hisi-riscv-qemu → ws63-rs`，每步保证 WS63 零回归(5/5 qtest)。
