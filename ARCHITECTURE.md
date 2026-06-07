# bs2x-guide — 架构

`bs2x-guide` 是 HiSilicon BS21/BS2X 的用户指南（Sphinx + MyST + sphinx-book-theme），
角色与 `ws63-guide` 对等，是 BS2X 三件套独立文档的一环：

```
bs2x-svd  (CMSIS-SVD 真值)  ──svd2rust──▶  bs2x-pac  ──chip-bs21──▶  hisi-riscv-hal
   ▲                                          ▲
   └──────────── fbb_bs2x SDK ────────────────┘
bs2x-guide  (本仓，配套用户指南)
```

- 真值源：`/root/fbb_bs2x`（以 csdk 为唯一标准）。
- 同族对照：`ws63-guide`（WS63 用户指南）。
- 配套代码：`bs2x-pac`、`hisi-riscv-hal`(`chip-bs21`)、`hisi-riscv-qemu`(`-M bs21`)、`bs21-examples`。

详见伞仓 <https://github.com/sanchuanhehe/hisi-riscv-rs>。
