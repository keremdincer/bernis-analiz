import os
import csv
import constants


def column_indices(data_header):
    print(' > Finding indices...')
    columns = {}
    for index, value in enumerate(data_header):
        for label, column_name in constants.STATIC_COLUMNS.items():
            if value == column_name:
                columns[label] = index
    return columns


def row_props(indices, row, index):
    props = {
        'correct': row[indices['Correct']] == '1',
        'positive': 'pos' in row[indices['Image']],
        'negative': 'neg' in row[indices['Image']],
        'incongruent_start': 'AAT_incon' in row[indices['ExperimentType']],
        'congruent_start': 'AAT_con' in row[indices['ExperimentType']],
        'reverse_rotation': ((index - 1) // 10) % 2 != 0,
        'response_time': row[indices['ResponseTime']]
    }
    column_no = ((index - 1) // 20) + 1
    if props['incongruent_start']:
        if props['reverse_rotation']:
            props['onset_time'] = row[indices['Con_' + str(column_no)]]
            props['inst_onset'] = row[indices['InstCon_' + str(column_no)]]
        else:
            props['onset_time'] = row[indices['Incon_' + str(column_no)]]
            props['inst_onset'] = row[indices['InstIncon_' + str(column_no)]]
    else:
        if props['reverse_rotation']:
            props['onset_time'] = row[indices['Incon_' + str(column_no)]]
            props['inst_onset'] = row[indices['InstIncon_' + str(column_no)]]
        else:
            props['onset_time'] = row[indices['Con_' + str(column_no)]]
            props['inst_onset'] = row[indices['InstCon_' + str(column_no)]]
    return props


def get_max(result):
    max_length = 0
    for value in result.values():
        if len(value) > max_length:
            max_length = len(value)
    return max_length


def plot_results(result):
    print(' > Plotting data...\n')
    print(f'{"":-^189}')
    for label in result.keys():
        print(f'{label:^16}', end=' | ')
    print(f'\n{"":-^189}')

    for index in range(0, get_max(result)):
        for label in result.keys():
            if len(result[label]) > index:
                print(f'{result[label][index]: ^16}', end=' | ')
            else:
                print(f'{".": ^16}', end=' | ')
        print()
    print(f'{"":-^189}\n')


def export_results(filename, result):
    print(' > Exporting file to', filename)
    output = open(filename, 'w+')
    max_length = get_max(result)
    keys = list(result.keys())
    output.write(';'.join(keys) + '\n')

    for i in range(max_length):
        line = []
        for key in keys:
            if i < len(result[key]):
                line.append(str(result[key][i]))
            else:
                line.append('')
        output.write(';'.join(line) + '\n')
    output.close()

def analyze(data):
    print(' > Started analyzing file...')
    result = {
        'Inst Onset': [],
        'Pos Cong Onset': [],
        'Pos Cong Resp': [],
        'Neg Cong Onset': [],
        'Neg Cong Resp': [],
        'Pos Incong Resp': [],
        'Pos Incong Onset': [],
        'Neg Incong Resp': [],
        'Neg Incong Onset': [],
        'Falses': []
    }

    indices = column_indices(data[0])

    resp_time_mri_trig = int(data[1][indices['ResponseTimeMriTrigger']])
    time_mri_trig = int(data[1][indices['TimeMriTrigger']])
    excess = (resp_time_mri_trig + time_mri_trig)

    print(' > Response Time MRI Trigger:', resp_time_mri_trig)
    print(' > Time MRI Trigger:', time_mri_trig)

    # ? Instruction Onset Times
    for y in range(1, len(data) - 1, 10):
        props = row_props(indices, data[y], y)
        result['Inst Onset'].append(
            (int(props['inst_onset']) - (excess)) / 1000)

    # ? Response Time
    for y in range(1, len(data) - 1):
        props = row_props(indices, data[y], y)
        key = ''

        if props['positive']:
            key += 'Pos '
        elif props['negative']:
            key += 'Neg '

        if props['congruent_start']:
            if props['reverse_rotation']:
                key += 'Incong '
            else:
                key += 'Cong '
        elif props['incongruent_start']:
            if props['reverse_rotation']:
                key += 'Cong '
            else:
                key += 'Incong '

        if props['correct']:
            result[key + 'Resp'].append(props['response_time'])
            result[key + 'Onset'].append((int(props['onset_time']) - excess) / 1000)
        else:
            result['Falses'].append((int(props['onset_time']) - excess) / 1000)
    return result


if __name__ == "__main__":
    files = os.listdir(constants.RAW_FOLDER_PATH)
    for file in files:
        print('\n > File Name:', file)
        result = analyze(
            list(csv.reader(open(constants.RAW_FOLDER_PATH + '/' + file))))
        plot_results(result)
        export_results(constants.OUTPUT_FOLDER_PATH + '/' + file, result)
        print(' > Done!\n')
