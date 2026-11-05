import csv
from pathlib import Path
from datetime import datetime

# 1. File paths
folder = Path(__file__).resolve().parent.parent / "data" / "raw"

source = folder / "olist_order_reviews_dataset.csv"
target = folder / "olist_order_reviews_cleaned.csv"

expected_columns = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
]

# 2. Counters
total_rows = 0
fixed_line_breaks = 0
long_comments = 0
long_titles = 0
invalid_dates = 0
invalid_scores = 0

# 3. Read original CSV
with source.open(
    "r", encoding="utf-8-sig", newline=""
) as infile:

    reader = csv.reader(
        infile,
        delimiter=",",
        quotechar='"',
        doublequote=True,
        strict=True
    )

    header = next(reader)

    if header != expected_columns:
        raise ValueError(
            f"Unexpected CSV columns: {header}"
        )

    # 4. Create cleaned CSV
    with target.open(
        "w", encoding="utf-8", newline=""
    ) as outfile:

        writer = csv.writer(
            outfile,
            delimiter=",",
            quotechar='"',
            escapechar="\\",
            doublequote=False,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n"
        )

        writer.writerow(header)

        for row in reader:
            total_rows += 1

            # Check column count
            if len(row) != 7:
                raise ValueError(
                    f"Row {total_rows}: "
                    f"expected 7 columns, got {len(row)}"
                )

            # Remove embedded line breaks in comments
            for col in [3, 4]:
                original = row[col]

                cleaned = (
                    original
                    .replace("\r\n", " ")
                    .replace("\n", " ")
                    .replace("\r", " ")
                    .replace("\x00", "")
                )

                if cleaned != original:
                    fixed_line_breaks += 1

                row[col] = cleaned

            # Check long text fields
            if len(row[3]) > 50:
                long_titles += 1

            if len(row[4]) > 256:
                long_comments += 1

            # Validate review score
            try:
                score = int(row[2])
                if score not in range(1, 6):
                    invalid_scores += 1
            except ValueError:
                invalid_scores += 1

            # Validate timestamps
            for col in [5, 6]:
                try:
                    datetime.strptime(
                        row[col], "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError:
                    invalid_dates += 1

            writer.writerow(row)

print("\n=== CLEANING REPORT ===")
print("Total reviews:", total_rows)
print("Fixed text fields:", fixed_line_breaks)
print("Titles longer than 50:", long_titles)
print("Comments longer than 256:", long_comments)
print("Invalid scores:", invalid_scores)
print("Invalid dates:", invalid_dates)
print("Output file:", target)

if total_rows == 99224:
    print("SUCCESS: Expected record count matched!")
else:
    print("WARNING: Record count differs from expected!")
