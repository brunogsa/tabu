# -*- coding: utf-8 -*-
import math
import random


# Function which calculates the euclidean distance between two points
def euclidean_distance(v1, v2):
    return round(math.sqrt(pow((v1[0] - v2[0]), 2) + pow((v1[1] - v2[1]), 2)))


# Function that evaluates the total length of a path
def tour_cost(perm):
    # Here tour tour_cost refers to the sum of the euclidean distance between consecutive points starting from first element
    total_distance = 0.0
    size = len(perm)
    for index in range(size):
        # select the consecutive point for calculating the segment length
        if index == size - 1:
            # This is because in order to complete the 'tour' we need to reach the starting point
            point2 = perm[0]
        else:  # select the next point
            point2 = perm[index + 1]

        total_distance += euclidean_distance(perm[index], point2)

    return total_distance


# Function that creates a random permutation from an initial permutation by shuffling the elements in to a random order
def construct_initial_solution(init_perm):
    # Randomize the initial permutation
    permutation = init_perm[:]  # make a copy of the initial permutation
    size = len(permutation)
    for index in range(size):
        # shuffle the values of the initial permutation randomly
        # get a random index and exchange values
        shuffle_index = random.randrange(index, size)  # randrange would exclude the upper bound
        permutation[shuffle_index], permutation[index] = permutation[index], permutation[shuffle_index]

    return permutation


def stochastic_two_opt_with_edges(perm):
    result = perm[:]  # make a copy
    size = len(result)
    # select indices of two random points in the tour
    p1, p2 = random.randrange(0, size), random.randrange(0, size)
    # do this so as not to overshoot tour boundaries
    exclude = {p1}
    if p1 == 0:
        exclude.add(size - 1)
    else:
        exclude.add(p1 - 1)

    if p1 == size - 1:
        exclude.add(0)
    else:
        exclude.add(p1 + 1)

    while p2 in exclude:
        p2 = random.randrange(0, size)

    # to ensure we always have p1<p2
    if p2 < p1:
        p1, p2 = p2, p1

    # now reverse the tour segment between p1 and p2
    result[p1:p2] = reversed(result[p1:p2])

    return result, [[perm[p1 - 1], perm[p1]], [perm[p2 - 1], perm[p2]]]


# Function that returns a best candidate, sorting by tour_cost
def locate_best_candidate(candidates):
    candidates.sort(key=lambda (c): c["candidate"]["tour_cost"])
    best, edges = candidates[0]["candidate"], candidates[0]["edges"]
    return best, edges


def is_tabu(perm, tabu_List):
    result = False
    size = len(perm)
    for index, edge1 in enumerate(perm):
        if index == size - 1:
            edge2 = perm[0]
        else:
            edge2 = perm[index + 1]
        if [edge1, edge2] in tabu_List:
            result = True
            break

    return result


def generate_candidates(best, tabu_list):
    permutation, edges, result = best["permutation"], None, {}
    while edges is None or is_tabu(permutation, tabu_list):
        permutation, edges = stochastic_two_opt_with_edges(best["permutation"])
    candidate = {}
    candidate["permutation"] = permutation
    candidate["tour_cost"] = tour_cost(candidate["permutation"])
    result["candidate"] = candidate
    result["edges"] = edges
    return result


def search(points, max_iterations, max_tabu, max_candidates):
    # construct a random tour
    best = {}
    best["permutation"] = construct_initial_solution(points)
    best["tour_cost"] = tour_cost(best["permutation"])
    tabu_list = []
    for index in range(max_iterations):
        # Generate candidates using stochastic 2-opt near current best candidate
        # Use Tabu list to not revisit previous rewired edges
        candidates = []
        for index2 in range(0, max_candidates):
            candidates.append(generate_candidates(best, tabu_list))
        # Locate the best candidate
        # sort the list of candidates by tour_cost
        # since it is an  involved sort, we write a function for getting the least tour_cost candidate
        best_candidate, best_candidate_edges = locate_best_candidate(candidates)
        # compare with current best and update if necessary
        if best_candidate["tour_cost"] < best["tour_cost"]:
            # set current to the best, so that we can continue iteration
            best = best_candidate
            # update tabu list
            for edge in best_candidate_edges:
                if len(tabu_list) < max_tabu:
                    tabu_list.append(edge)

        print " > iteration " + str(index + 1) + ", best=" + str(best["tour_cost"])

    return best


def main():
    berlin52 = [[565, 575], [25, 185], [345, 750], [945, 685], [845, 655],
                [880, 660], [25, 230], [525, 1000], [580, 1175], [650, 1130], [1605, 620],
                [1220, 580], [1465, 200], [1530, 5], [845, 680], [725, 370], [145, 665],
                [415, 635], [510, 875], [560, 365], [300, 465], [520, 585], [480, 415],
                [835, 625], [975, 580], [1215, 245], [1320, 315], [1250, 400], [660, 180],
                [410, 250], [420, 555], [575, 665], [1150, 1160], [700, 580], [685, 595],
                [685, 610], [770, 610], [795, 645], [720, 635], [760, 650], [475, 960],
                [95, 260], [875, 920], [700, 500], [555, 815], [830, 485], [1170, 65],
                [830, 610], [605, 625], [595, 360], [1340, 725], [1740, 245]]
    max_iterations = 100
    max_tabu_count = 15
    max_candidates = 50
    # Execute the algorithm
    result = search(berlin52, max_iterations, max_tabu_count, max_candidates)
    print "Best Solution: c=" + str(result["tour_cost"]) + ", v=" + str(result["permutation"])
    print "Optimal solution c=7542"


main()