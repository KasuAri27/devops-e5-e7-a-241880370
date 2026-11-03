# AI使用记录（AI_USAGE）

## 工具/模型/日期
- 工具与模型：Antigravity Coding Agent（Gemini）
- 日期：2026-11-03

## 输入上下文与问题
1. 阅读 `DevOps_E8_E10_20261031` 教学包中的 `00_公共准备.md`、`8_E8_A组.md`、`9_E9_A组.md`、`10_E10_A组.md`、`07_提交与排错.md` 与 `08_个人测试编写示例.md`，梳理 A 组（EChecker）实验流程与验收条件。
2. 针对 A 组自主扩展任务：如何在不破坏原有保守失效（`selective=False`）课堂断言的前提下，在 `labs/e8e10/lab.py` 中实现按目标依赖闭包判断的精确增量失效（`selective=True`），并补充多级传递头文件包含与目标级复用单元测试。

## 模型建议
1. 在 `labs/e8e10/lab.py` 中新增辅助函数 `can_reuse_target(target, key, old, selective=False)`，当 `selective=True` 时检查全局 `recipes / flags / compiler` 以及目标历史真实依赖集合 `old['actual'][target]` 内各文件的预处理指令列表 `directives` 是否一致，未受影响的目标直接复用。
2. 在 `labs/e8e10/test_profile.py` 中加入 `StudentE8A`、`StudentE9A`（含保守失效与 `selective=True` 目标级复用两个测试方法）、`StudentE10A`（三级传递包含 `config.h -> extra.h -> leaf.h`），并在 E10 证据目录下增加 `custom-transitive` 的 5 次重复计时与集合一致性对比。

## 采纳/拒绝及理由
- **采纳**：采纳 `can_reuse_target` 目标依赖闭包检查方案与 4 项新增单元测试。理由是 `old['actual'][target]` 已经包含上一次 `gcc -MM` 采集到的全部直接与间接本地头文件，只要闭包内所有文件的 `#` 预处理指令行未变且编译参数/配方未变，该目标的头文件依赖图必定不变，既能保证与全量扫描 100% 集合一致，又能避免无关目标（如 `helper.o`）重复调用 `gcc -MM`。
- **拒绝**：拒绝直接替换 `scan()` 默认行为为仅刷新单目标，因为 E9 第 7 步与 E10 第 4/6/7 步实操脚本显式断言默认保守模式下 `set(r['refreshed']) == {'main.o', 'helper.o'}`；采用默认 `selective=False`、可选 `selective=True` 的方式兼顾了课程基线兼容性与扩展验证。

## 人工修改
- 核对了服务器运行环境（`course-e8e10:241880370` 镜像 ID、容器禁网 `--network none` 与 `--cap-add SYS_PTRACE` 权限），确认所有实验数据、Git 提交 SHA、`strace` PID/行号与 5 次计时中位数均来自服务器容器真实运行，未使用静态伪造数据。

## 实际验证命令/输入/结果
1. **单元测试验证**：
   - 命令：`docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD:/course" -w /course "course-e8e10:241880370" python3 -m unittest discover -s labs/e8e10 -p test_profile.py -v`
   - 输入：原 7 项 `ProfileTests` + 新增 4 项 `StudentE8A / StudentE9A / StudentE10A` 测试。
   - 结果：`Ran 11 tests in 0.291s - OK`（`TEST_EXIT_CODE=0`，日志保存在 `work/unit-tests-20261103-100558.log`）。
2. **分步实操与自主扩展验证**：
   - 命令：按 `8_E8_A组.md`、`9_E9_A组.md`、`10_E10_A组.md` 逐步执行 `lab_new_run` 与 `lab_python`。
   - 结果：
     - E8（`work/e8-A-manual.Ot2223`）：`BASELINE_PASS`、`BUILDCHECKER_BASELINE_PASS`、`REUSE_PASS`；
     - E9（`work/e9-A-manual.0mx4pJ`）：`C0_BUILD_AND_BASELINE_PASS`、`C1_REUSE_PASS`、`C2_REFRESH_PASS`、`C3_RESOLVED_PASS`；
     - E10（`work/e10-A-manual.ZkijlZ`）：`MATRIX_PASS`（30 行全部 `equal=True`）、`DYNAMIC_CROSSCHECK_AND_MATRIX_PASS`、`CUSTOM_TRANSITIVE_SELECTIVE_PASS`（5 次重复 `equal=True`，`selective=True` 加速比 `1.545x`）。
3. **参考实现与个人贡献边界**：
   - 参考实现：`run_lab.py`、`labs/e8e10/environment/`、`labs/e8e10/lab.py` 原有函数及 `ProfileTests` 原 7 项测试来自课程实验包 `03_实验包`。
   - 个人贡献：`labs/e8e10/lab.py` 中的 `can_reuse_target()` 与 `scan(..., selective=False)` 扩展、`labs/e8e10/test_profile.py` 中的 `StudentE8A / StudentE9A / StudentE10A` 共 4 项单元测试、`work/e10-A-manual.ZkijlZ/custom-transitive` 扩展实验以及 `docs/students/241880370/e8-e10/` 下的三份实验文档。
