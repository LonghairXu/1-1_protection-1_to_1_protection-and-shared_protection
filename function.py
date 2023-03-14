import networkx as nx
import json
import random
import math


def read_topology(filename):
    # load JSON file
    json_graph = json.load(open(filename))

    # transform JSON structure into a NetworkX graph
    return nx.json_graph.node_link_graph(json_graph)


def generate_demands(G, deletion_percent=0.2):
    traffic_dict = {}

    traffic_Gbit_list = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

    # go through all the node pairs
    for src_id in G.nodes():
        for dst_id in G.nodes():
            if src_id >= dst_id:
                continue

            # randomly decide whether to add the traffic demand for this src-dst pair
            if random.random() > deletion_percent:
                traffic_dict[(src_id, dst_id)] = random.choice(traffic_Gbit_list)

    return traffic_dict


def set_priority(traffic_dict):
    traffic_dict_1_plus = {}
    traffic_dict_1_to = {}
    traffic_dict_sp = {}

    for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
        traffic_G = traffic_dict[(src_id, dst_id)]
        traffic_1_plus = traffic_G * 0.6
        traffic_1_to = traffic_G * 0.2
        traffic_sp = traffic_G * 0.2
        traffic_dict_sp[(src_id,dst_id)] = traffic_sp
        traffic_dict_1_plus[(src_id, dst_id)] = traffic_1_plus
        traffic_dict_1_to[(src_id, dst_id)] = traffic_1_to
    return traffic_dict_1_plus, traffic_dict_1_to, traffic_dict_sp


def clear_spectrum(G, num_slots=400):
    # occupation of all the channels of all the links is initially zero
    for link in G.edges:
        G.edges[link]['spectrum_slots'] = [0] * num_slots

def compute_k_edge_disjoint_paths(G, num_candidate_paths=10):
    k_paths_dict = {}

    for src_id in G.nodes():
        for dst_id in G.nodes():
            if src_id >= dst_id:
                continue

            # Compute primary path
            primary_path = nx.shortest_path(G, source=src_id, target=dst_id, weight='length')

            # Compute backup paths
            backup_paths = []
            path_generator = nx.edge_disjoint_paths(G, src_id, dst_id)

            for path in path_generator:
                if set(path) != set(primary_path):
                    backup_paths.append(path)
                    if len(backup_paths) == num_candidate_paths:
                        break

            k_paths_dict[(src_id, dst_id)] = [primary_path] + backup_paths

    return k_paths_dict


def choose_MF(G, path, traffic_G):
    '''choose modulation format with lowest spectrum occupation based on path traffic request'''

    # {traffic_request_Gbit/s: [(maximum_r  each, number_of_slots)]}
    MF_option = {100: [(4500, 6), (3500, 4), (3000, 3), (2500, 2), (1500, 2)],
                 200: [(2500, 8), (1500, 6), (1000, 5), (700, 4), (500, 3)],
                 300: [(2000, 10), (1500, 8), (1000, 7), (800, 6), (500, 4)],
                 400: [(2000, 16), (1000, 12), (800, 8), (600, 6), (200, 5)],
                 500: [(1500, 20), (800, 16), (600, 12), (500, 8), (200, 7)],
                 600: [(1000, 28), (700, 22), (500, 20), (400, 16), (200, 10)],
                 700: [(1000, 32), (600, 26), (400, 24), (300, 20), (200, 14)],
                 800: [(800, 36), (500, 32), (300, 28), (250, 24), (200, 18)],
                 900: [(600, 42), (400, 36), (250, 32), (200, 28), (100, 24)],
                 1000: [(500, 48), (300, 42), (200, 38), (150, 32), (100, 24)]}

    path_length = 0
    for link in zip(path, path[1:]):
        path_length += G.edges[link]['length']

    min_slots = 1e6

    # choose option with lowest number of slots with reach higher than path length
    for max_reach, num_slots in MF_option[traffic_G]:
        if path_length <= max_reach and num_slots < min_slots:
            min_slots = num_slots

    # return default value of 1 if no valid modulation format option was found
    if min_slots == 1e6:
        return 1
    else:
        return int(min_slots)


def First_Fit(G, path, num_slots):
    # check if the graph has a num_slots attribute
    if 'num_slots' not in G.graph:
        raise ValueError("The graph must have a 'num_slots' attribute.")

    slots_in_band = G.graph["num_slots"]
    reserved_slots = [False] * slots_in_band

    # calculate the number of slots required for primary and backup paths
    num_slots_req = num_slots * 2

    for slot in range(slots_in_band - num_slots_req + 1):
        # check if the slots are available for both primary and backup paths
        backup_path_start = slot + num_slots
        backup_path_end = slot + num_slots_req
        if all(not reserved_slots[i] for i in range(slot, backup_path_start)) and all(
                not reserved_slots[i] for i in range(backup_path_start, backup_path_end)):
            # mark the slots as reserved for both primary and backup paths
            for i in range(slot, backup_path_end):
                reserved_slots[i] = True
            return slot

    return None

def occupy_spectrum(G, path, first_slot, num_slots):
    for link in zip(path, path[1:]):
        for slot_shift in range(num_slots):
            G.edges[link]['spectrum_slots'][first_slot + slot_shift] = 1

def spectrum_occupation(G):
    num_slots_occupied = 0
    for link in G.edges:
        num_slots_occupied += sum(G.edges[link]['spectrum_slots'])

    return num_slots_occupied

def get_num_transponders(chosen_paths):
    num_transponders = 0
    for path_tuple in chosen_paths.values():
        if len(path_tuple) == 2:
            p1, p2 = path_tuple
            if p1 != -1:
                num_transponders += 1
            if p2 != -1:
                num_transponders += 1
    return num_transponders


def get_num_transponders_1_to_1(one_to_one):
    num_transponders = 0
    for paths in one_to_one:
        if len(paths) == 2:
            num_transponders += 1
    return num_transponders


def get_num_transponders_shared_protection(G, chosen_paths, traffic_dict):
    num_transponders = 0
    for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
        traffic_G = traffic_dict[(src_id, dst_id)]
        if traffic_G < 50:
            traffic_G = 100
        else:
            traffic_G = round(traffic_G, -2)
        primary_path, backup_path = chosen_paths[(src_id, dst_id)]

        if backup_path is None:
            num_slots_primary = choose_MF(G, primary_path, traffic_G)
            num_transponders += math.ceil(num_slots_primary / 2)
        else:
            num_slots_primary = choose_MF(G, primary_path, traffic_G)
            num_slots_backup = choose_MF(G, backup_path, traffic_G)
            num_transponders += math.ceil(max(num_slots_primary, num_slots_backup) / 2)

    return num_transponders

def is_path_available(G, path, first_slot, num_slots):
    spectrum_available = G.graph.get('spectrum_available', {})
    for i in range(len(path)):
        if i == len(path) - 1:
            continue
        edge = (path[i], path[i+1])
        if edge not in spectrum_available:
            return False
        for slot in range(first_slot, first_slot + num_slots):
            if slot not in spectrum_available[edge]:
                return False
        for adjacent_edge in G.edges(path[i]):
            if adjacent_edge == edge or adjacent_edge == (path[i+1], path[i]):
                continue
            if adjacent_edge not in spectrum_available:
                return False
            for slot in range(first_slot, first_slot + num_slots):
                if slot not in spectrum_available[adjacent_edge]:
                    return False
    return True

def release_spectrum(G, path, first_slot, num_slots):
    for i in range(1, len(path)):
        if 'spectrum_slots' in G[path[i-1]][path[i]]:
            for slot in range(first_slot, first_slot + num_slots):
                G[path[i-1]][path[i]]['spectrum_slots'][slot] = 0


def k_shortest_path_first_fit_1_plus_1_RSA(G, k_SP_dict, traffic_dict):
    chosen_paths = {}

    for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
        traffic_G = traffic_dict[(src_id, dst_id)]
        if traffic_G < 50:
            traffic_G = 100
        else:
            traffic_G = round(traffic_G, -2)

        k_paths = k_SP_dict[(src_id, dst_id)]
        primary_path = k_paths[0]
        backup_paths = k_paths[1:]

        # Allocate spectrum for primary path
        num_slots = choose_MF(G, primary_path, traffic_G)
        primary_first_slot = First_Fit(G, primary_path, num_slots)
        occupy_spectrum(G, primary_path, primary_first_slot, num_slots)

        # Allocate spectrum for backup path
        backup_path = None
        for path in backup_paths:
            num_slots = choose_MF(G, path, traffic_G)
            first_slot = First_Fit(G, path, num_slots)
            if first_slot is not None:
                backup_path = path
                occupy_spectrum(G, backup_path, first_slot, num_slots)
                break

        chosen_paths[(src_id, dst_id)] = (primary_path, backup_path)

    return chosen_paths


def k_shortest_path_first_fit_1_to_1_RSA(G, k_SP_dict, traffic_dict):
    chosen_paths = {}

    for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
        traffic_G = traffic_dict[(src_id, dst_id)]
        if traffic_G < 50:
            traffic_G = 100
        else:
            traffic_G = round(traffic_G, -2)

        k_paths = k_SP_dict[(src_id, dst_id)]
        primary_path = k_paths[0]
        backup_path = None

        # Allocate spectrum for primary path
        num_slots = choose_MF(G, primary_path, traffic_G)
        primary_first_slot = First_Fit(G, primary_path, num_slots)
        occupy_spectrum(G, primary_path, primary_first_slot, num_slots)

        # Check if the primary path is available, if not, switch to backup path
        if not is_path_available(G, primary_path, primary_first_slot, num_slots):
            for path in k_paths[1:]:
                # Allocate spectrum for backup path
                num_slots = choose_MF(G, path, traffic_G)
                first_slot = First_Fit(G, path, num_slots)
                if is_path_available(G, path, first_slot, num_slots):
                    backup_path = path
                    occupy_spectrum(G, backup_path, first_slot, num_slots)
                    break

            # Switch the traffic to the backup path
            if backup_path:
                release_spectrum(G, primary_path, primary_first_slot, num_slots)
                primary_path = backup_path
                primary_first_slot = first_slot
                occupy_spectrum(G, primary_path, primary_first_slot, num_slots)

        chosen_paths[(src_id, dst_id)] = primary_path

    return chosen_paths

def k_shortest_path_shared_protection(G, k_SP_dict, traffic_dict):
    chosen_paths = {}

    # Group demands that share a common link or node
    group_dict = {}
    for demand_id, (src_id, dst_id) in enumerate(traffic_dict.keys()):
        for path in k_SP_dict[(src_id, dst_id)]:
            for u, v in zip(path[:-1], path[1:]):
                group_key = frozenset([u, v])
                if group_key not in group_dict:
                    group_dict[group_key] = []
                group_dict[group_key].append((demand_id, src_id, dst_id))

    # Compute shared backup paths for each group
    for group_demands in group_dict.values():
        # Compute all k shortest paths for each demand in the group
        k_paths_dict = {}
        for demand_id, src_id, dst_id in group_demands:
            k_paths_dict[demand_id] = k_SP_dict[(src_id, dst_id)]

        # Find the common backup path that satisfies any two demands in the group
        common_backup_path = None
        for i, (demand_id_1, _, _) in enumerate(group_demands):
            for j, (demand_id_2, _, _) in enumerate(group_demands[i+1:], start=i+1):
                backup_paths_1 = k_paths_dict[demand_id_1][1:]
                backup_paths_2 = k_paths_dict[demand_id_2][1:]
                for path_1 in backup_paths_1:
                    for path_2 in backup_paths_2:
                        if path_1 == path_2:
                            common_backup_path = path_1
                            break
                    if common_backup_path is not None:
                        break
                if common_backup_path is not None:
                    break
            if common_backup_path is not None:
                break

        # Allocate primary and backup paths for each demand in the group
        for demand_id, src_id, dst_id in group_demands:
            traffic_G = traffic_dict[(src_id, dst_id)]
            if traffic_G < 50:
                traffic_G = 100
            else:
                traffic_G = round(traffic_G, -2)
            primary_path = k_paths_dict[demand_id][0]
            num_slots = choose_MF(G, primary_path, traffic_G)
            primary_first_slot = First_Fit(G, primary_path, num_slots)
            # occupy_spectrum(G, primary_path, primary_first_slot, num_slots)
            backup_path = None
            if common_backup_path is not None:
                backup_path = common_backup_path
                num_slots = choose_MF(G, common_backup_path, traffic_G)
                first_slot = First_Fit(G, common_backup_path, num_slots)
                occupy_spectrum(G, common_backup_path, first_slot, num_slots)
            else:
                backup_paths = k_paths_dict[demand_id][1:]
                for path in backup_paths:
                    if path != primary_path:
                        backup_path = path
                        num_slots = choose_MF(G, backup_path, traffic_G)
                        first_slot = First_Fit(G, backup_path, num_slots)
                        # occupy_spectrum(G, backup_path, first_slot, num_slots)
                        break

            chosen_paths[(src_id, dst_id)] = (None, backup_path)

    return chosen_paths

























