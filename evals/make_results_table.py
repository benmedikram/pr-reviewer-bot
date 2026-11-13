# evals/make_results_table.py
# Usage: python evals/make_results_table.py <labeled csv> [id,id,...]
# Writes <csv stem>_table.md (all rows) or <csv stem>_cases.md (listed ids).
import csv
import sys
from pathlib import Path

src = Path(sys.argv[1])
rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))
wanted = {int(x) for x in sys.argv[2].split(",")} if len(sys.argv) > 2 else None


def cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


lines = ["| id | PR | Bot finding | Reference issue | Match | Verdict | Justification |",
         "|---|---|---|---|---|---|---|"]
for r in rows:
    if wanted is not None and int(r["id"]) not in wanted:
        continue
    where = f"`{r['file'].split('/')[-1]}:{r['line']}`"
    lines.append(f"| {r['id']} | {r['pr']} | {where} {cell(r['finding'])} | "
                 f"{cell(r['reference_id']) or '-'} | {r['match']} | {r['verdict']} | {cell(r['justification'])} |")

out = src.with_name(src.stem + ("_cases.md" if wanted else "_table.md"))
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(lines) - 2} rows -> {out}")