# Student Performance Analysis (Python)

This project analyzes student performance using marks, attendance, gender, and subjects.

## Dataset

`data/student_performance.csv` includes:
- `Student_ID`
- `Gender`
- `Attendance`
- Subject marks: `Math`, `Science`, `English`, `History`

## Visualizations generated

1. **Box plots for score distribution**
2. **Correlation heatmap**
3. **Subject-wise comparison (average marks by gender)**

All charts are saved in the `outputs/` folder.

## Run the project

```bash
cd student_performance_analysis
python3 analyze_student_performance.py
```

Generated files:
- `outputs/boxplot_score_distribution.svg`
- `outputs/correlation_heatmap.svg`
- `outputs/subject_wise_comparison.svg`
