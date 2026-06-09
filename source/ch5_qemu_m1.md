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

## 5.4 原厂固件在 QEMU 上（loaderboot 已跑起来）

目标:像 WS63 那样在 `-M ws63` 跑厂商 C SDK 固件,在 `-M bs21` 上跑 **BS2X 原厂固件**。

> **进展(已达成)**:fbb_bs2x 预编译 **loaderboot 在 `-M bs21` 上已执行** ——
> `hisi-riscv-qemu/scripts/bs21-vendor-boot.sh` 解开签名镜像、把代码装到 `0x40000` 运行,
> 跑完约 **480 条**真实厂商代码(把启动参数块搬到 DTCM、拉起 PMU `0x57004600`),进入其
> 下载模式空转(`j .` @0x4298e),**0 条非法指令**——xlinx 解码器(经 ws63 CPU 型号对 `-M bs21` 生效)透明处理。
> 详见 `hisi-riscv-qemu/docs/bs21-vendor-firmware.md`。
>
> **跑通过程中修了一个真 bug**:loaderboot 把启动参数搬到 `0x20000000`(真实 BS21 DTCM,`APP_DTCM_ORIGIN`),
> 而 `bs21.c` 原先把 DTCM 错放在 `0xF0000` → 写 `0x20002d50` 时 fault。已修正(DTCM→`0x20000000`;M1 + 5/5 WS63 qtest 不回归)。

### 签名镜像格式(已破解 loaderboot)

多段式:`0x000` 镜像头(魔数 `0x4bd2f01e`,头长 `0x40`)+ pad;`0x100` code-info 头(魔数 `0x4bd2f02d`,
代码大小 = code-info+`0x24` 处的 u32);尾部是代码(`code_size` 字节,到 EOF)。loaderboot:`0x5c20` 字节 @ 文件 `0x300`。
flashboot 用**另一种**格式(魔数=ImageId `0x4b1e3c1e`、code-info 作尾部 trailer `0x4b1e3c2d`),尚未破解。

### 已核实的事实与剩余边界:

**已就位的地基**
- **xlinx 解码器对 `-M bs21` 已生效**:解码 hook 在 `target/riscv`(0001 patch),按 `ws63` CPU 型号触发;`bs21.c` 用的就是 `ws63` CPU,故无需额外改动即可解码 xlinx。
- **BS2X 固件确实用 linx131 = xlinx**(同一套自定义 ISA):SDK 有 `arch/riscv/src/linx131/custom.cmake`,用厂商 gcc(`cc_riscv32_musl_fp`)+ `-Wa,-mcjal-expand`,与 WS63 同源。
- **预编译固件已取**:`src/interim_binary/bs21e/bin/boot_bin/{loaderboot,flashboot}_sign*.bin`(签名镜像)。
- **ROM 表可得**:`src/drivers/chips/bs2x/rom/rom_info/.../librom_callback.a` + 符号(如 `memset_s=0x3d80c`,落在 ROM 区 `0x0–0x80000`),对应 WS63 的 `acore.sym`。
- 启动握手(a0=启动参数指针)与 WS63 一致,`bs21.c` 已就位。

**剩余边界(= 推后的连接性工作,多日量级)**
- **签名镜像解包**:`*_sign.bin` 有嵌套头(外层魔数 `0x4bd2f01e`,内层还有一层),真实代码偏移/装载地址需按 sign-tool 规格解析。直接把 `+0x40` 之后的内容裸装到 `0x10000000` 运行 → 立即落到 `0000`(illegal)死循环,印证缺装载语义。
- **掩膜 ROM**:正常由 mask ROM 校验+装载镜像并提供 ROM 函数;`-M bs21` 的 `0x0–0x80000` 是清零 RAM,flashboot 一旦 call ROM 函数(`memset_s@0x3d80c`…)就会执行到零 → fault。需 **BS21 ROM 调用表**(类似 WS63 的 `ws63_rom_call`,但地址/函数是 BS21 的)。
- **SFC/flash** 未建模。

**路线(镜像 WS63 的 csdk-on-qemu 之旅)**:① 从 `librom_callback.a`/符号表提取 BS21 ROM 表 → 在 `bs21.c` 注册 ROM-ABI 回调(机器侧,复用 0001 重构的框架);② 解析签名镜像头得到装载地址、或从 SDK 源构建出 ELF fixture;③ 补 SFC + mask-ROM 桩。M1 已证明 CPU+内存+UART+GPIO+xlinx 这条链是通的;原厂固件差的就是 ROM 表 + 镜像装载。

## 5.5 其它后续（随连接性）

全外设 64 MHz 时钟树对齐、BLE/SLE 厂商 blob、`BS2X.svd` 余下外设(NFC、GADC 的 AFE/PMU/DIAG 子块、电源/时钟控制块)补全。
