from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "student_performance.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
SUBJECT_COLUMNS = ["Math", "Science", "English", "History"]


def load_data(path: Path) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(
                {
                    "Student_ID": row["Student_ID"],
                    "Gender": row["Gender"],
                    "Attendance": float(row["Attendance"]),
                    **{subject: float(row[subject]) for subject in SUBJECT_COLUMNS},
                }
            )
    return rows


def quantile(sorted_values: list[float], q: float) -> float:
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[int(index)]
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * (index - lower)


def box_stats(values: list[float]) -> dict[str, float]:
    sorted_values = sorted(values)
    return {
        "min": sorted_values[0],
        "q1": quantile(sorted_values, 0.25),
        "median": quantile(sorted_values, 0.5),
        "q3": quantile(sorted_values, 0.75),
        "max": sorted_values[-1],
    }


def pearson(x: list[float], y: list[float]) -> float:
    mean_x = mean(x)
    mean_y = mean(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denominator_x = math.sqrt(sum((a - mean_x) ** 2 for a in x))
    denominator_y = math.sqrt(sum((b - mean_y) ** 2 for b in y))
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    return numerator / (denominator_x * denominator_y)


def save_svg(path: Path, width: int, height: int, body: list[str]) -> None:
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="white"/>',
                *body,
                "</svg>",
            ]
        ),
        encoding="utf-8",
    )


def plot_boxplots(rows: list[dict[str, float | str]]) -> None:
    width, height = 900, 520
    margin_left, margin_bottom, margin_top = 90, 70, 60
    plot_width, plot_height = width - 150, height - margin_bottom - margin_top
    y_min, y_max = 30, 100

    def y_scale(v: float) -> float:
        return margin_top + (y_max - v) / (y_max - y_min) * plot_height

    body = [
        '<text x="450" y="30" text-anchor="middle" font-size="22" font-family="Arial">Score Distribution by Subject (Box Plot)</text>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="black"/>',
    ]

    for tick in range(30, 101, 10):
        y = y_scale(tick)
        body.append(f'<line x1="{margin_left - 6}" y1="{y}" x2="{margin_left}" y2="{y}" stroke="black"/>')
        body.append(
            f'<text x="{margin_left - 12}" y="{y + 4}" text-anchor="end" font-size="12" font-family="Arial">{tick}</text>'
        )

    spacing = plot_width / len(SUBJECT_COLUMNS)
    colors = ["#6baed6", "#9ecae1", "#74c476", "#fd8d3c"]

    for idx, subject in enumerate(SUBJECT_COLUMNS):
        values = [float(row[subject]) for row in rows]
        stats = box_stats(values)
        x_center = margin_left + spacing * idx + spacing / 2
        box_width = 80

        y_q1, y_q3 = y_scale(stats["q1"]), y_scale(stats["q3"])
        y_median = y_scale(stats["median"])
        y_min_v = y_scale(stats["min"])
        y_max_v = y_scale(stats["max"])

        body.append(
            f'<line x1="{x_center}" y1="{y_max_v}" x2="{x_center}" y2="{y_q3}" stroke="black"/>'
        )
        body.append(
            f'<line x1="{x_center}" y1="{y_q1}" x2="{x_center}" y2="{y_min_v}" stroke="black"/>'
        )
        body.append(
            f'<rect x="{x_center - box_width/2}" y="{y_q3}" width="{box_width}" height="{max(1, y_q1-y_q3)}" fill="{colors[idx]}" stroke="black"/>'
        )
        body.append(
            f'<line x1="{x_center - box_width/2}" y1="{y_median}" x2="{x_center + box_width/2}" y2="{y_median}" stroke="black" stroke-width="2"/>'
        )
        body.append(
            f'<line x1="{x_center - 20}" y1="{y_max_v}" x2="{x_center + 20}" y2="{y_max_v}" stroke="black"/>'
        )
        body.append(
            f'<line x1="{x_center - 20}" y1="{y_min_v}" x2="{x_center + 20}" y2="{y_min_v}" stroke="black"/>'
        )
        body.append(
            f'<text x="{x_center}" y="{margin_top + plot_height + 30}" text-anchor="middle" font-size="13" font-family="Arial">{subject}</text>'
        )

    save_svg(OUTPUT_DIR / "boxplot_score_distribution.svg", width, height, body)


def plot_correlation_heatmap(rows: list[dict[str, float | str]]) -> None:
    fields = ["Attendance", *SUBJECT_COLUMNS]
    matrix = {
        a: {b: pearson([float(r[a]) for r in rows], [float(r[b]) for r in rows]) for b in fields}
        for a in fields
    }

    width, height = 760, 760
    start_x, start_y, cell = 170, 120, 90
    body = ['<text x="380" y="45" text-anchor="middle" font-size="22" font-family="Arial">Correlation Heatmap</text>']

    for i, row_name in enumerate(fields):
        body.append(
            f'<text x="140" y="{start_y + i * cell + cell/2 + 4}" text-anchor="end" font-size="13" font-family="Arial">{row_name}</text>'
        )
        body.append(
            f'<text x="{start_x + i * cell + cell/2}" y="95" text-anchor="middle" font-size="13" font-family="Arial">{row_name}</text>'
        )
        for j, col_name in enumerate(fields):
            value = matrix[row_name][col_name]
            red = int((1 - value) * 127)
            green = int((1 - abs(value)) * 120 + 80)
            blue = int((1 + value) * 127)
            color = f"rgb({red},{green},{blue})"
            x, y = start_x + j * cell, start_y + i * cell
            body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" stroke="white"/>')
            body.append(
                f'<text x="{x + cell/2}" y="{y + cell/2 + 5}" text-anchor="middle" font-size="13" fill="black" font-family="Arial">{value:.2f}</text>'
            )

    save_svg(OUTPUT_DIR / "correlation_heatmap.svg", width, height, body)


def plot_subject_wise_comparison(rows: list[dict[str, float | str]]) -> None:
    genders = ["Female", "Male"]
    averages = {
        gender: {
            subject: mean([float(r[subject]) for r in rows if r["Gender"] == gender])
            for subject in SUBJECT_COLUMNS
        }
        for gender in genders
    }

    width, height = 900, 520
    margin_left, margin_bottom, margin_top = 90, 80, 60
    plot_width, plot_height = width - 160, height - margin_bottom - margin_top
    y_min, y_max = 40, 100

    def y_scale(v: float) -> float:
        return margin_top + (y_max - v) / (y_max - y_min) * plot_height

    body = [
        '<text x="450" y="30" text-anchor="middle" font-size="22" font-family="Arial">Subject-wise Average Marks by Gender</text>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="black"/>',
    ]

    for tick in range(40, 101, 10):
        y = y_scale(tick)
        body.append(f'<line x1="{margin_left - 6}" y1="{y}" x2="{margin_left}" y2="{y}" stroke="black"/>')
        body.append(
            f'<text x="{margin_left - 12}" y="{y + 4}" text-anchor="end" font-size="12" font-family="Arial">{tick}</text>'
        )

    spacing = plot_width / len(SUBJECT_COLUMNS)
    bar_width = 28
    palette = {"Female": "#5b8ff9", "Male": "#f6bd16"}

    for idx, subject in enumerate(SUBJECT_COLUMNS):
        cluster_x = margin_left + idx * spacing + spacing / 2
        for g_idx, gender in enumerate(genders):
            value = averages[gender][subject]
            x = cluster_x - bar_width - 2 + g_idx * (bar_width + 4)
            y = y_scale(value)
            h = margin_top + plot_height - y
            body.append(
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" fill="{palette[gender]}" opacity="0.9"/>'
            )
            body.append(
                f'<text x="{x + bar_width/2}" y="{y - 6}" text-anchor="middle" font-size="11" font-family="Arial">{value:.1f}</text>'
            )
        body.append(
            f'<text x="{cluster_x}" y="{margin_top + plot_height + 30}" text-anchor="middle" font-size="13" font-family="Arial">{subject}</text>'
        )

    legend_x, legend_y = width - 170, 90
    for i, gender in enumerate(genders):
        y = legend_y + i * 24
        body.append(f'<rect x="{legend_x}" y="{y}" width="14" height="14" fill="{palette[gender]}"/>')
        body.append(
            f'<text x="{legend_x + 22}" y="{y + 12}" font-size="12" font-family="Arial">{gender}</text>'
        )

    save_svg(OUTPUT_DIR / "subject_wise_comparison.svg", width, height, body)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_data(DATA_PATH)
    plot_boxplots(rows)
    plot_correlation_heatmap(rows)
    plot_subject_wise_comparison(rows)
    print(f"Analysis complete. SVG files generated in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
