import sys
import os
import cv2 as cv
import numpy as np
import statistics
import math

# jack diameter: 53px = 1.5in
# play ball diameter: 124px = 3.5in
# player iterables follow convention green=0, red=1


def main(*dirs):
    # handle various cases of specified input and output directories
    if len(dirs) == 0: f = ('input', 'output')
    elif len(dirs) == 1: f = (str(dirs[0]), str(dirs[0])+'_output')
    else: f = (str(dirs[0]), str(dirs[1]))
    # read input filenames and prepare output files
    ins, outs = get_filenames(f[0], f[1])
    files = zip(ins, outs)
    # track average distances/errors for each round (only used in companion BLOSSOM logging system)
    green_dists = []
    red_dists = []
    # track scores for each round
    round_scores = []
    for pair in files:
        # calculate scores and generate output images for each round
        results = round_analysis(pair[0], pair[1])
        green_dists.append(results[0][0])
        red_dists.append(results[0][1])
        round_scores.append(results[1])
    # mean distances
    dists = (px_to_in(statistics.mean(green_dists)), px_to_in(statistics.mean(red_dists)))
    # aggregate scores into final score
    points = [0, 0]
    for s in round_scores:
        points[s[0]] += s[1]
    # print final scores
    print('Green:', points[0])
    print('Red:', points[1])
    return f[0], len(ins), dists, points


def get_filenames(input_dir, output_dir):
    input_list = os.listdir(input_dir)
    input_files = []
    output_files = []
    try: os.mkdir(output_dir)
    except FileExistsError: pass
    for name in input_list:
        if name.lower().endswith('.jpg'):
            input_files.append(input_dir + '/' + name)
            output_files.append(output_dir + '/' + name[:-4] + '_output.jpg')
    return input_files, output_files


def round_analysis(round_image, output_file):
    # calculate score and generate output image for a round
    # ingest images
    image = cv.imread(round_image)
    jack, green, red = cv.imread('jack.jpg'), cv.imread('green.jpg'), cv.imread('red.jpg')
    # calculate best relative scale of templates to round_image and rescale templates
    scale = find_scale(image.copy(), (jack, green, red), 20)
    jack, green, red = rescale(jack, scale), rescale(green, scale), rescale(red, scale)
    # find each ball in the round_image and get distances
    jack_center = jack_id(image, jack)
    green_dist = ball_id(image, jack_center, green)
    red_dist = ball_id(image, jack_center, red)
    # calculate and return score of the round
    accuracy = (statistics.mean(green_dist), statistics.mean(red_dist))
    scores = score(green_dist, red_dist)
    score_gui(image, scores)
    cv.imwrite(output_file, image)
    return accuracy, scores


def find_scale(image, templates, speed_factor=1):
    # rescale images for linearly faster operation according to speed_factor
    image = rescale(image, 1/math.sqrt(speed_factor))  # sqrt of speed_factor because scaling along both x and y
    templates_scaled = [rescale(im, 1/math.sqrt(speed_factor)) for im in templates]
    templates = templates_scaled
    # hyperparameters: min and max scales to check and size of steps between them
    # (will work even if delta is not exactly divisible by step)
    min_scale = 0.70
    max_scale = 1.30
    step = 0.02
    count = int(((max_scale - min_scale) * (1/step)) + 1)
    scales = [min_scale + (i * step) for i in range(count)]
    # quality of match is determined for each scale according to below
    match_quality = []
    for scale in scales:
        # metric of match quality is the sum of the quality of best match for each template
        metric = 0
        # rescale each template to the scale being tested and check quality of best match
        for t in templates:
            scaled = rescale(t, scale)
            match_result = cv.matchTemplate(image, scaled, cv.TM_CCORR_NORMED)
            dummy, max_val, dummy2, max_loc = cv.minMaxLoc(match_result)
            metric += max_val
        match_quality.append(metric)
    # choose scale with best overall quality
    chosen = match_quality.index(max(match_quality))
    scale_out = scales[chosen]
    return scale_out


def rescale(image, scale):
    # provides shorthand go get proportionally-resized image according to given scale without changing original
    return cv.resize(image.copy(), (int(image.shape[1] * scale), int(image.shape[0] * scale)),
                     interpolation=cv.INTER_AREA)


def jack_id(image, template):
    # match to template, add graphic elements to image, and return location of center according to single best match
    dummy, match_val, dummy2, match_pos = cv.minMaxLoc(cv.matchTemplate(image, template, cv.TM_CCORR_NORMED))
    w = template.shape[1]
    h = template.shape[0]
    center = (match_pos[0] + (w // 2), match_pos[1] + (h // 2))
    cv.rectangle(image, match_pos, (match_pos[0] + w, match_pos[1] + h), (0, 255, 0), 5)
    cv.circle(image, center, 5, (0, 255, 0), -1)
    return center


def ball_id(image, target_center, ball):
    # find each ball and return distances relative to target, assuming four balls are present
    w = ball.shape[1]
    h = ball.shape[0]
    # get corner locations of four (distinct) matches
    balls = get_n_matches(image, ball, 4)
    distances = []
    for corner in zip(*balls[::-1]):
        center = (corner[0] + (w // 2), corner[1] + (h // 2))
        distance = math.sqrt((center[0] - target_center[0]) ** 2 + (center[1] - target_center[1]) ** 2)
        distances.append(distance)
        # graphics
        cv.rectangle(image, corner, (corner[0] + w, corner[1] + h), (0, 255, 255), 5)
        cv.circle(image, center, 9, (0, 255, 255), -1)
        cv.putText(image, str(px_to_in(distance))[:4], (corner[0], corner[1] - 8),
                   cv.FONT_HERSHEY_SIMPLEX, 1.7, (0, 255, 255), 4, cv.LINE_AA)
    return distances


def get_n_matches(image, template, n):
    # get n matches of template to image and return corner positions
    res = cv.matchTemplate(image, template, cv.TM_CCORR_NORMED)
    # use pointify to prevent getting n matches of same real-world object otherwise would return four highest scores
    # which are likely to be slightly-varied identifications of the same real-world object
    points = pointify(res, n, template.shape[0] // 3)
    positions = np.nonzero(points)
    return positions


def pointify(array, n, sweep):
    # assumes 2D array with equal-length rows
    # "sweep" distance around n local maxima to ignore other high scores in nearly-identical positions
    out = np.zeros(array.shape)
    for i in range(n):
        dummy, active_val, dummy2, active_pos = cv.minMaxLoc(array)
        out[active_pos[1]][active_pos[0]] = active_val
        for j in range(sweep):
            for k in range(sweep):
                array[active_pos[1] - j][active_pos[0] - k] = 0
                array[active_pos[1] - j][active_pos[0] + k] = 0
                array[active_pos[1] + j][active_pos[0] - k] = 0
                array[active_pos[1] + j][active_pos[0] + k] = 0
    return out


def px_to_in(px):
    # pixel measurement to inches according to jack which has diameter of 53px in template and 1.5 inches in real world
    return px * (1.5 / 53)


def score(greens, reds):
    # find closest ball of each side; winner is closest of these
    mins = [min(greens), min(reds)]
    winner = 0 if mins[0] < mins[1] else 1
    dists = [greens, reds]
    # points awarded to winner equals total number of their balls closer than closest of opponent
    points = 0
    for ball in dists[winner]:
        if ball < mins[1 - (winner * 1)]:
            points += 1
    return winner, points


def score_gui(image, scoring):
    # add points and winner to each image
    cv.putText(image, str(scoring[1]) + ' point' + ('s' if scoring[1] > 1 else '') +
               ' to ' + ['green', 'red'][scoring[0]], (image.shape[1] // 30, image.shape[0] // 20),
               cv.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 255), 8, cv.LINE_AA)


if __name__ == '__main__':
    main(*[arg for arg in sys.argv[1:]])
