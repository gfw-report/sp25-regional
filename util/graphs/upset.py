import matplotlib.pyplot as plt
import pandas as pd
from upsetplot import generate_counts, plot
import argparse


def read_files_and_prepare_data(file_path_1, file_path_2):
    data_1 = pd.read_csv(file_path_1)
    data_2 = pd.read_csv(file_path_2)
    combined_data = pd.concat([data_1, data_2])

    combined_data.set_index(['url', 'category'], inplace=True)

    binary_data = pd.DataFrame(index=pd.MultiIndex.from_product([combined_data.index.get_level_values('url').unique(), 
                                                                combined_data.index.get_level_values('category').unique()],
                                                                names=['url', 'category']))

    binary_data['present'] = 0
    binary_data.loc[combined_data.index, 'present'] = 1

    binary_matrix = binary_data.unstack('category')['present'].fillna(0).astype(int)

    formatted_matrix = binary_matrix.replace({1: True, 0: False})

    formatted_counts = formatted_matrix.groupby(list(formatted_matrix.columns)).size()

    return formatted_counts


def main():
    parser = argparse.ArgumentParser(
        description='Process two files to prepare data for an upset plot.')

    parser.add_argument('file_path_1',
                        metavar='file1',
                        type=str,
                        help='the path to the first input file')

    parser.add_argument('file_path_2',
                        metavar='file2',
                        type=str,
                        help='the path to the second input file')

    # Execute the parse_args() method
    args = parser.parse_args()

    result = read_files_and_prepare_data(args.file_path_1, args.file_path_2)
    print(result)

    plot(result, show_counts='{:d}')
    plt.show()



if __name__ == "__main__":
    main()