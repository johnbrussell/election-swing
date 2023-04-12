import csv
from collections import namedtuple

dataWithColumns = namedtuple('dataWithColumns', ['data', 'columns'])


class CsvReader:
    def read(self, file_path, delimiter=','):
        with open(file_path) as f:
            csv_reader = csv.reader(f, delimiter=delimiter)
            column_row = next(csv_reader)
            input_column_indices, output_column_indices = self._create_csv_column_dict(column_row)
            data = self._read_in_data(csv_reader, input_column_indices, output_column_indices)
        return data

    @staticmethod
    def _create_csv_column_dict(column_row):
        # Takes the first row of a CSV file (ie., the columns).  Returns dict(column_name: index_in_row).
        input_column_index = 0
        output_column_index = 0
        input_column_indices = dict()
        output_column_indices = dict()
        for name in column_row:
            if name:
                input_column_indices[name] = input_column_index
                output_column_indices[name] = output_column_index
                output_column_index += 1
            input_column_index += 1
        return input_column_indices, output_column_indices

    @staticmethod
    def _read_in_data(csv_reader, input_column_indices, output_column_indices):
        columns = input_column_indices
        data_structure = namedtuple('CsvData', [str(k) for k in columns.keys() if str(k)])
        return dataWithColumns([data_structure(**{col: line[columns[col]] for col in columns.keys() if col})
                                for line in csv_reader], output_column_indices)
