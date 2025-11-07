"""从 CSV 读取剖面数据，调用 NRLMSIS2 批量计算并保存结果到 CSV。

行为：
- 从 `data/ERA5_T_20120101.csv` 读取：包含 valid_time, model_level, latitude, longitude, t
- 使用 `data/137层气压_高度对应关系.txt` 将 model_level 映射为海拔高度（米 -> km）
- 批量调用 `model.pymsis2.NRLMSIS2.calc_many` 获得 T_local, T_exo, dn10
- 将输出追加到 `results/ERA5_T_20120101_msis.csv`

注意：脚本仅使用标准库，按块处理以控制内存；若未找到 MSIS DLL，会抛出并提示。
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
INPUT_CSV = DATA_DIR / "ERA5_T_20120101.csv"
LEVEL_MAP = DATA_DIR / "137层气压_高度对应关系.txt"
OUTPUT_CSV = RESULTS_DIR / (INPUT_CSV.stem + "_msis.csv")


def load_level_map(path: Path) -> Dict[int, float]:
	"""读取分层映射文件，返回 level -> height_km 映射。
	文件中高度以米为单位，需要转换为千米。
	"""
	mapping: Dict[int, float] = {}
	with path.open("r", encoding="utf-8") as fh:
		# 文件是以制表符/空格分隔，第一行为标题
		reader = csv.DictReader(fh, delimiter='\t')
		# 若分隔符不正确，fallback 用逗号分割
		if reader.fieldnames is None or 'Level' not in reader.fieldnames:
			fh.seek(0)
			reader = csv.DictReader(fh)
		for row in reader:
			try:
				lvl = int(float(row.get('Level') or row.get('level') or row.get('Level\r') or 0))
				h_m = float(row.get('heigh_m') or row.get('heigh_m\r') or row.get('heigh_m ') or row.get('heigh_m') or row.get('heigh_m'))
				mapping[lvl] = h_m / 1000.0
			except Exception:
				# 忽略无法解析的行
				continue
	return mapping


def parse_valid_time(s: str) -> datetime:
	# 输入示例：2012-01-01 00:00:00
	return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")


def main(chunk_size: int = 1000, f107a: float = 150.0, f107: float = 150.0):
	# 保证路径
	RESULTS_DIR.mkdir(parents=True, exist_ok=True)

	# 将项目根加入 sys.path，以便导入 model.pymsis2
	root_parent = Path(__file__).resolve().parent
	if str(root_parent) not in sys.path:
		sys.path.insert(0, str(root_parent))

	try:
		from model.pymsis2 import NRLMSIS2, doy, seconds_of_day
	except Exception as e:
		raise RuntimeError("无法导入 model.pymsis2，请确认 DLL 已编译并且 Python 路径正确: " + str(e))

	level_map = load_level_map(LEVEL_MAP)
	if not level_map:
		print("警告：未加载到 level->height 映射，请检查", LEVEL_MAP)

	msis = NRLMSIS2()  # 使用默认 DLL 路径与单精度

	with INPUT_CSV.open("r", encoding="utf-8") as infh, OUTPUT_CSV.open("w", encoding="utf-8", newline='') as outfh:
		reader = csv.DictReader(infh)
		fieldnames = list(reader.fieldnames or [])
		# 新增输出字段
		extra = ["alt_km", "T_local_K", "T_exo_K"] + [f"dn10_{i}" for i in range(10)]
		writer = csv.DictWriter(outfh, fieldnames=fieldnames + extra)
		writer.writeheader()

		batch_rows: List[Dict[str, str]] = []
		batch_day = []
		batch_utsec = []
		batch_alt = []
		batch_lat = []
		batch_lon = []

		def flush_batch():
			if not batch_rows:
				return
			# 调用 msis
			try:
				results = msis.calc_many(
					day=batch_day,
					utsec=batch_utsec,
					alt_km=batch_alt,
					lat_deg=batch_lat,
					lon_deg=batch_lon,
					f107a=[f107a],
					f107=[f107],
					ap7=None,
					out_numpy=False,
				)
			except Exception as e:
				raise RuntimeError("调用 msis.calc_many 失败: " + str(e))

			for row, res in zip(batch_rows, results):
				out = dict(row)
				out["alt_km"] = f"{res.alt_km:.6f}"
				out["T_local_K"] = f"{res.T_local_K:.6f}"
				out["T_exo_K"] = f"{res.T_exo_K:.6f}"
				for i, v in enumerate(res.dn10):
					out[f"dn10_{i}"] = f"{v:.6e}"
				writer.writerow(out)

			# 清空批次
			batch_rows.clear()
			batch_day.clear()
			batch_utsec.clear()
			batch_alt.clear()
			batch_lat.clear()
			batch_lon.clear()

		# 逐行读取
		for i, row in enumerate(reader, start=1):
			try:
				vt = parse_valid_time(row["valid_time"]) if row.get("valid_time") else None
				if vt is None:
					raise ValueError("valid_time 为空")
				day = doy(vt.year, vt.month, vt.day)
				utsec = seconds_of_day(vt.hour, vt.minute, vt.second)

				lvl_raw = row.get("model_level")
				lvl = int(float(lvl_raw)) if lvl_raw is not None and lvl_raw != "" else None
				alt_km: Optional[float]
				if lvl is None:
					alt_km = None
				else:
					alt_km = level_map.get(lvl)
				if alt_km is None:
					# 若找不到映射，设为 0 km 并记录
					alt_km = 0.0

				lat = float(row.get("latitude") or 0.0)
				lon = float(row.get("longitude") or 0.0)

			except Exception as e:
				# 无法解析此行，跳过并打印日志
				print(f"跳过第 {i} 行：解析失败: {e}")
				continue

			batch_rows.append(row)
			batch_day.append(day)
			batch_utsec.append(utsec)
			batch_alt.append(alt_km)
			batch_lat.append(lat)
			batch_lon.append(lon)

			if len(batch_rows) >= chunk_size:
				flush_batch()

		# 刷新剩余
		flush_batch()

	print(f"完成：输出写入 {OUTPUT_CSV}")


if __name__ == "__main__":
	import argparse

	p = argparse.ArgumentParser(description="Run MSIS on ERA5 CSV and save results")
	p.add_argument("--chunk-size", type=int, default=1000, help="批量大小（默认 1000）")
	p.add_argument("--f107", type=float, default=150.0, help="f107 值，默认 150.0")
	p.add_argument("--f107a", type=float, default=150.0, help="f107a 值，默认 150.0")
	p.add_argument("--input", type=str, default=str(INPUT_CSV), help="输入 CSV 路径")
	p.add_argument("--output", type=str, default=str(OUTPUT_CSV), help="输出 CSV 路径")
	p.add_argument("--level-map", type=str, default=str(LEVEL_MAP), help="level->height 映射文件路径")

	args = p.parse_args()

	# 允许通过命令行覆盖模块级常量
	INPUT = Path(args.input)
	OUTPUT = Path(args.output)
	LEVEL = Path(args.level_map)

	# 覆盖模块常量（简单处理）
	INPUT_CSV = INPUT
	OUTPUT_CSV = OUTPUT
	LEVEL_MAP = LEVEL

	try:
		main(chunk_size=args.chunk_size, f107a=args.f107a, f107=args.f107)
	except Exception as e:
		print("运行失败:", e)
		raise
