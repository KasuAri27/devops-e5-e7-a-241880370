# 决策记录（ADR）：A组 EChecker 增量依赖图缓存失效与配置身份绑定

## 背景与约束
在 C/Make 项目的持续集成与增量提交场景（E8—E10）中，每次提交均执行完整 `make clean` + `strace` 全量系统调用跟踪（如 `BuildChecker` 耗时约 `127 ms`）或对全部编译目标无条件重跑预处理器（`gcc -MM`，约 `10.0 ms`）会带来重复开销。需要在受限 C/Make 教学配置（显式目标规则、本地头文件、`gcc` 编译器）下设计增量依赖图的缓存键（`key`）与失效策略，确保：
1. 任何可能改变真实头文件读取集合的源码或编译配置变更都不会漏刷新（零假阴性 / 与全量扫描 100% 集合一致）；
2. 仅修改普通函数体表达式或仅修改 `Makefile` 声明行时，能直接复用历史真实依赖图。

## 选择与替代方案
1. **配置身份绑定（Cache Key 结构）**：
   - 将配置身份绑定为四元组 `key = {directives, recipes, flags, compiler}`：
     - `directives`：项目中所有 `.c` / `.h` 文件内以 `#` 开头的预处理指令行有序列表（覆盖直接与间接 `#include`、`#define`、`#if` 等变更）；
     - `recipes`：`Makefile` 中所有以 `\t` 开头的编译/链接配方行；
     - `flags`：解析后的 `CFLAGS` 编译参数（白名单校验 `-O0`、`-O1`、`-O0 -DMODE=1`，对未知参数如 `-include` 显式抛出 `UNSUPPORTED_FLAGS` 拒绝）；
     - `compiler`：`gcc --version` 首行版本签名。
   - **声明图（`declared`）与真实图（`actual`）解耦**：每次扫描始终重新解析 `Makefile` 的目标依赖声明（开销极低），但真实依赖图 `actual` 通过 `key` 决定复用或调用 `gcc -MM` 刷新，随后在最新 `(actual, declared)` 上重算 `MISSING` 与 `REDUNDANT` 及增量差分 `added` / `resolved`。
2. **缓存失效粒度（保守全局失效 vs. 目标闭包精确失效）**：
   - **方案 A（默认保守全局失效，`selective=False`）**：只要全局 `old['key'] != key`，所有目标（`main.o`、`helper.o`）全部重新运行 `gcc -MM`。优点是实现极简、绝对安全；缺点是单个文件新增 `#include` 时会连带刷新无关目标。
   - **方案 B（扩展实现：基于历史目标依赖闭包的选择性失效，`can_reuse_target(..., selective=True)`）**：当全局 `recipes`、`flags`、`compiler` 未变时，针对每个目标 `t` 检查其历史真实依赖集合 `old['actual'][t]`（含源 `.c` 及全部直接/传递包含的本地 `.h`）中每个文件的 `directives` 是否与历史一致。若一致则直接复用 `old['actual'][t]`，仅对闭包内预处理指令发生变更的目标重跑 `gcc -MM`。
   - **最终决策**：在 `labs/e8e10/lab.py` 中同时提供两种模式——默认 `selective=False` 保持与课程分步实操基线断言 100% 兼容，同时通过 `can_reuse_target` 支持 `selective=True` 目标级精确失效，并在 `StudentE9A` 及 E10 自主扩展实验中完成验证。

## 代价与覆盖范围
- **代价**：每次扫描需读取项目内全部 `.c`/`.h` 提取 `#` 开头行并调用一次 `gcc --version`（固定开销约 `1.7 ms`），因此在极小样例且全目标失效（如 `flags` 改变）时，增量扫描耗时（约 `10.1 ms`）与全量扫描（约 `10.0 ms`）基本持平（加速比 `0.97x~0.99x`）。
- **收益**：在代码体修改（`body`）、声明修复（`declaration`）及未变化（`unchanged`）场景下，扫描耗时从 `10.0 ms` 降至 `1.74~1.79 ms`（**加速比 `5.56x~5.95x`**）；在单目标传递头文件变更场景下开启 `selective=True`，耗时降至 `6.48 ms`（**加速比 `1.545x`**）。
- **覆盖范围与边界**：覆盖显式规则与项目内头文件的直接/多级传递包含（如 `main.c -> config.h -> extra.h -> leaf.h`）；不支持隐式模式规则（`%`）、Order-only 依赖（`|`）或构建期动态生成源码，遇到越界配置时显式抛出 `ValueError` 拒绝而非静默漏报。

## 验证命令与实际证据
- **单元测试验证**：
  ```bash
  docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD:/course" -w /course course-e8e10:241880370 python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v
  ```
  - 实际证据：`work/unit-tests-20261103-100558.log`（11 项测试全部 `OK`，`TEST_EXIT_CODE=0`）。
- **阶段与矩阵验证**：
  - E8 基线与复用：`work/e8-A-manual.Ot2223/baseline.json`、`work/e8-A-manual.Ot2223/incremental.json`、`work/e8-A-manual.Ot2223/buildchecker/findings.json`。
  - E9 连续提交演化：`work/e9-A-manual.0mx4pJ/C1.json`、`C2.json`、`C3.json`。
  - E10 30 行矩阵与自主扩展 5 次测量：`work/e10-A-manual.ZkijlZ/matrix/results.csv`、`performance-summary.csv`、`gate.json` 及 `work/e10-A-manual.ZkijlZ/custom-transitive/custom-summary.json`。
