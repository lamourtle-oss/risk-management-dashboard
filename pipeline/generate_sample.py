"""Create a sample Excel workbook matching the dashboard Word spec."""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample-data"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

QUARTERS = ["Q4/2567", "Q1/2568", "Q2/2568", "Q3/2568"]
NPL_TYPES = ["HP Home appliance", "HP Commercial"]
STAGES = ["Stage 1", "Stage 2", "Stage 3"]
LOAN_TYPES = ["HP Home appliance", "HP Commercial", "สินเชื่อเช่าซื้ออื่น"]
BRANCHES = [
    ("สาขาสยาม", "กรุงเทพมหานคร"),
    ("สาขารังสิต", "ปทุมธานี"),
    ("สาขาชลบุรี", "ชลบุรี"),
    ("สาขาระยอง", "ระยอง"),
    ("สาขานครราชสีมา", "นครราชสีมา"),
    ("สาขาขอนแก่น", "ขอนแก่น"),
    ("สาขาอุดรธานี", "อุดรธานี"),
    ("สาขาเชียงใหม่", "เชียงใหม่"),
    ("สาขาหาดใหญ่", "สงขลา"),
    ("สาขาสุราษฎร์", "สุราษฎร์ธานี"),
]
PRODUCTS = ["ตู้เย็น", "เครื่องซักผ้า", "แอร์", "ทีวี", "พัดลม", "เตาแก๊ส"]
HEADER_FILL = PatternFill("solid", fgColor="1E3A5F")
HEADER_FONT = Font(color="FFFDF8", bold=True, name="Tahoma", size=11)


def _sheet(wb: Workbook, title: str, headers: list[str], rows: list[tuple]) -> None:
    ws = wb.create_sheet(title)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(1, col, header)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
    for r_idx, row in enumerate(rows, 2):
        for c_idx, value in enumerate(row, 1):
            ws.cell(r_idx, c_idx, value)
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 22
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"
    ws.freeze_panes = "A2"


def build_workbook() -> Workbook:
    wb = Workbook()
    default = wb.active
    wb.remove(default)

    overview = []
    for quarter in QUARTERS:
        overview.append((quarter, "HP Home appliance", 4.8 if "2567" in quarter else 3.9, 42_500_000))
        overview.append((quarter, "HP Commercial", 6.1 if "2567" in quarter else 5.4, 18_200_000))
    _sheet(wb, "NPL ภาพรวม", ["ไตรมาส", "ประเภท NPL", "สัดส่วน NPL (%)", "มูลค่า NPL"], overview)

    stages = []
    for quarter in QUARTERS:
        for npl_type in NPL_TYPES:
            stages.append((quarter, npl_type, "Stage 1", 820, 12_000_000))
            stages.append((quarter, npl_type, "Stage 2", 210, 7_400_000))
            stages.append((quarter, npl_type, "Stage 3", 95 if npl_type.startswith("HP Home") else 140, 9_800_000))
    _sheet(
        wb,
        "NPL Stage",
        ["ไตรมาส", "ประเภท NPL", "Stage", "จำนวนสัญญา", "มูลค่า"],
        stages,
    )

    closures = []
    for quarter in QUARTERS:
        for loan in LOAN_TYPES:
            closures.append((quarter, loan, 12, 2_100_000, 8, 1_450_000, 64, 9_800_000))
    _sheet(
        wb,
        "NPL ปิดสัญญา",
        [
            "ไตรมาส",
            "ประเภทสินเชื่อ",
            "จำนวน Writeoff",
            "มูลค่า Writeoff",
            "จำนวนยึดหลักประกัน",
            "มูลค่ายึดหลักประกัน",
            "จำนวนปิดปกติ",
            "มูลค่าปิดปกติ",
        ],
        closures,
    )

    hp_home = []
    for month, ratio, amount in [
        ("ม.ค. 2568", 2.1, 3_200_000),
        ("ก.พ. 2568", 2.4, 3_450_000),
        ("มี.ค. 2568", 2.8, 3_900_000),
        ("เม.ย. 2568", 3.1, 4_150_000),
        ("พ.ค. 2568", 3.0, 4_020_000),
        ("มิ.ย. 2568", 2.7, 3_780_000),
        ("ก.ค. 2568", 2.9, 3_960_000),
        ("ส.ค. 2568", 3.2, 4_280_000),
    ]:
        hp_home.append((month, ratio, amount, "สัญญาเกิดใหม่ตั้งแต่ ม.ค. 2568"))
    _sheet(
        wb,
        "NPL HP Home 2568",
        ["เดือน", "สัดส่วน NPL (%)", "มูลค่า NPL", "หมายเหตุ"],
        hp_home,
    )

    mix = []
    for quarter in QUARTERS:
        mix.append((quarter, "ตู้เย็น", 28_000_000))
        mix.append((quarter, "แอร์", 24_500_000))
        mix.append((quarter, "เครื่องซักผ้า", 18_200_000))
        mix.append((quarter, "ทีวี", 15_400_000))
        mix.append((quarter, "พัดลม", 6_800_000))
        mix.append((quarter, "เตาแก๊ส", 4_100_000))
        mix.append((quarter, "น้ำมัน", 11_000_000))
    _sheet(wb, "ยอดขายสัดส่วน", ["ไตรมาส", "ประเภทสินค้า", "ยอดขาย"], mix)

    branch_rows = []
    product_rows = []
    for quarter in QUARTERS:
        for i, (branch, province) in enumerate(BRANCHES):
            base = 4_800_000 - i * 280_000
            if "2567" in quarter:
                base *= 0.92
            branch_rows.append((quarter, branch, province, int(base)))
            for j, product in enumerate(PRODUCTS):
                amount = int(base * (0.28, 0.22, 0.2, 0.16, 0.09, 0.05)[j] * (1.15 - (i % 4) * 0.08))
                product_rows.append((quarter, branch, province, product, amount))
    _sheet(wb, "ยอดขายสาขา", ["ไตรมาส", "สาขา", "จังหวัด", "ยอดขาย"], branch_rows)
    _sheet(
        wb,
        "ยอดขายสินค้า",
        ["ไตรมาส", "สาขา", "จังหวัด", "สินค้า", "ยอดขาย"],
        product_rows,
    )

    aging = []
    locations = ["คลังพระราม 2", "คลังบางนา", "คลังโคราช", "คลังเชียงใหม่", "คลังหาดใหญ่"]
    for i, product in enumerate(["ตู้เย็น 2 ประตู", "แอร์ 12000 BTU", "เครื่องซักผ้า 10kg", "ทีวี 55 นิ้ว", "พัดลมตั้งพื้น", "เตาแก๊ส 2 หัว", "ตู้เย็นมือสอง", "แอร์มือสอง"]):
        grade = "มือ 2" if "มือสอง" in product else "มือ 1"
        aging.append(
            (
                product,
                grade,
                1_250_000 - i * 80_000,
                95_000 + i * 12_000,
                40 - i,
                12 + i,
                max(2, i - 1),
                locations[i % len(locations)],
                BRANCHES[i % len(BRANCHES)][0],
                BRANCHES[i % len(BRANCHES)][1],
            )
        )
    _sheet(
        wb,
        "Aging สินค้า",
        ["สินค้า", "สภาพ", "Cost", "Provision", "0-2 ปี", "3-4 ปี", "4 ปีขึ้นไป", "Location", "สาขา", "จังหวัด"],
        aging,
    )

    minmax = []
    for i, (branch, province) in enumerate(BRANCHES):
        minmax.append((branch, province, 80 + i * 4, 420 - i * 10, 190 + i * 8))
    _sheet(wb, "MinMax Stock", ["สาขา", "จังหวัด", "Min stock", "Max stock", "คงเหลือ"], minmax)

    oil = []
    liters_cycle = [32, 68, 120, 175, 240, 48, 90, 155, 210, 18]
    for quarter in QUARTERS:
        for i, (branch, province) in enumerate(BRANCHES):
            liters = liters_cycle[i] + (15 if "2568" in quarter else 0)
            oil.append((quarter, branch, province, liters))
    _sheet(wb, "น้ำมัน", ["ไตรมาส", "สาขา", "จังหวัด", "ปริมาณลิตร"], oil)

    sla_rows = []
    buckets = ["0-7 วัน", "7-15 วัน", "15-30 วัน", "30-60 วัน", "60-90 วัน", "มากกว่า 90 วัน"]
    for quarter in QUARTERS:
        counts = [180, 42, 18, 9, 4, 2]
        if "2567" in quarter:
            counts = [150, 55, 24, 12, 6, 3]
        for bucket, count in zip(buckets, counts, strict=True):
            sla_rows.append((quarter, bucket, count))
    _sheet(wb, "SLA ซ่อม", ["ไตรมาส", "ระยะเวลาซ่อม", "จำนวนงาน"], sla_rows)

    province_sla = []
    for quarter in QUARTERS:
        for i, (branch, province) in enumerate(BRANCHES):
            met = 70 - i * 3
            miss = 8 + (i % 4) * 2
            if i in {3, 6, 9}:
                miss += 12
            province_sla.append((quarter, province, branch, met + miss, met, miss))
    _sheet(
        wb,
        "SLA จังหวัด",
        ["ไตรมาส", "จังหวัด", "สาขา", "งานทั้งหมด", "ตาม SLA", "ไม่ตาม SLA"],
        province_sla,
    )

    csat = [(quarter, 4.4 + (0.1 if "2568" in quarter else 0) - i * 0.05) for i, quarter in enumerate(QUARTERS)]
    _sheet(wb, "CSAT ซ่อม", ["ไตรมาส", "คะแนนความพึงพอใจ"], csat)
    return wb


def main() -> None:
    SAMPLE.mkdir(parents=True, exist_ok=True)
    path = SAMPLE / "dashboard-spec.xlsx"
    build_workbook().save(path)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
