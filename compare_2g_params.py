#!/usr/bin/env python3
"""Compare Huawei 2G cell parameter dumps: Pre (26 Apr) vs Post (13 Sep)."""

from __future__ import annotations

import gc
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pyxlsb import open_workbook

PRE_PATH = "/tmp/extract_pre/2G Cell Parameters Data_26April26_Pre.xlsb"
POST_PATH = "/tmp/extract_post/2G Cell Parameters Data_13Sep26_Post.xlsb"
PARAM_LIST_PATH = "/workspace/GSM_Parameter List_Huawei_v1.0.xlsb"

SKIP_SHEETS = {
    "Cover",
    "HOME",
    "UserSelectMoc",
    "CMETemplateInfo",
    "FileIdentification",
    "Cover_ENG",
    "GCELLSBC_SCHEME_ENUM",
}

# Identity / location columns — not radio parameters
SKIP_PARAMS = {
    "BSCName",
    "BTSNAME",
    "CELLNAME",
    "CELLID",
    "Thana",
    "Dis",
    "Region",
    "REMARK",
    "OPNAME",
    "NSEI",
    "BVCI",
}

KEY_PARAMS = {"BSCName", "CELLNAME"}

CDR_KEYWORDS = re.compile(
    r"\b(drop|cdr|handover|hand.?over|radio link|rlt|quality|rxqual|rxlev|"
    r"interfere|timer|t310|t312|sacch|power control|ta\b|timing advance|"
    r"call drop|bad quality|emergency ho|ho fail|assignment fail|"
    r"access fail|rach|sddyn|congestion|preemption|directed retry|"
    r"ul pc|dl pc|dtx|fer|ber|ho thresh|ho hyst|penalty|ncell|"
    r"reselect|idle|ta drop|max ta|level|qual)\b",
    re.I,
)

OUT_DIR = Path("/workspace")
PROGRESS = Path("/tmp/compare_progress.log")


def log(msg: str) -> None:
    print(msg, flush=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.10g}"
    if isinstance(v, int):
        return str(v)
    s = str(v).strip()
    if s.lower() in {"none", "nan", "null"}:
        return ""
    if s.endswith(".0") and s.replace(".", "", 1).lstrip("-").isdigit():
        return s[:-2]
    return s


def row_vals(row) -> list:
    return [c.v for c in row]


def load_param_catalog() -> dict[tuple[str, str], dict]:
    """(MO, Parameter ID) -> metadata from Huawei parameter list."""
    cat: dict[tuple[str, str], dict] = {}
    with open_workbook(PARAM_LIST_PATH) as wb:
        with wb.get_sheet(1) as sh:
            it = sh.rows()
            header = [norm(c.v) for c in next(it)]
            idx = {name: i for i, name in enumerate(header) if name}

            def get(vals, col, default=""):
                i = idx.get(col)
                if i is None or i >= len(vals):
                    return default
                return vals[i] if vals[i] is not None else default

            for row in it:
                vals = row_vals(row)
                mo = norm(get(vals, "MO"))
                pid = norm(get(vals, "Parameter ID"))
                if not mo or not pid:
                    continue
                meaning = get(vals, "Meaning")
                impact = get(vals, "Impact on Radio Network Performance")
                rec = get(vals, "Recommended Value")
                default = get(vals, "Default Value")
                rng = get(vals, "GUI Value Range")
                pname = get(vals, "Parameter Name")
                cat[(mo, pid)] = {
                    "name": norm(pname) if not isinstance(pname, str) else str(pname or ""),
                    "meaning": str(meaning or "").strip(),
                    "impact": str(impact or "").strip(),
                    "recommended": str(rec or "").strip(),
                    "default": str(default or "").strip(),
                    "range": str(rng or "").strip(),
                    "mml": str(get(vals, "MML Command") or "").strip(),
                }
                # keep first occurrence if duplicates
                if (mo, pid) not in cat:
                    pass
    log(f"Loaded parameter catalog: {len(cat)} entries")
    return cat


def load_mo_desc(path: str) -> dict[str, str]:
    desc = {}
    with open_workbook(path) as wb:
        if "HOME" not in wb.sheets:
            return desc
        with wb.get_sheet("HOME") as sh:
            it = sh.rows()
            next(it)  # header
            for row in it:
                vals = row_vals(row)
                if len(vals) >= 2 and vals[0]:
                    desc[norm(vals[0])] = str(vals[1] or "")
    return desc


def load_sheet(path: str, sheet: str):
    """Return (param_ids, param_names, records keyed by (BSC, CELL[, extra]))."""
    with open_workbook(path) as wb:
        with wb.get_sheet(sheet) as sh:
            it = sh.rows()
            try:
                ids_raw = row_vals(next(it))
                names_raw = row_vals(next(it))
            except StopIteration:
                return [], [], {}

            ids = [norm(x) if x is not None else f"COL{i}" for i, x in enumerate(ids_raw)]
            names = [str(x).strip() if x is not None else "" for x in names_raw]
            # PRE GCELL has unnamed location cols
            for i, pid in enumerate(ids):
                if pid.startswith("COL") and i < len(names) and names[i]:
                    ids[i] = names[i].replace(" ", "")

            id_to_idx = {}
            for i, pid in enumerate(ids):
                if pid and pid not in id_to_idx:
                    id_to_idx[pid] = i

            bsc_i = id_to_idx.get("BSCName")
            cell_i = id_to_idx.get("CELLNAME")
            extra_keys = []
            for k in ("NSEI", "BVCI"):
                if k in id_to_idx:
                    extra_keys.append((k, id_to_idx[k]))

            records = {}
            n_rows = 0
            for row in it:
                vals = [norm(c.v) for c in row]
                n_rows += 1
                if bsc_i is None or cell_i is None:
                    # no cell key — skip
                    continue
                if bsc_i >= len(vals) or cell_i >= len(vals):
                    continue
                bsc, cell = vals[bsc_i], vals[cell_i]
                if not bsc and not cell:
                    continue
                key_parts = [bsc, cell]
                for _, ei in extra_keys:
                    key_parts.append(vals[ei] if ei < len(vals) else "")
                key = tuple(key_parts)
                # keep first occurrence
                if key in records:
                    continue
                records[key] = vals
            return ids, names, records


def is_cdr_related(pid: str, pname: str, meaning: str, impact: str) -> bool:
    blob = " ".join([pid, pname, meaning, impact])
    return bool(CDR_KEYWORDS.search(blob))


def top_transitions(counter: Counter, n: int = 8) -> str:
    items = counter.most_common(n)
    parts = []
    for (a, b), c in items:
        a_s = a if a != "" else "(empty)"
        b_s = b if b != "" else "(empty)"
        parts.append(f"{a_s} → {b_s} ({c})")
    return "; ".join(parts)


def write_xlsx(summary_rows, sheet_stats, new_cells, del_cells, cat, mo_desc, out_path):
    wb = Workbook()

    # styles
    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
    alt_fill = PatternFill("solid", fgColor="D6EAF8")
    cdr_fill = PatternFill("solid", fgColor="FDEBD0")
    top_fill = PatternFill("solid", fgColor="F5B7B1")
    thin = Border(
        left=Side(style="thin", color="BFBFBF"),
        right=Side(style="thin", color="BFBFBF"),
        top=Side(style="thin", color="BFBFBF"),
        bottom=Side(style="thin", color="BFBFBF"),
    )
    wrap = Alignment(wrap_text=True, vertical="top")

    def style_header(ws, ncols):
        ws.auto_filter.ref = f"A1:{get_column_letter(ncols)}1"
        ws.freeze_panes = "A2"
        for col in range(1, ncols + 1):
            cell = ws.cell(1, col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")

    def autosize(ws, widths):
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

    # ----- Sheet 1: Ranked parameter changes -----
    ws = wb.active
    ws.title = "Changed Parameters (Ranked)"
    headers = [
        "Rank",
        "MO",
        "MO Description",
        "Parameter ID",
        "Parameter Name",
        "Cells Changed",
        "% of Common Cells",
        "Common Cells",
        "Distinct Transitions",
        "Top Value Changes (Pre → Post)",
        "CDR Related",
        "Meaning",
        "Impact on Radio Network Performance",
        "Recommended Value",
        "Default Value",
        "GUI Range",
    ]
    ws.append(headers)
    style_header(ws, len(headers))

    for i, r in enumerate(summary_rows, 1):
        ws.append(
            [
                i,
                r["mo"],
                r["mo_desc"],
                r["pid"],
                r["pname"],
                r["n_changed"],
                r["pct"],
                r["n_common"],
                r["n_trans"],
                r["transitions"],
                "YES" if r["cdr"] else "NO",
                r["meaning"],
                r["impact"],
                r["recommended"],
                r["default"],
                r["range"],
            ]
        )
        fill = None
        if i <= 20:
            fill = top_fill
        elif r["cdr"]:
            fill = cdr_fill
        elif i % 2 == 0:
            fill = alt_fill
        for col in range(1, len(headers) + 1):
            cell = ws.cell(i + 1, col)
            cell.border = thin
            cell.alignment = wrap
            if fill:
                cell.fill = fill
        ws.row_dimensions[i + 1].height = 48 if i <= 80 else 30

    autosize(ws, [8, 22, 36, 28, 40, 16, 18, 16, 18, 70, 14, 70, 50, 20, 18, 22])
    ws.row_dimensions[1].height = 30

    # ----- Sheet 2: CDR-related only -----
    ws2 = wb.create_sheet("CDR Related Changes")
    ws2.append(headers)
    style_header(ws2, len(headers))
    cdr_rows = [r for r in summary_rows if r["cdr"]]
    for i, r in enumerate(cdr_rows, 1):
        ws2.append(
            [
                i,
                r["mo"],
                r["mo_desc"],
                r["pid"],
                r["pname"],
                r["n_changed"],
                r["pct"],
                r["n_common"],
                r["n_trans"],
                r["transitions"],
                "YES",
                r["meaning"],
                r["impact"],
                r["recommended"],
                r["default"],
                r["range"],
            ]
        )
        fill = top_fill if i <= 15 else (alt_fill if i % 2 == 0 else None)
        for col in range(1, len(headers) + 1):
            cell = ws2.cell(i + 1, col)
            cell.border = thin
            cell.alignment = wrap
            if fill:
                cell.fill = fill
        ws2.row_dimensions[i + 1].height = 45
    autosize(ws2, [8, 22, 36, 28, 40, 16, 18, 16, 18, 70, 14, 70, 50, 20, 18, 22])
    ws2.row_dimensions[1].height = 30

    # ----- Sheet 3: MO / sheet stats -----
    ws3 = wb.create_sheet("MO Comparison Stats")
    h3 = [
        "MO",
        "MO Description",
        "Pre Cells",
        "Post Cells",
        "Common Cells",
        "New in Post",
        "Removed since Pre",
        "Params Compared",
        "Params Changed",
        "Total Cell-Param Changes",
        "Params only in Pre",
        "Params only in Post",
    ]
    ws3.append(h3)
    style_header(ws3, len(h3))
    for i, s in enumerate(sheet_stats, 1):
        ws3.append(
            [
                s["mo"],
                s["mo_desc"],
                s["n_pre"],
                s["n_post"],
                s["n_common"],
                s["n_new"],
                s["n_del"],
                s["n_params"],
                s["n_params_changed"],
                s["n_total_changes"],
                s["only_pre"],
                s["only_post"],
            ]
        )
        for col in range(1, len(h3) + 1):
            cell = ws3.cell(i + 1, col)
            cell.border = thin
            if i % 2 == 0:
                cell.fill = alt_fill
    autosize(ws3, [24, 40, 12, 12, 14, 14, 18, 16, 16, 24, 28, 28])

    # ----- Sheet 4: inventory -----
    ws4 = wb.create_sheet("Cell Inventory")
    h4 = ["Item", "Count"]
    ws4.append(h4)
    style_header(ws4, 2)
    ws4.append(["Pre cells (GCELL)", sheet_stats[0]["n_pre"] if sheet_stats else ""])
    # find GCELL stats
    g = next((x for x in sheet_stats if x["mo"] == "GCELL"), None)
    if g:
        ws4.append(["Pre cells (GCELL)", g["n_pre"]])
        ws4.append(["Post cells (GCELL)", g["n_post"]])
        ws4.append(["Common cells", g["n_common"]])
        ws4.append(["New cells in Post (added after Apr 26)", g["n_new"]])
        ws4.append(["Cells removed since Pre", g["n_del"]])
    ws4.append(["Parameters with at least 1 change", len(summary_rows)])
    ws4.append(["CDR-related parameters with changes", len(cdr_rows)])
    autosize(ws4, [50, 18])

    ws5 = wb.create_sheet("New Cells (Post only)")
    ws5.append(["BSCName", "CELLNAME"])
    style_header(ws5, 2)
    for i, k in enumerate(sorted(new_cells)[:50000], 1):
        ws5.append([k[0], k[1]])
        if i % 2 == 0:
            ws5.cell(i + 1, 1).fill = alt_fill
            ws5.cell(i + 1, 2).fill = alt_fill
    autosize(ws5, [18, 24])

    ws6 = wb.create_sheet("Removed Cells (Pre only)")
    ws6.append(["BSCName", "CELLNAME"])
    style_header(ws6, 2)
    for i, k in enumerate(sorted(del_cells)[:50000], 1):
        ws6.append([k[0], k[1]])
        if i % 2 == 0:
            ws6.cell(i + 1, 1).fill = alt_fill
            ws6.cell(i + 1, 2).fill = alt_fill
    autosize(ws6, [18, 24])

    wb.save(out_path)
    log(f"Wrote Excel: {out_path}")


def write_markdown(summary_rows, sheet_stats, new_cells, del_cells, out_path):
    g = next((x for x in sheet_stats if x["mo"] == "GCELL"), None)
    cdr_rows = [r for r in summary_rows if r["cdr"]]
    lines = []
    lines.append("# 2G Cell Parameter Comparison — Pre vs Post")
    lines.append("")
    lines.append("**Pre dump:** 2G Cell Parameters Data_26April26_Pre")
    lines.append("")
    lines.append("**Post dump:** 2G Cell Parameters Data_13Sep26_Post")
    lines.append("")
    lines.append("**Parameter descriptions:** GSM_Parameter List_Huawei_v1.0")
    lines.append("")
    lines.append("Scope: all cell-level MOs present in both workbooks. Identity columns (BSC/BTS/Cell name/index) are excluded. Ranked by number of cells whose value changed.")
    lines.append("")
    lines.append("## Network inventory")
    lines.append("")
    if g:
        lines.append(f"- Pre cells: **{g['n_pre']:,}**")
        lines.append(f"- Post cells: **{g['n_post']:,}**")
        lines.append(f"- Common cells compared: **{g['n_common']:,}**")
        lines.append(f"- New cells in Post: **{g['n_new']:,}**")
        lines.append(f"- Cells removed since Pre: **{g['n_del']:,}**")
    lines.append(f"- Parameters with any change: **{len(summary_rows):,}**")
    lines.append(f"- Of those, CDR/radio-performance related: **{len(cdr_rows):,}**")
    lines.append("")
    lines.append("## Changed parameters (highest change count first)")
    lines.append("")
    lines.append("| Rank | MO | Parameter ID | Parameter Name | Cells Changed | % Common | Top Pre → Post transitions | CDR related |")
    lines.append("|---:|---|---|---|---:|---:|---|---|")
    for i, r in enumerate(summary_rows[:150], 1):
        trans = r["transitions"].replace("|", "/")
        lines.append(
            f"| {i} | {r['mo']} | `{r['pid']}` | {r['pname']} | {r['n_changed']:,} | {r['pct']} | {trans} | {'YES' if r['cdr'] else ''} |"
        )
    lines.append("")
    lines.append("## CDR-related parameter changes")
    lines.append("")
    lines.append("These parameters are tagged because their Huawei meaning/impact mentions drop, handover, quality, timers, power control, TA, access, or similar radio-failure mechanisms.")
    lines.append("")
    for i, r in enumerate(cdr_rows[:40], 1):
        meaning = (r["meaning"] or "").replace("\n", " ")
        if len(meaning) > 400:
            meaning = meaning[:400] + "..."
        impact = (r["impact"] or "").replace("\n", " ")
        if len(impact) > 300:
            impact = impact[:300] + "..."
        lines.append(f"### {i}. {r['mo']} / {r['pid']} — {r['pname']}")
        lines.append("")
        lines.append(f"- Cells changed: **{r['n_changed']:,}** ({r['pct']} of {r['n_common']:,} common cells)")
        lines.append(f"- Value changes: {r['transitions']}")
        if meaning:
            lines.append(f"- Meaning: {meaning}")
        if impact:
            lines.append(f"- Radio impact: {impact}")
        if r["recommended"]:
            lines.append(f"- Recommended: {r['recommended']}")
        lines.append("")
    lines.append("## MO-level change volume")
    lines.append("")
    lines.append("| MO | Description | Params changed | Total cell-param diffs | Common cells |")
    lines.append("|---|---|---:|---:|---:|")
    for s in sorted(sheet_stats, key=lambda x: -x["n_total_changes"]):
        if s["n_total_changes"] == 0 and s["n_params_changed"] == 0:
            continue
        lines.append(
            f"| {s['mo']} | {s['mo_desc']} | {s['n_params_changed']} | {s['n_total_changes']:,} | {s['n_common']:,} |"
        )
    lines.append("")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    log(f"Wrote markdown: {out_path}")


def main():
    PROGRESS.write_text("", encoding="utf-8")
    log("Starting comparison")
    cat = load_param_catalog()
    mo_desc = load_mo_desc(PRE_PATH)
    mo_desc.update(load_mo_desc(POST_PATH))

    with open_workbook(PRE_PATH) as wb:
        pre_sheets = [s for s in wb.sheets if s not in SKIP_SHEETS]
    with open_workbook(POST_PATH) as wb:
        post_sheets = set(wb.sheets)

    summary_rows = []
    sheet_stats = []
    new_cells = set()
    del_cells = set()
    inventory_done = False

    for si, sheet in enumerate(pre_sheets, 1):
        if sheet not in post_sheets:
            log(f"[{si}/{len(pre_sheets)}] SKIP {sheet} (not in Post)")
            continue
        log(f"[{si}/{len(pre_sheets)}] Loading {sheet} ...")
        pre_ids, pre_names, pre_rec = load_sheet(PRE_PATH, sheet)
        post_ids, post_names, post_rec = load_sheet(POST_PATH, sheet)
        log(f"    pre={len(pre_rec)} post={len(post_rec)}")

        pre_map = {pid: i for i, pid in enumerate(pre_ids)}
        post_map = {pid: i for i, pid in enumerate(post_ids)}
        name_map = {}
        for i, pid in enumerate(pre_ids):
            if i < len(pre_names) and pre_names[i]:
                name_map[pid] = pre_names[i]
        for i, pid in enumerate(post_ids):
            if pid not in name_map and i < len(post_names) and post_names[i]:
                name_map[pid] = post_names[i]

        common_keys = pre_rec.keys() & post_rec.keys()
        only_pre_keys = pre_rec.keys() - post_rec.keys()
        only_post_keys = post_rec.keys() - pre_rec.keys()

        if sheet == "GCELL":
            new_cells = {(k[0], k[1]) for k in only_post_keys}
            del_cells = {(k[0], k[1]) for k in only_pre_keys}
            inventory_done = True

        params = [
            p
            for p in pre_map
            if p in post_map and p not in SKIP_PARAMS and p and not p.startswith("COL")
        ]
        only_pre_p = [p for p in pre_map if p not in post_map and p not in SKIP_PARAMS]
        only_post_p = [p for p in post_map if p not in pre_map and p not in SKIP_PARAMS]

        n_total_changes = 0
        n_params_changed = 0

        for pid in params:
            pi = pre_map[pid]
            qi = post_map[pid]
            n_changed = 0
            trans = Counter()
            for k in common_keys:
                a = pre_rec[k][pi] if pi < len(pre_rec[k]) else ""
                b = post_rec[k][qi] if qi < len(post_rec[k]) else ""
                if a != b:
                    n_changed += 1
                    trans[(a, b)] += 1
            if n_changed == 0:
                continue
            n_params_changed += 1
            n_total_changes += n_changed
            meta = cat.get((sheet, pid), {})
            pname = meta.get("name") or name_map.get(pid) or pid
            meaning = meta.get("meaning", "")
            impact = meta.get("impact", "")
            n_common = len(common_keys)
            pct = f"{(100.0 * n_changed / n_common):.2f}%" if n_common else "n/a"
            summary_rows.append(
                {
                    "mo": sheet,
                    "mo_desc": mo_desc.get(sheet, ""),
                    "pid": pid,
                    "pname": pname,
                    "n_changed": n_changed,
                    "pct": pct,
                    "n_common": n_common,
                    "n_trans": len(trans),
                    "transitions": top_transitions(trans, 8),
                    "cdr": is_cdr_related(pid, pname, meaning, impact),
                    "meaning": meaning,
                    "impact": impact,
                    "recommended": meta.get("recommended", ""),
                    "default": meta.get("default", ""),
                    "range": meta.get("range", ""),
                }
            )

        sheet_stats.append(
            {
                "mo": sheet,
                "mo_desc": mo_desc.get(sheet, ""),
                "n_pre": len(pre_rec),
                "n_post": len(post_rec),
                "n_common": len(common_keys),
                "n_new": len(only_post_keys),
                "n_del": len(only_pre_keys),
                "n_params": len(params),
                "n_params_changed": n_params_changed,
                "n_total_changes": n_total_changes,
                "only_pre": ", ".join(only_pre_p[:20]),
                "only_post": ", ".join(only_post_p[:20]),
            }
        )
        log(f"    changed_params={n_params_changed} cell-param diffs={n_total_changes}")
        del pre_rec, post_rec
        gc.collect()

    summary_rows.sort(key=lambda r: (-r["n_changed"], r["mo"], r["pid"]))
    log(f"TOTAL parameters with changes: {len(summary_rows)}")

    # JSON sidecar for reuse
    sidecar = {
        "summary": summary_rows,
        "sheet_stats": sheet_stats,
        "n_new_cells": len(new_cells),
        "n_del_cells": len(del_cells),
        "new_cells": sorted(new_cells),
        "del_cells": sorted(del_cells),
    }
    json_path = OUT_DIR / "2G_Parameter_Change_Data.json"
    json_path.write_text(json.dumps(sidecar), encoding="utf-8")
    log(f"Wrote JSON: {json_path}")

    xlsx_path = OUT_DIR / "2G_Parameter_Change_Summary.xlsx"
    write_xlsx(summary_rows, sheet_stats, new_cells, del_cells, cat, mo_desc, xlsx_path)
    md_path = OUT_DIR / "2G_Parameter_Change_Report.md"
    write_markdown(summary_rows, sheet_stats, new_cells, del_cells, md_path)

    # compact CSV of ranked list
    csv_path = OUT_DIR / "2G_Changed_Parameters_Ranked.csv"
    import csv

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Rank",
                "MO",
                "Parameter ID",
                "Parameter Name",
                "Cells Changed",
                "Pct Common Cells",
                "Common Cells",
                "Distinct Transitions",
                "Top Value Changes",
                "CDR Related",
                "Meaning",
                "Impact on Radio Network Performance",
            ]
        )
        for i, r in enumerate(summary_rows, 1):
            w.writerow(
                [
                    i,
                    r["mo"],
                    r["pid"],
                    r["pname"],
                    r["n_changed"],
                    r["pct"],
                    r["n_common"],
                    r["n_trans"],
                    r["transitions"],
                    "YES" if r["cdr"] else "NO",
                    r["meaning"],
                    r["impact"],
                ]
            )
    log(f"Wrote CSV: {csv_path}")
    log("DONE")


if __name__ == "__main__":
    main()
