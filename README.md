# E5–E7 A 组：BuildChecker

学号 241880370 的 DevOps 实验代码、测试与报告。实现来源是课程教学参考包，修改及 AI 协助范围在报告中列明。

- [实验报告](docs/实验报告.md) 与 [验收记录](docs/验收记录.csv)。
- [正常 CI](https://github.com/KasuAri27/devops-e5-e7-a-241880370/actions/runs/40179739134)、[故意失败 CI](https://github.com/KasuAri27/devops-e5-e7-a-241880370/actions/runs/40179963889)、[恢复 CI](https://github.com/KasuAri27/devops-e5-e7-a-241880370/actions/runs/40261914861)。
- [PR #1](https://github.com/KasuAri27/devops-e5-e7-a-241880370/pull/1) 记录真实拒绝合并和修正后普通合并。

最终服务测试为 17 项，独立判定测试 6 项，完整门禁 8 项。样例检测得到 MD(main.o, config.h) 与 RD(main.o, unused.h)，修复后 findings 为空。

报告中的 `work/` 相对链接指向提交压缩包内的原始证据；运行产物不提交到 Git。线上证据可通过上面的 Actions 链接查看，完整 artifact 已备份到提交包。

## 从仓库根目录运行

实验宿主需要 Linux、Python、Git 和 Docker；镜像构建需要访问 Docker Hub、Debian 软件源和 PyPI。云主机原始内存自检结果及代理构建过程已在报告中如实记录。

```bash
python3 scripts/lab_cloud.py doctor
python3 scripts/lab_cloud.py build --out work/build-new --build-timeout 1200
python3 scripts/lab_cloud.py e5 --out work/e5-new
python3 scripts/lab_cloud.py e6 --out work/e6-before-new
python3 scripts/lab_cloud.py e6 --fixed --out work/e6-after-new
python3 scripts/verify_e6_evidence.py --before work/e6-before-new/evidence/findings.json --after work/e6-after-new/evidence/findings.json
python3 -m unittest discover -s tests/e7 -v
python3 scripts/lab_cloud.py gate --out work/e7-new
```

原始缺陷样例的 e6 命令因 `--fail-on-findings` 预期退出 1，门禁对正确识别的缺陷和故障判 PASS。每次重跑应使用新的输出目录。

## CI 演示材料

`.github/workflows/e7-quality-gate.yml` 自动构建、测试、扫描并上传 artifact。`ci/A-main-protection.json` 是本次使用的保护配置；`ci/rejection-demo/A/` 保留故意失败及修正后的测试，复制到 `services/buildchecker/tests/` 后可重现教学流程。

本项目是单 Make 进程、每个 recipe 一个最终输出的教学实现，完整论文基准及后续 EChecker 不在本次范围。
