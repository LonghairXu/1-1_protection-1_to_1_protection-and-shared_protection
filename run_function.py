import networkx as nx
import json
import heapq
import random
import time

# def k_shortest_path_first_fit_1_plus_1_RSA(G, k_SP_dict, traffic_dict):
#     chosen_paths = {}
#
#     # Total number of spectrum slots
#     max_slots = 400
#
#     for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
#         traffic_G = traffic_dict[(src_id, dst_id)]
#         k_paths = k_SP_dict[(src_id, dst_id)]
#         primary_path = k_paths[0]
#         backup_paths = k_paths[1:]
#
#         # Allocate spectrum for primary path
#         num_slots = choose_MF(G, primary_path, traffic_G)
#         primary_first_slot = First_Fit(G, primary_path, num_slots)
#         occupy_spectrum(G, primary_path, primary_first_slot, num_slots)
#
#         # Allocate spectrum for backup path
#         backup_path = None
#         for path in backup_paths:
#             num_slots = choose_MF(G, path, traffic_G)
#             first_slot = First_Fit(G, path, num_slots)
#             if first_slot is not None:
#                 backup_path = path
#                 occupy_spectrum(G, backup_path, first_slot, num_slots)
#
#                 # Check if total occupied slots exceed max_slots
#                 total_slots = sum(len(slots) for slots in G.graph['spectrum_available'].values())
#                 if total_slots > max_slots:
#                     release_spectrum(G, backup_path)
#                     backup_path = None
#                     break
#
#         chosen_paths[(src_id, dst_id)] = (primary_path, backup_path)
#
#     return chosen_paths

def proactive_1_plus_1_protection(G, k_paths, traffic_dict, interval):
    '''Proactive 1+1 protection scheme with periodic path testing'''

    # initialize path status dictionary
    path_status = {}
    for demand, paths in k_paths.items():
        path_status[demand] = {'primary': paths[0], 'backup': paths[1], 'active': 'primary', 'last_checked': 0}

    # iterate over time intervals
    while True:

        # check path statuses for each demand
        for demand, status in path_status.items():

            # check if it's time to test the primary path
            if time.time() - status['last_checked'] >= interval:

                # test primary path
                primary_PLR = calculate_PLR(G, demand, status['primary'])
                if primary_PLR > 0.1:
                    # if primary path PLR is higher than threshold, switch to backup path
                    status['active'] = 'backup'
                    print(f"Switching demand {demand} to backup path")

                # update last checked time
                status['last_checked'] = time.time()

        # sleep for the interval
        time.sleep(interval)


def is_path_working(G, path, demand):
    '''Check if path is working by verifying that there are enough free spectrum slots'''

    num_slots = G.graph['num_slots']

    # find first fit along path
    first_slot = First_Fit(G, path, num_slots)

    if first_slot is not None:
        # mark the slots as reserved for the demand
        for link in zip(path, path[1:]):
            for i in range(first_slot, first_slot + num_slots):
                G.edges[link]['spectrum_slots'][i] = demand['demand_id']

        # simulate transmission along the path
        for link in zip(path, path[1:]):
            for slot in range(demand['num_slots']):
                if G.edges[link]['spectrum_slots'][demand['first_slot'] + slot] != demand['demand_id']:
                    return 1

        return 0

    return 1

def calculate_PLR(G, demand, path):
    '''calculate the packet loss ratio for a demand along a path in a graph'''

    primary_PLR = is_path_working(G, path, demand)
    if primary_PLR > 0.1 and 'backup_path' in demand:
        backup_path = demand['backup_path']
        backup_PLR = is_path_working(G, backup_path, demand)
        if backup_PLR <= primary_PLR:
            return backup_PLR

    return primary_PLR

def compute_1_1_edge_disjoint_paths(G, num_candidate_paths=10):
    k_paths_dict = {}

    for src_id in G.nodes():
        for dst_id in G.nodes():
            if src_id >= dst_id:
                continue

            path_generator = nx.edge_disjoint_paths(G, src_id, dst_id)

            shortest_paths = []
            for path in path_generator:
                cost = len(path) - 1
                heapq.heappush(shortest_paths, (cost, path))
                if len(shortest_paths) > num_candidate_paths:
                    heapq.heappop(shortest_paths)

            k_paths_dict[(src_id, dst_id)] = []
            for path_ind, short_path in enumerate(shortest_paths):
                if path_ind == num_candidate_paths:
                    break
                else:
                    k_paths_dict[(src_id, dst_id)].append(short_path[1])

            if len(k_paths_dict[(src_id, dst_id)]) == 0:
                k_paths_dict[(src_id, dst_id)] = None

    return k_paths_dict

# def k_shortest_path_first_fit_1_to_1_RSA(G, k_SP_dict, traffic_dict):
#     chosen_paths = {}
#
#     # find route and spectrum allocation for every demand
#     for (src_id, dst_id), traffic_G in traffic_dict.items():
#
#         # Initialize the first and second paths to None
#         first_path = None
#         second_path = None
#
#         # sequentially check candidate paths
#         for path in k_SP_dict[(src_id, dst_id)]:
#
#             # choose MF that provisions traffic with lowest spectrum occupation
#             num_slots = choose_MF(G, path, traffic_G)
#
#             # find first available spectrum channel along this path
#             first_slot = First_Fit(G, path, num_slots)
#
#             # spectrum found
#             if first_slot is not None:
#                 # If the first path is not set, set it to this path and occupy its spectrum
#                 if first_path is None:
#                     first_path = path
#                     occupy_spectrum(G, path, first_slot, num_slots)
#                 # If the first path is set but the second path is not, set the second path to this path and occupy its spectrum
#                 elif second_path is None:
#                     second_path = path
#                     occupy_spectrum(G, path, first_slot, num_slots)
#                     # If the second path has been set, break out of the loop since we have found both paths
#                     break
#
#         # Save the chosen paths for this demand
#         if first_path is not None and second_path is not None:
#             chosen_paths[(src_id, dst_id)] = (first_path, second_path)
#         else:
#             # If we couldn't find both paths, append None to indicate failure
#             chosen_paths[(src_id, dst_id)] = (None, None)
#
#     return chosen_paths

def proactive_1_to_1_protection(G, k_11_dict, traffic_dict, interval):
    # initialize path status dictionary
    path_status = {}
    for demand, paths in k_11_dict.items():
        path_status[demand] = {'primary': paths[0], 'backup': paths[1], 'active': 'primary', 'last_checked': 0}

    while True:
        for demand, status in path_status.items():
            # check if it's time to test the primary path
            if time.time() - status['last_checked'] >= interval:
                # test primary path
                primary_working = is_path_working(G, status['primary'], traffic_dict[demand])
                if not primary_working:
                    # switch to backup path
                    status['active'] = 'backup'
                    print(f"Switching demand {demand} to backup path")

                # update last checked time
                status['last_checked'] = time.time()

        # sleep for the interval
        time.sleep(interval)


def is_path_working_1_to(G, path, demand):
    # extract demand parameters
    num_slots = demand['num_slots']
    first_slot = demand['first_slot']

    # check if there are enough free slots in the spectrum
    for link in zip(path, path[1:]):
        for i in range(first_slot, first_slot + num_slots):
            if G.edges[link]['spectrum_slots'][i] != 0:
                return False

    # mark the slots as reserved for the demand
    for link in zip(path, path[1:]):
        for i in range(first_slot, first_slot + num_slots):
            G.edges[link]['spectrum_slots'][i] = demand['demand_id']

    return True

def calculate_1_to_1_PLR(G, k_paths, traffic_dict):
    '''Calculate the path loss ratio (PLR) for each demand in a 1-to-1 protection scheme'''

    PLRs = []

    for (src_id, dst_id), traffic_G in traffic_dict.items():
        # get the primary and backup paths for this demand
        primary_path, backup_path = k_paths[(src_id, dst_id)]

        # if both paths are None, there is no protection for this demand
        if primary_path is None and backup_path is None:
            PLRs.append(1.0)
            continue

        # calculate the PLR for the primary path
        primary_PLR = calculate_PLR(G, (src_id, dst_id), primary_path)

        # if the primary path PLR is below the threshold, we don't need to check the backup path
        if primary_PLR <= 0.1:
            PLRs.append(primary_PLR)
            continue

        # calculate the PLR for the backup path
        backup_PLR = calculate_PLR(G, (src_id, dst_id), backup_path)

        # choose the path with the lowest PLR
        if primary_PLR <= backup_PLR:
            PLRs.append(primary_PLR)
        else:
            PLRs.append(backup_PLR)

    return PLRs

# check num of spectrum used

# def check_spectrum_availability(G, path, first_slot, num_slots):
#     for link in zip(path, path[1:]):
#         if len(G.edges[link]['spectrum_slots']) < first_slot + num_slots:
#             return False
#         for slot_shift in range(num_slots):
#             if G.edges[link]['spectrum_slots'][first_slot + slot_shift] != 0:
#                 return False
#     return True
#
# def k_1_1_spectrum(G, k_shortest_paths_dict, traffic_dict, num_slots):
#     # Allocate spectrum to each path in the order of k-shortest paths
#     allocated_spectrum = {}
#     for src, dst in traffic_dict.keys():
#         for k in range(len(k_shortest_paths_dict[(src, dst)])):
#             path = k_shortest_paths_dict[(src, dst)][k]
#             # Try to allocate spectrum to the path
#             for slot in range(num_slots):
#                 if check_spectrum_availability(G, path, slot, num_slots):
#                     # Spectrum allocation successful, store it and break the loop
#                     allocated_spectrum.update({(src, dst, k): list(range(slot, slot+num_slots))})
#                     occupy_spectrum(G, path, slot, num_slots)
#                     break
#             else:
#                 # Spectrum allocation failed for all slots, store None
#                 allocated_spectrum.update({(src, dst, k): None})
#     return allocated_spectrum
#
#
# def get_num_spectrum_slots(allocated_spectrum, num_slots):
#     spectrum_slots = [0] * num_slots
#     for spectrum in allocated_spectrum.values():
#         if spectrum is not None:
#             for slot in spectrum:
#                 spectrum_slots[slot] += 1
#     num_spectrum_slots = sum([1 for slots in spectrum_slots if slots > 0])
#     return num_spectrum_slots




