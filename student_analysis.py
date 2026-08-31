"""
===================================================================
 Student Performance Data Analysis
===================================================================
Purpose: Clean, analyze, and visualize student performance data
         using Pandas, NumPy, and Matplotlib.
===================================================================
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "students.csv"
IMAGES_DIR = "images"


def load_and_clean_data(path=CSV_FILE):
    """Load CSV, normalize columns, and clean the data."""
    print("\nLoading dataset...")
    df = pd.read_csv(path)
    original_rows = len(df)

    # 1. Normalize column names (strip whitespace, lowercase, replace spaces/hyphens with _)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    # Rename common variations to standard internal names
    column_mapping = {
        "attendance": "attendance_%",
        "attendance_percentage": "attendance_%",
        "attendance_percent": "attendance_%",
        "hours_studied": "study_hours",
        "study_hour": "study_hours",
        "study_time": "study_hours",
        "math": "math_marks",
        "science": "science_marks",
        "english": "english_marks",
        "computer": "computer_marks",
        "computers": "computer_marks",
        "id": "student_id",
    }
    df = df.rename(columns=column_mapping)

    # Automatically identify subject mark columns
    subject_cols = [c for c in df.columns if c.endswith("_marks")]
    if not subject_cols:
        # Fallback to defaults if column names differ
        subject_cols = [c for c in ["math", "science", "english", "computer"] if c in df.columns]

    # Clean study_hours column if it contains strings (e.g. "5.5 hrs")
    if "study_hours" in df.columns:
        if df["study_hours"].dtype == object:
            df["study_hours"] = (
                df["study_hours"]
                .astype(str)
                .str.extract(r"([\d.]+)", expand=False)
                .astype(float)
            )

    numeric_cols = [c for c in ["attendance_%", "study_hours"] + subject_cols if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Remove duplicate records
    id_col = "student_id" if "student_id" in df.columns else df.columns[0]
    duplicates_found = df.duplicated(subset=[id_col]).sum()
    df = df.drop_duplicates(subset=[id_col], keep="first").reset_index(drop=True)

    # 3. Handle out-of-range values (0 to 100)
    invalid_attendance = 0
    if "attendance_%" in df.columns:
        invalid_mask = (df["attendance_%"] < 0) | (df["attendance_%"] > 100)
        invalid_attendance = invalid_mask.sum()
        df.loc[invalid_mask, "attendance_%"] = np.nan

    invalid_marks_total = 0
    for subj in subject_cols:
        invalid_mask = (df[subj] < 0) | (df[subj] > 100)
        invalid_marks_total += invalid_mask.sum()
        df.loc[invalid_mask, subj] = np.nan

    # 4. Handle missing values
    missing_before = df.isnull().sum().sum()
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(round(median_val, 1))

    # 5. Neatly format numeric values
    if "attendance_%" in df.columns:
        df["attendance_%"] = df["attendance_%"].round(1)
    if "study_hours" in df.columns:
        df["study_hours"] = df["study_hours"].round(1)
    for subj in subject_cols:
        df[subj] = df[subj].round(0)

    # 6. Calculated fields
    df["total_marks"] = df[subject_cols].sum(axis=1)
    df["average_marks"] = df[subject_cols].mean(axis=1).round(2)
    df["grade"] = df["average_marks"].apply(assign_grade)

    print("Data cleaning complete.")
    print(f"   • Rows loaded originally     : {original_rows}")
    print(f"   • Duplicate rows removed     : {duplicates_found}")
    print(f"   • Out-of-range values fixed  : {invalid_attendance + invalid_marks_total}")
    print(f"   • Missing values found       : {missing_before} (filled using column median)")
    print(f"   • Final clean row count      : {len(df)}\n")

    return df, subject_cols


def assign_grade(avg):
    if avg >= 90:
        return "A+"
    elif avg >= 80:
        return "A"
    elif avg >= 70:
        return "B"
    elif avg >= 60:
        return "C"
    elif avg >= 50:
        return "D"
    return "F"


def show_all_students(df):
    print("\n===== ALL STUDENTS =====")
    cols = [c for c in ["student_id", "name", "gender", "attendance_%", "study_hours", "total_marks", "average_marks", "grade"] if c in df.columns]
    print(df[cols].to_string(index=False))


def show_class_statistics(df):
    print("\n===== CLASS STATISTICS =====")
    print(f"Number of students     : {len(df)}")
    print(f"Class average marks    : {df['average_marks'].mean():.2f}")
    print(f"Class average (%)      : {df['average_marks'].mean():.2f}%")

    top = df.loc[df["average_marks"].idxmax()]
    low = df.loc[df["average_marks"].idxmin()]

    name_col = "name" if "name" in df.columns else df.columns[0]
    id_col = "student_id" if "student_id" in df.columns else df.columns[0]

    print(f"\nHighest scorer  : {top[name_col]} ({top[id_col]}) - Average: {top['average_marks']:.2f}, Total: {top['total_marks']:.0f}")
    print(f"Lowest scorer   : {low[name_col]} ({low[id_col]}) - Average: {low['average_marks']:.2f}, Total: {low['total_marks']:.0f}")

    if "attendance_%" in df.columns:
        print(f"\nAverage attendance : {df['attendance_%'].mean():.2f}%")
    if "study_hours" in df.columns:
        print(f"Average study hours: {df['study_hours'].mean():.2f} hrs/day")


def show_top_students(df, n=5):
    print(f"\n===== TOP {n} STUDENTS =====")
    top_n = df.sort_values("average_marks", ascending=False).head(n)
    cols = [c for c in ["student_id", "name", "total_marks", "average_marks", "grade"] if c in df.columns]
    print(top_n[cols].to_string(index=False))


def subject_wise_analysis(df, subjects):
    print("\n===== SUBJECT-WISE ANALYSIS =====")
    subject_avg = df[subjects].mean().round(2)
    subject_max = df[subjects].max()
    subject_min = df[subjects].min()

    summary = pd.DataFrame({
        "Average": subject_avg,
        "Highest": subject_max,
        "Lowest": subject_min
    })
    print(summary.to_string())

    best_subject = subject_avg.idxmax()
    worst_subject = subject_avg.idxmin()
    print(f"\nBest performing subject overall : {best_subject} ({subject_avg.max():.2f} avg)")
    print(f"Weakest performing subject      : {worst_subject} ({subject_avg.min():.2f} avg)")


def students_needing_improvement(df, threshold=50):
    print(f"\n===== STUDENTS NEEDING IMPROVEMENT (Average < {threshold}) =====")
    weak = df[df["average_marks"] < threshold].sort_values("average_marks")
    if weak.empty:
        print("Great news! No students are below the threshold.")
    else:
        cols = [c for c in ["student_id", "name", "average_marks", "grade"] if c in df.columns]
        print(weak[cols].to_string(index=False))


def analyze_attendance(df):
    if "attendance_%" not in df.columns:
        print("\nAttendance column not found.")
        return
    print("\n===== ATTENDANCE ANALYSIS =====")
    print(f"Average attendance : {df['attendance_%'].mean():.2f}%")
    print(f"Highest attendance : {df['attendance_%'].max():.2f}%")
    print(f"Lowest attendance  : {df['attendance_%'].min():.2f}%")

    correlation = df["attendance_%"].corr(df["average_marks"])
    print(f"\nCorrelation between Attendance and Average Marks: {correlation:.2f}")
    interpret_correlation(correlation, "attendance", "marks")

    low_attendance = df[df["attendance_%"] < 75]
    print(f"\nStudents with attendance below 75%: {len(low_attendance)}")
    if not low_attendance.empty:
        cols = [c for c in ["student_id", "name", "attendance_%"] if c in df.columns]
        print(low_attendance[cols].to_string(index=False))


def analyze_study_hours(df):
    if "study_hours" not in df.columns:
        print("\nStudy hours column not found.")
        return
    print("\n===== STUDY HOURS ANALYSIS =====")
    print(f"Average study hours : {df['study_hours'].mean():.2f} hrs/day")
    print(f"Maximum study hours : {df['study_hours'].max():.2f} hrs/day")
    print(f"Minimum study hours : {df['study_hours'].min():.2f} hrs/day")

    correlation = df["study_hours"].corr(df["average_marks"])
    print(f"\nCorrelation between Study Hours and Average Marks: {correlation:.2f}")
    interpret_correlation(correlation, "study hours", "marks")


def interpret_correlation(corr, var1, var2):
    strength = "weak"
    if abs(corr) >= 0.7:
        strength = "strong"
    elif abs(corr) >= 0.4:
        strength = "moderate"

    direction = "positive" if corr >= 0 else "negative"
    print(f"This indicates a {strength} {direction} relationship between {var1} and {var2}.")


def display_graphs(df, subjects, save_combined=True):
    os.makedirs(IMAGES_DIR, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle("Student Performance Analysis - Dashboard", fontsize=16, fontweight="bold")

    # 1. Subject-wise average marks
    subject_avg = df[subjects].mean()
    axes[0, 0].bar(
        [s.replace("_marks", "").capitalize() for s in subjects],
        subject_avg.values,
        color=["#4C72B0", "#55A868", "#C44E52", "#8172B2"][:len(subjects)]
    )
    axes[0, 0].set_title("Subject-wise Average Marks")
    axes[0, 0].set_ylabel("Average Marks")
    axes[0, 0].set_ylim(0, 100)
    for i, v in enumerate(subject_avg.values):
        axes[0, 0].text(i, v + 1, f"{v:.1f}", ha="center")

    # 2. Marks distribution
    axes[0, 1].hist(df["average_marks"], bins=10, color="#4C72B0", edgecolor="black")
    axes[0, 1].set_title("Distribution of Average Marks")
    axes[0, 1].set_xlabel("Average Marks")
    axes[0, 1].set_ylabel("Number of Students")

    # 3. Attendance vs marks
    if "attendance_%" in df.columns:
        axes[1, 0].scatter(df["attendance_%"], df["average_marks"], color="#C44E52", alpha=0.7)
        axes[1, 0].set_title("Attendance % vs Average Marks")
        axes[1, 0].set_xlabel("Attendance %")
        axes[1, 0].set_ylabel("Average Marks")
        z = np.polyfit(df["attendance_%"], df["average_marks"], 1)
        trend = np.poly1d(z)
        xs = np.linspace(df["attendance_%"].min(), df["attendance_%"].max(), 50)
        axes[1, 0].plot(xs, trend(xs), "k--", linewidth=1)

    # 4. Study hours vs marks
    if "study_hours" in df.columns:
        axes[1, 1].scatter(df["study_hours"], df["average_marks"], color="#55A868", alpha=0.7)
        axes[1, 1].set_title("Study Hours vs Average Marks")
        axes[1, 1].set_xlabel("Study Hours per day")
        axes[1, 1].set_ylabel("Average Marks")
        z2 = np.polyfit(df["study_hours"], df["average_marks"], 1)
        trend2 = np.poly1d(z2)
        xs2 = np.linspace(df["study_hours"].min(), df["study_hours"].max(), 50)
        axes[1, 1].plot(xs2, trend2(xs2), "k--", linewidth=1)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_combined:
        out_path = os.path.join(IMAGES_DIR, "charts.png")
        plt.savefig(out_path, dpi=150)
        print(f"\nCharts saved to '{out_path}'")

    plt.show()
    plt.close(fig)


def print_menu():
    print("\n===== STUDENT PERFORMANCE ANALYSIS =====")
    print("1. Show all students")
    print("2. Show class statistics")
    print("3. Show top students")
    print("4. Subject-wise analysis")
    print("5. Find students needing improvement")
    print("6. Analyze attendance")
    print("7. Analyze study hours")
    print("8. Display graphs")
    print("9. Exit")


def main():
    df, subjects = load_and_clean_data(CSV_FILE)

    while True:
        print_menu()
        choice = input("Enter your choice (1-9): ").strip()

        if choice == "1":
            show_all_students(df)
        elif choice == "2":
            show_class_statistics(df)
        elif choice == "3":
            try:
                n = int(input("How many top students to show? (default 5): ") or 5)
            except ValueError:
                n = 5
            show_top_students(df, n)
        elif choice == "4":
            subject_wise_analysis(df, subjects)
        elif choice == "5":
            try:
                threshold = float(input("Enter the improvement threshold (default 50): ") or 50)
            except ValueError:
                threshold = 50
            students_needing_improvement(df, threshold)
        elif choice == "6":
            analyze_attendance(df)
        elif choice == "7":
            analyze_study_hours(df)
        elif choice == "8":
            display_graphs(df, subjects)
        elif choice == "9":
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()