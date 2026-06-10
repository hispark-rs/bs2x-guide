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

多段式:`0x000` 镜像头(头长 `0x40`)+ pad;`0x100` code-info 头(代码大小 = code-info+`0x24` 的 u32);尾部是代码。
**loaderboot** 与 **flashboot 结构相同**,只是魔数不同:loaderboot 镜像头 `0x4bd2f01e` / code-info `0x4bd2f02d`(代码 `0x5c20` @ `0x300`);
flashboot 镜像头 `0x4b1e3c1e`(=ImageId)/ code-info `0x4b1e3c2d`(代码 `0x8ab0` @ `0x300`)。`bs21-vendor-boot.sh` 两种都认。

**flashboot 也跑起来了**:同样链接到 `0x40000`,跑 ~206 条(复位 → ULP_AON 时钟配置 `0x5702c***` → 清零/重定位循环 → 主代码 `0x40552`),
随后在碰 **SFC(串行 Flash 控制器 @`0x90000000`)** 时早停——它要先认 flash。**已建模**:把 WS63 的 `ws63-sfc`(v150,RDID→JEDEC ID)映射到 `0x90000000`。
然后 flashboot 经 **XIP @`0x90100000`** 读分区表,校验首字魔数 `0x4b87a52d`。**已建模**:`bs21.c` 加 `flash1` RAM 窗 @`0x90100000`,
载入预编译 `partition.bin`(魔数在偏移 0)后,flashboot **跨过魔数、跑进主逻辑 ~940 条(4×)**——解析分区表、跑主流程,再停在新的空转点 `0x4293a`。
复现:`bs21-vendor-boot.sh flashboot_sign_a.bin 5 0x40000 partition.bin`。
**全固件镜像已就位**:`bs21-build-flash.sh` 解包 `bs21e_all.fwpkg`(loaderboot/partition/flashboot_a+b/**application**/nv),
按分区表偏移摆放(app @0x15000 → XIP 0x90115000),boot 脚本分块装到 0x90100000(generic loader 单次裸装上限 ~0x10000)。
flashboot 在全固件下仍跑那 940 条。

**`0x4293a` 已破解(2026-06-09):它不是 boot-mode 判定,而是缺失 BS21 掩膜 ROM 导致的崩溃。**
此前"解析后 boot-mode 判定"的猜测是**错的**——根因是 objdump 误解码 xlinx。用**厂商 xlinx 感知的 objdump**
(`fbb_ws63/.../cc_riscv32_musl_fp/bin/riscv32-linux-musl-objdump -b binary -m riscv:rv32 -D --adjust-vma=0x40000`;
BS2X 的 linx131 == WS63 xlinx,同一套 ISA)重新反汇编看清:
- `0x4293a` 是 flashboot 的 **panic 尾**:`irq_lock()` → 把原因 `0xdeadbeaf` 记到 DTCM `0x2000ffe8` → 清 `BOOT_PORTING_RESET_REG`(0x57004600)bit0 → `j .`;
  由 flashboot 的**异常处理程序**(`mtvec=0x47bbc`,printf 打 `exception:/mepc=/mcause=/mtval=/...`)进入。即 flashboot **先 trap、再 panic**。
- **第一次 trap:`mcause=0x2`(非法指令)、`mepc=0`。** flashboot 校验掩膜 ROM 签名:`0x43c8a` 读 `*(0x10020)`,`bne a4, 0xd4818193, 0x4403a`。
  `-M bs21` 的 ROM 区(0x10000–0x40000)是**清零 RAM**(无 ROM dump),`*(0x10020)=0 ≠ 0xd4818193` → 在 `0x4403a` 以 **ra=0** 做 `ret` → 跳到 PC 0 → 非法指令陷阱。
- **验证**:注入魔数 `-device loader,addr=0x10020`(值 0xd4818193)后,flashboot **不再跳崩溃路径**、走通 magic-OK 分支(0x43c98)、多跑到 1260 条,
  再在更深处崩溃(`mcause=0x5` 取数访问异常 @`0x570004a0`)——说明 flashboot 有**多处**掩膜 ROM/外设依赖,魔数只是第一道。
- **结论**:与 WS63 同理,flashboot 与硅上掩膜 ROM 紧耦合(签名 + ROM 数据表 + 它 tail-call 并回注回调的 ROM 函数,如 ROM 地址 0x1c200)。
  SDK 只给 `librom_callback.a`+`.sym`(无 ROM 镜像),故后续路 = **模拟 BS21 掩膜 ROM**(造签名/表 + 扩 `bs21_rom_call`),与 WS63 ROM-on-QEMU 同量级,属推后的连接性工程。
  **不是**单个寄存器能搞定的 boot-mode 标志。M1 + 5/5 WS63 qtest 全程不回归(本轮纯调查,未改 QEMU 源码)。

### flashboot 跑过签名校验、打印 banner(2026-06-09)

两处 `bs21.c` 本地改动把 flashboot 从 `0x4293a` 崩溃推到**完整跑完 init、串口打印 banner**(2953 条,原 723):
- **掩膜 ROM 签名建模**:`bs21.c` 在机器初始化时把 `*(0x10020)=0xd4818193` 写进 RAM 化的 ROM 区(可扩展的 `rom_data[]` 表),签名校验原生通过(不再需要 `-device loader` 注入)。
- **TCXO 碰撞修复**:共享 `ws63-tcxo` 映在 `0x57000200`、区域 0x1000(WS63 布局,那里 TCXO 独占 0x44000000),在 BS21 上吞掉了整个 GLB_CTL_A/D,且对 flashboot 读 `0x570004a0` 的 2 字节访问**触发取数异常**(TCXO ops 要求 4 字节)。按 SDK(`TCXO_COUNT_BASE_ADDR 0x57000200`、`GLB_CTL_A 0x57000400`)计数块只有 0x200,故 `bs21.c` 只 alias `BS21_TCXO_SIZE`(0x200),GLB_CTL_A/D 落回吸收器;BS21 的 TCXO_COUNT 在区域**基址**(偏移 0)而非 WS63 的 +0x4C0,新加 `ws63_tcxo_set_count_off(tcxo,0)`(`hisi_riscv31.h`)把状态/lo/hi 指过去——count-valid 轮询通过(BS21 `uart_hello` 的 tick 计数也随之读对)。WS63 仍默认 0x4C0,5/5 qtest 不回归。

flashboot 现打印:

```
Flashboot Init! id = 0x0 / Power On / Reboot cause:0xF0F0 / Reboot count:0x0
Flash Init ret = 0x80001341 / Load App Failed!
```

### flashboot 检测 flash、载入并跳转 app(2026-06-09)

`Flash Init ret=0x80001341` 是 **flash ID 不匹配**:BS21 flashboot 的 flash 表是 **GigaDevice**(`sfc_config_info_porting.c`:GD25LE80),检测例程在 `0x42122` 把读到的 JEDEC ID 与 **`0x1460C8`**(mfr 0xC8 / type 0x60 / cap 0x14)比较;而共享 `ws63-sfc` 对 RDID 回的是 WS63 的 Winbond W25Q16(0x1560EF),故检测失败 → 置错误标志 → `0x80001341`。把 SFC 的 RDID JEDEC ID 做成**按机器可配**(新 `ws63_sfc_set_flash_id()`,WS63 默认 W25Q16;bs21.c 设 `0x1460C8`)。配合**完整 flash 镜像**(`bs21-build-flash.sh`,app @ XIP `0x90115000`):

```
Flashboot Init! / Power On / Reboot cause:0xF0F0 / Reboot count:0x0
Flash Init ret = 0x0 / No need to upgrade / Jump to addr = 0x90115300
```

flashboot 的 **flash 检测 ✓、升级版本校验 ✓、载入并跳转 app @0x90115300 ✓**;app 的 RTOS 启动随即从 XIP 执行(设 `mtvec`、清 `mstatus`/`mie`、配 LOCI 自定义 CSR `0x7c2`/`0x7c3`、`gp` 指到 DTCM `0x2000369c`)。**flashboot 的任务已完成**。复现:`bs21-vendor-boot.sh flashboot_sign_a.bin 8 0x40000 <full-flash.bin>`(第 4 参数 = `bs21-build-flash.sh` 出的镜像)。BS2X 原厂启动链(loaderboot → flashboot → app)在 `-M bs21` 上已**端到端打通到 app 交接**;再往后跑完整 LiteOS BLE/SLE app 是更大的连接性工程(全内存图 / RAM 初始化 / 全外设)。WS63 5/5 + BS21 M1 不回归。

### app(LiteOS)启动:xlinx prefd 解码,跑进 init-call 表(2026-06-09)

flashboot 跳到 app 后,LiteOS 启动只跑 21 条就 trap(mcause=2)在 `.data` 拷贝循环的 `prefd`(`0x0003300b`)上——xlinx opcode 0x0b funct3=3,一条缓存预取提示,解码器原把全部 0x0b 当 ldmia/stmia(funct3 0/1),prefd 匹配不到寄存器位 → illegal → 跳到 app 的 `mtvec`(0x44330,ITCM)跑到 flashboot 残留 → 空转。给 opcode 0x0b 加 funct3 分派:**f3 2/3 = pref/prefd → NOP**(预取无体系结构副作用),f3 0/1 仍是 ldmia/stmia。这样 app 的 `ldmia`/`stmia` 块拷贝跑通,app 执行 **934 条**真实 LiteOS 启动(拷 `.data` flash→DTCM、设 gp/sp、早期 init),跑进它的 **init-call 表**(11 个函数指针 @0x90115a10..0x90115a3c)。**下一关**:init `table[9]`(0x90118a3a,一个 LiteOS 任务/线程注册——入口 0x90118cfe、栈 1536、优先级 31,经创建器 0x90118a2a)返回错误 **0x2000209** → app 打日志后停在 `0x90128c62 (j .)`。这已是 LiteOS 内核 bring-up(任务创建/调度器/内存池,再到 BLE/SLE 栈)——属更大的连接性工程,每个 init level 都要喂饱其子系统。WS63 5/5 + BS21 M1 不回归。

### xlinx muliadd 立即数修复 → app 跑过 LiteOS 任务创建,跑完内核 init(2026-06-09)

init-call `table[9]` 卡死(`LOS_TaskResume` 返回任务 errno `0x2000209`)的根因是**解码器 bug**,不是缺子系统:`LOS_TaskResume` 用 xlinx `muliadd s0,s0,a0,92` 把 TCB 数组按 `base + id*92` 索引,但解码器把立即数的 funct7 字段掩成 5 位(`& 0x1f`)而非完整 7 位(`& 0x7f`)——立即数 = `(funct7<<1) | bit14`(最高 8 位),故 >63 的值被截断(92→28)。`TCB[1]` 算成 `base+28` 而非 `base+92` → resume 读错 TCB(status=0 非 SUSPENDED)→ `0x2000209`。用 app 里 82 条立即数 64..192 的 `muliadd` 验证:旧 5 位掩码 82 条全错,7 位掩码 82 条全对。

修好后 app **跑过任务创建、跑完整个 LiteOS 内核 init**(1663 条 app 指令,原 934),到达 app 自己的 reboot/idle 路径(`APP|Reboot core:%d cause 0x%x`,停在 0x90126206)。**下一边界**:该路径读 ULP_AON 寄存器(`*0x5702c0f0` vs 0x10000,吸收器回 0),且看着是 app/多核相关(`core:2` ≈ BT 从核)——更深的 app/连接性层。WS63 5/5 + BS21 M1 不回归。

### xlinx ldmia/stmia bank 选择位修复 → `core:2`「多核」停机其实是 app 崩溃,已消除(2026-06-10)

先核实多核是否真实:BT 从核**确实存在**(`slave_cpu_t{SLAVE_CPU_BT, SLAVE_CPU_MAX_NUM}`),但 0x90126206 的 `APP|Reboot core:2` 停机**并非多核边界**——`core:2` 是硬编码的 reboot 来源码,且该路径是经一次**空指针 `memcpy`**(源指针被踩)走到的。根因是**第三个 xlinx 解码器 bug**:`ldmia/stmia`(opcode 0x0b)带一个 16 槽寄存器存在位图,**bit31 选两组寄存器 bank** 中的哪一组映射各槽;旧解码器只认 **bank 0**(`{ra,sp,s0,s1,a0,a1,s2..s11}`)。LiteOS 的 8 字 `memcpy` 块拷贝用的是 **bank 1** 列表(`{ra,t0..t2,a0..a7,t3..t6}`),于是被当成 bank-0 的 s 寄存器译码,**踩掉调用者的 `s0..s11`** → 后续 `memcpy(dst, s0=NULL, n)` → 崩溃 → 走到 app 的 reboot 路径。补上 bit31 bank 选择位 + 一张 `[2][16]` 槽→GPR 表(槽位 `7,8,9,10,11,20..30`),并用固件里 **164 条真实 `ldmia`/`stmia` 100% 验证**(96 条 bank-0 + 68 条 bank-1)。修好后崩溃消失(0 trap,mcause=0),app 跨过 reboot 路径继续 init。**下一关**:app 现在卡在 **32K 时钟校准轮询** @0x901286b2——`while (!(*(u16*)0x57008488 & 1))`,即 `HAL_CALIBRATION_32K_CLOCK_DET_STS` 的 bit0(PMU2_CMU `0x57008000` + `0x488`,`hal_32k_clock.c:18`);通用吸收器回 0,等待永不完成。把该状态位建模为「校准完成」(bit0=1)是下一步。WS63 5/5 qtest ×4 QEMU 版本 + BS21 M1 不回归。

### 32K 时钟校准状态建模 → app 跨过校准轮询,继续硬件 bring-up(2026-06-10)

在 GLB 吸收器之上新增一小块 `bs21.clk32k` MMIO 区(PMU2_CMU 的 32K 时钟检测块,`0x57008480`,大小 `0x20`):`DET_STS`(`+0x08` = `0x57008488`)读出 bit0=1(DONE)、bit1=0(非 DOING),于是 `hal_32k_clock_get_detect_result()` 的 `while (!(STS & 1))` 立即完成;CFG/VAL 使能写入为空操作。检测结果读为 0 —— **安全**:`calibration_get_clock_frq()`(clock_calibration.c:55)在除法前有 `if (result != 0)` 守卫,结果为 0 时保留默认 `g_clock_32k = 32768 Hz`。核实了精确访问序列(写 VAL=0x40、查 DOING、清/置 ENABLE、DONE 轮询=1、读 RES=0)共 9 次、无循环。借此 app 跨过 0x901286b2,跑了**多得多**的 init(内存池、**LOS 任务创建** @0x90118xxx、注册表、0x90122/0x90126/0x90128xxx),才到下一关。**下一关**:app 进入一个 20-PC 的紧 ITCM 循环(常驻 boot-stage 服务码 @0x41/0x42/0x45xxx),用 TCXO 延时**轮询 `0x570007a0` 的一个 2-bit 字段**(GLB_CTL_A 区,经描述符表寄存器访问器),其间夹杂 ULP_AON 配置写(`0x5702c934 = 0xc5`、读 `0x5702c330..340`)。通用吸收器回 0,字段永不达到 ready 值 → 死等。这是更深的**时钟/电源域 bring-up**(PLL/时钟切换或 LDO 的 "ready" 状态);正确建模 `0x570007a0` 的 ready 字段需要 BS2X 的 GLB_CTL_A 寄存器图。(另把 `bs21-smoke-test.sh` 修正到 regroup 后的 `examples/bs21` 路径——此前它静默 SKIP=假 PASS。)WS63 5/5 qtest + BS21 M1(uart_hello 横幅 + 13 次 GPIO 翻转、0 illegal trap)均绿。

### 卡死循环追到 eFUSE(v151)+ ULP_AON PMU bring-up(2026-06-10)

把 `0x570007a0` 挖到底。app **确实卡死**(8s 与 25s 时 app PC 覆盖完全相同:3723 个、最大 `0x901662bc`、9 行 UART),卡在一个 **20-PC 的 ITCM 循环**里、**无任何 app PC**——这是一个 init/handler 表迭代(DTCM `0x20002ae4` 处的 `{fn_ptr@0x9019Fxxx, id, 0, fn_ptr@0x90166xxx}` 表),其中某个 handler 跑 **eFUSE + ULP_AON PMU 寄存器操作**,退出条件永不满足。从实时 DTCM dump 解出:`0x425b6` = `hal_efuse_switch_en_set(0xa5a5)`(把 eFUSE 解锁魔数 `0xa5a5` 写到 `g_efuse_switch_en_addr = 0x5702C258`);逐字节循环 `0x4269e` 经 `g_efuse_base = 0x57028030`、读数据 `0x57028800+`、boot-done 状态 `g_efuse_boot_done_addr = 0x5702802C`(bit2 = `efuse_boot2_done`,`EFUSE_BOOT_DONE_MASK 0x4`)迭代 eFUSE 字节。eFUSE IP 是 **v151**(完整源码在 `fbb_ws63/.../hal/efuse/v151/`;`HAL_EFUSE_SWITCH_EN 0xa5a5`)。稳态 MMIO 是一段**多样的**序列(不是单点轮询):eFUSE `0x57028030`/`0x5702887c` + ULP_AON `0x5702c204`/`0x5702c520`/`0x5702c930`/`0x5702c938`/`0x5702c974` 的写(`0xa5a5`/`0x5a5a`/配置)与读。**根因**:eFUSE 控制器(`0x57028000`)与 ULP_AON PMU 状态块(`0x5702c000`)都未建模——吸收器回 0,handler 等的校准/PMU "ready"/trim 数据永不出现。**这是一个独立的、更大的阶段**:建模 **eFUSE v151 控制器**(boot-done bit2 置位、switch-en 接受 `0xa5a5`、读数据返回空白/eFUSE 镜像)**+ ULP_AON PMU 状态寄存器**。确切的 ready 位/期望值需要 BS2X 的 ULP_AON + eFUSE 寄存器图,而这些**不在开源 SDK 源里**(预编译 hal 库/生成头)——所以不像 32K 时钟那样是一处单寄存器小建模,得先拿到寄存器规格(遵循「以 csdk 为唯一标准」,不猜位)。可复用探针:QMP `human-monitor-command "xp/Nxw addr"` 实时 dump DTCM;`-d in_asm` 跨不同时长比 app-PC 覆盖以判「卡死 vs 慢」;`-d unimp` 尾部读稳态 MMIO 足迹。

### 真正根因 = TCXO v150 计数布局(16-bit 分块);eFUSE v151 已建模 → app 跑完全部时钟/PMU/校准 init 到 stage-1 reboot(2026-06-10)

上一节「eFUSE/ULP_AON 状态」的猜测是错的。**关键发现**:app 会**覆写 ITCM**(0x40000)成它自己拷贝的代码,所以之前用 flashboot 反汇编那段循环是反错了字节——dump **实时 ITCM**(QMP `pmemsave`)才看到真相。那个 20-PC 循环是 `uapi_tcxo_delay_us` 忙等:计数读取(`0x42816`)latch 住 TCXO,把 64-bit 计数拼成 `(*0x57000204 & 0xffff) | (*0x57000208 << 16)`(低)和 `(*0x5700020c & 0xffff) | (*0x57000210 << 16)`(高)。按 SDK(`hal_tcxo_v150_regs_def.h`,**真值**)BS21 TCXO 有**四个 16-bit 计数寄存器**(count0[15:0]@+4、count1[31:16]@+8、count2[47:32]@+0C、count3[63:48]@+10;status `valid` = bit4)。我们共享的 TCXO 模型用的是 **WS63 的 2 寄存器布局**(count[31:0]@+4、count[63:32]@+8),于是 app 只拼出 `count[15:0]`(每 ~2ms 回绕)、高位=0 → 延时的 `now < target` 永不成立 → 死等。**修复**:`ws63_tcxo_set_chunked16()`——一个 BS21-only 模式,把计数拆成四个 16-bit 块(WS63 路径不动,默认关 → 字节一致,5/5 qtest 绿)。另外把 **eFUSE v151 控制器**也建了模(`hal_efuse_v151`,真值):boot-done 状态置位、ctl/avdd/clk 回读、128 字节(1024-bit)空白熔丝阵列(trim 读 0 → 校准走默认)、写时按位 OR 编程——忠实的配套基础设施(它不是卡点,但避免吸收器回 0 的 eFUSE boot-done 让 `check_efuse_boot_done` 每次花 50×1ms)。两者一起,app 跨过延时循环、跑完**全部**时钟/PMU/eFUSE/校准 init(新代码 0x9012d5xx/0x9012fxxx),然后**主动 reboot**:`reboot(core=2, cause=0x2003)`(经 `0x9012d59c`,`"APP|Reboot core:%d cause 0x%x"`;reason 存 DTCM 0x2000ffd8,magic 0xdeadbeaf @0x2000ffe8)——core 2 = APPS_CORE;它清 BOOT_PORTING_RESET_REG `0x57004600` 的 bit0 然后 `j .` 等芯片复位。这正是**最初的「core:2」停机,如今是干净到达的**(不再是崩溃),跑完一整轮 init 后的 stage-1 → stage-2 reboot。**下一步**:建模芯片复位触发(0x57004600 bit0 清 → `qemu_system_reset`)让 app 重启进第二阶段;先判 cause 0x2003 是正常校准 reboot 还是错误。WS63 5/5 qtest + BS21 M1(uart_hello 横幅 + 13 次 GPIO 翻转、0 illegal)均绿。**关键探针**:app 会覆写 ITCM——过了 app 交接后,永远反汇编**实时内存**(QMP `pmemsave`),别反汇编装载镜像。

### `cause=0x2003` 那个 reboot 其实是 PANIC,卡在事件等待超时 = 连接性边界(2026-06-10)

判定了上一节的悬念:那个 reboot **不是**干净的 stage-1→2 reboot,而是一次**软件 panic**(没有 CPU trap——mtvec `0x44330` 从未进入,mcause/mepc = 0)。panic 处理器 `0x9012f8ec` 打印 `"APP|[panic]id:%d,code:0x%x,call:0x%x"`,然后 `0x9012f9a0` dump 上下文并调 `reboot(core=2, cause=0x2003)`。触发点是一个**队列消费 + 定时等待循环** `0x9013062e`:它轮询一个软件消息队列(`0x90130368` 读 `0x4bed0`/`0x4bec4` 的链表项)、查 pending 状态(`0x90122cd4` → 2 = pending)、做定时等待(`0x90122d64`),超时就 `panic(id=9)`(cause 0x2003 **不是**看门狗——那些是 reboot_porting.h 里的 0x2002/0x4002/0x8002)。**根因**:它等的那个队列/事件永远不会被生产——生产者需要**事件/消息驱动的连接性栈**(BLE/SLE/radio + 协议/BT 核的中断/IPC),也就是推后的连接性工作,尚未建模。所以**建模芯片复位触发并不会推进启动——只会 reboot 死循环回到同一个 panic**(缺的事件是结构性的,不是首boot状态)。这正是**单核 stage-1 bring-up 的预期终点**:app 跑完全部内核 init + 时钟/PMU/eFUSE/校准,然后阻塞在连接性/事件层。跨过它 = 推后的 BLE/SLE blob + 多核/IPC + 全外设事件工作(项目北极星),数周量级,不是单个寄存器/解码器修复。WS63 5/5 qtest + BS21 M1 均绿(本节纯分析,无代码改动)。

### `bs21_rom_call` 已实现(patches/v10.0.0/0005)

BS21 ROM 调用拦截器已落地(镜像 `ws63_rom_call`,按不相交 PC 区间分发):模拟 BS2X 启动阶段调用的 secure-libc
(`memset_s 0x3d80c`、`memcpy_s 0x3e07e`、`memmove_s 0x3e95c`、`*printf_s @0x3ef..`;printf 复用 `ws63_vformat`)。
**已验证**:`scripts/bs21-rom-call-test.sh` —— guest `jalr` 到 `0x3d80c` 被拦截、memset 生效、回到 `ra`,串口打印 `XA`,**PASS**。
WS63 不回归(5/5 qtest + M1)。
> **关于 loaderboot**:它**完全不调 ROM**(从不执行 0x40000 以下),所以 `bs21_rom_call` 不改变它的行为——它本就停在下载模式空转。
> `bs21_rom_call` 服务的是后续阶段(flashboot/app),那些才大量调 secure-libc。

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
