#!/usr/bin/env python3
"""cross-border-listing-ma-finance-practice 技能验证脚本。

断言"上市/并购分析产出=合规成立"：
- GOOD 样例：含全部合规要素（境外上市备案核查/ODI 审批链/税务结构/审计要求），且无违规 → exit 0
- BAD 样例：命中任一违规模式（分拆出境/VIE 免备案/跳过备案/代持）→ exit 1

退出码契约：0=通过，1=存在错误，2=文件错误。
"""
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_FILE_ERROR = 2


def read_sample(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)
    return p.read_text(encoding="utf-8")


GOOD_REQUIREMENTS = [
    (r"备案|证监会", "缺少证监会境外上市备案核查"),
    (r"ODI|发改.{0,6}商务.{0,6}外汇|三部门", "缺少 ODI 三部门审批链核查"),
    (r"10%|受益所有人|预提", "缺少税务结构核查（协定/受益所有人）"),
    (r"PCAOB|审计", "缺少审计合规要求（PCAOB/目标市场）"),
    (r"37\s*号文", "缺少 37 号文登记检查"),
]

BAD_VIOLATIONS = [
    (r"分批.{0,4}出境|分拆.{0,6}(购汇|汇出|出境)", "命中违规：分拆/分批出境规避监管"),
    (r"避免.{0,8}(监管|审查|关注|触发)", "命中违规：以规避监管为策略"),
    (r"VIE.{0,12}(无需|不用|绕开|规避).{0,6}(备案|监管|审批)|(?<!不)(?<!非)免备案", "命中违规：VIE 免备案话术"),
    (r"(跳过|无需|免办).{0,6}(备案|审批|ODI|登记)", "命中违规：跳过备案/审批"),
    (r"代持|借.{0,4}他人.{0,6}名义", "命中违规：代持规避"),
    (r"(先|资金?先).{0,6}(出境|汇出).{0,10}(后|再).{0,6}(补|办)", "命中违规：先出境后补手续"),
]


def find_violations(text: str) -> list:
    hits = []
    for pattern, msg in BAD_VIOLATIONS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(msg)
    return hits


def find_missing_good(text: str) -> list:
    missing = []
    for pattern, msg in GOOD_REQUIREMENTS:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(msg)
    return missing


def main():
    if len(sys.argv) < 2:
        print("用法: validate.py <sample.md>", file=sys.stderr)
        sys.exit(EXIT_FILE_ERROR)

    sample_path = sys.argv[1]
    text = read_sample(sample_path)
    fname = Path(sample_path).name.lower()
    is_bad = "bad" in fname

    errors = []

    violations = find_violations(text)
    if is_bad:
        if not violations:
            errors.append("BAD 样例未命中任何已知违规模式（应至少命中一条）")
        else:
            errors.append(f"BAD 样例命中 {len(violations)} 条违规（预期失败）：{'; '.join(violations)}")
    else:
        if violations:
            errors.append(f"GOOD 样例命中违规（不应有）：{'; '.join(violations)}")
        missing = find_missing_good(text)
        errors.extend(missing)

    if errors:
        print(f"验证失败（{len(errors)} 项）：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(EXIT_FAIL)

    print("验证通过")
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
