import sys
import aliss
import os
import csv


# csv fields: game_id(e.g. date), green_points, red_points, green_wins?(0=F, 1=T), red_wins?(0=F, 1=T)
# add relative distances comparing to closest

def main(util_select='r', log_file='log.csv', *bocce_data):
    if util_select == 'w':
        results = aliss.main(*bocce_data)
        write(log_file, results)
    elif util_select == 'r':
        read(log_file)
    elif util_select == 'wr':
        main(log_file, 'w', *bocce_data)
        main(log_file, 'r', *bocce_data)
    else:
        print('Specify function: \'r\' to read data, \'w\' to write, \'wr\' to write then read with new data.')


def write(log_file, game_info):
    is_new = not os.path.exists(log_file)
    log = open(log_file, 'a', newline='')
    writer = csv.writer(log, 'excel')
    if is_new:
        writer.writerow(['Game_id', 'Game_length',
                         'Green_points','Red_points',
                         'Green_avg_dist_inches', 'Red_avg_dist_inches',
                         'Green_wins?', 'Red_wins?'])
    game_id, game_length, dists, points = game_info
    row = [game_id, game_length, *points, *dists]
    if points[0] > points[1]:
        wins = (1, 0)
    elif points[1] > points[0]:
        wins = (0, 1)
    else:
        wins = (1, 1)
    row.append(wins[0])
    row.append(wins[1])
    writer.writerow(row)


def read(log_file):
    if os.path.exists(log_file):
        log = open(log_file, 'r', newline='')
        reader = csv.reader(log, 'excel')
        hist = [row for row in reader]
        total_rounds = 0
        green_points = 0
        red_points = 0
        green_dist = 0
        red_dist = 0
        green_wins = 0
        red_wins = 0
        for game in hist[1:]:
            total_rounds += int(game[1])
            green_points += int(game[2])
            red_points += int(game[3])
            green_dist += int(game[1]) * float(game[4])
            red_dist += int(game[1]) * float(game[5])
            green_wins += int(game[6])
            red_wins += int(game[7])
        green_dist = green_dist/total_rounds
        red_dist = red_dist/total_rounds
        outputs = [total_rounds, green_points, red_points, green_dist, red_dist, green_wins, red_wins]
        output_strings = ['Total rounds played:',
                          'Green career points:', 'Red career points:',
                          'Green mean error:', 'Red mean error:',
                          'Green career wins:', 'Red career wins:']

        print('Reading from:', log_file)
        for i in range(len(output_strings)):
            print(output_strings[i], outputs[i])
    else:
        print(log_file, 'does not exist (defaulted to \'log.csv\' if file was not specified)')


if __name__ == '__main__':
    main(*sys.argv[1:])
