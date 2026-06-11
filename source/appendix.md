(appendix)=

# 缩略语

```{glossary}
ADC
  Analog to Digital Converter，模数转换器（BS2X 的 GADC 为 13-bit）

APB
  Advanced Peripheral Bus，高级外设总线

BLE
  Bluetooth Low Energy，低功耗蓝牙（BS2X 为 BLE 5.4）

BQB
  Bluetooth Qualification Body，蓝牙资格认证（其测试常用 DTM/HCI-UART 固件）

CIC
  Cascaded Integrator-Comb，级联积分梳状滤波器（PDM 抽取链的第一级）

CSR
  Control and Status Register，控制状态寄存器（RISC-V 特权/自定义寄存器）

DMA
  Direct Memory Access，直接存储器访问

DTCM
  Data Tightly-Coupled Memory，数据紧耦合存储器（BS21 `0x2000_0000`）

DTM
  Direct Test Mode，直接测试模式（蓝牙控制器的射频测试模式）

DWC OTG
  DesignWare Cores USB On-The-Go，Synopsys 的 USB 2.0 OTG 控制器 IP（BS2X USB）

eFUSE
  electronic Fuse，电子熔丝（一次性可编程，存校准/配置；BS2X 为 v151）

GADC
  General-purpose ADC，通用模数转换器（BS2X 13-bit，IP v153）

GLE
  Generic Link Engine，海思统一的 BLE + SLE 主机协议栈（host 侧 blob）

GPIO
  General-Purpose Input/Output，通用输入输出（BS2X GPIO IP v150）

HAL
  Hardware Abstraction Layer，硬件抽象层（本项目的 `hisi-riscv-hal`）

HCI
  Host Controller Interface，主机控制器接口（蓝牙 host↔controller 边界；BS2X 为进程内消息 ABI，非 H4-UART）

IP
  Intellectual Property (core)，知识产权核（此处指外设控制器的版本化硬件模块，如 UART v151）

IRQ
  Interrupt Request，中断请求

ITCM
  Instruction Tightly-Coupled Memory，指令紧耦合存储器

KEYSCAN
  Key-matrix Scanner，键盘矩阵扫描器（BS2X IP v150）

L2RAM
  Level-2 RAM，二级片上 RAM（BS20 128K / BS21E·BS22 160K，数据/栈所在）

LiteOS
  Huawei LiteOS，华为轻量级实时操作系统（fbb_bs2x 厂商固件的内核）

linx131
  BS2X 应用核的海思自定义压缩 ISA（WS63 `xlinx` 的同族变体，占用 C 扩展编码空间）

LOCI
  Local Interrupt，海思「HimiDeer」核的本地中断架构（mie 26-31 + 自定义 LOCI ≥32）

MMIO
  Memory-Mapped I/O，内存映射输入输出

NearLink
  星闪，即 SLE/SparkLink，海思自有的近距离无线连接（非蓝牙 SIG 标准）

OTP
  One-Time Programmable (memory)，一次性可编程存储器

PAC
  Peripheral Access Crate，外设访问 crate（svd2rust 生成的 `bs2x-pac`/`ws63-pac`）

PDM
  Pulse-Density Modulation，脉冲密度调制（数字麦克风音频前端；BS2X IP v150）

PMU
  Power Management Unit，电源管理单元

QDEC
  Quadrature Decoder，正交编码器解码（BS2X IP v150）

riscv31
  海思「HimiDeer」RISC-V 核家族（WS63/BS2X 共用，RV32IMFC_Zicsr + 自定义 ISA + LOCI）

RT
  Runtime，运行时（本项目的 `hisi-riscv-rt`：启动汇编 + 链接脚本 + 中断向量）

SFC
  Serial Flash Controller，串行 Flash 控制器（XIP QSPI；BS2X IP v150）

SKU
  Stock Keeping Unit，产品型号（BS20 / BS21E / BS22）

SLE
  SparkLink Low Energy，星闪低功耗（NearLink 的低功耗子集）

SRC
  Sample-Rate Conversion，采样率转换（PDM 链中的下采样级）

SVD
  System View Description，CMSIS 寄存器描述 XML（`BS2X.svd`，svd2rust 输入）

TCXO
  Temperature-Compensated Crystal Oscillator，温补晶振（BS2X 提供自由计数器；v150 为 16-bit 分块计数）

TRNG
  True Random Number Generator，真随机数发生器（BS2X 为 v1）

UART
  Universal Asynchronous Receiver/Transmitter，通用异步收发器（BS2X IP v151，3 实例）

USB
  Universal Serial Bus，通用串行总线（BS2X 为 USB 2.0 OTG / DWC OTG）

WDT
  Watchdog Timer，看门狗定时器（BS2X IP v151）

XIP
  eXecute In Place，就地执行（代码直接从 NOR Flash 运行，`0x1000_0000`）

xlinx
  WS63 应用核的海思自定义压缩 ISA（BS2X `linx131` 的同族）
```
