import csv


class CsvWriter:
    @staticmethod
    def write(data_with_columns, file_path):
        with open(file_path, "w") as f:
            csv_writer = csv.writer(f, delimiter=",", quotechar='"')
            csv_writer.writerow(data_with_columns.columns)
            for row in data_with_columns.data:
                csv_writer.writerow([row[c] for c in data_with_columns.columns])
