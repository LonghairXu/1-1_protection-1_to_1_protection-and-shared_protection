import random
from function import generate_demands, read_topology,clear_spectrum, compute_k_edge_disjoint_paths, k_shortest_path_first_fit_1_plus_1_RSA, get_num_transponders,k_shortest_path_first_fit_1_to_1_RSA, get_num_transponders_1_to_1,set_priority, k_shortest_path_shared_protection, get_num_transponders_shared_protection, spectrum_occupation

topology_filename = 'IT_21.json'
G = read_topology(topology_filename)
G.graph['num_slots'] = 400

num_slots = 400
clear_spectrum(G, num_slots)
for u, v in G.edges():
    G[u][v]['spectrum_available'] = {i: True for i in range(num_slots)}

num_candidate_paths = 10
k_path_candidate = compute_k_edge_disjoint_paths(G, num_candidate_paths=10)

for i in range(42,52):
    saving_spectrum_1_to = {}
    saving_spectrum_sp = {}
    random.seed(i)
    traffic_dict = generate_demands(G)
    traffic_dict_1_plus, traffic_dict_1_to, traffic_sp = set_priority(traffic_dict)
    # print('Number of traffic demands:', len(traffic_dict))
    clear_spectrum(G)
    k_plus_1 = k_shortest_path_first_fit_1_plus_1_RSA(G, k_path_candidate, traffic_dict_1_plus)
    slots_1_plus = spectrum_occupation(G)
    print(slots_1_plus, 'slots occupied in the 1+1')
    clear_spectrum(G)
    k_1to_1 = k_shortest_path_first_fit_1_to_1_RSA(G,k_path_candidate,traffic_dict_1_to)
    slots_1_to = spectrum_occupation(G)
    print(slots_1_to, 'slots occupied in the 1:1')
    clear_spectrum(G)
    k_sp = k_shortest_path_shared_protection(G,k_path_candidate,traffic_sp)
    slots_sp = spectrum_occupation(G)
    print(slots_sp, 'slots occupied in the shared_protection')
    clear_spectrum(G)

    num_transponders_1_pus = get_num_transponders(k_plus_1)
    num_transponders_1_to = get_num_transponders_1_to_1(k_1to_1)
    num_transponders_sp = get_num_transponders(k_sp)

    print(num_transponders_1_to,'the num of transponders used in 1:1 protection ')
    print(num_transponders_1_pus,'the num of transponders used in 1+1 protection ')
    print(num_transponders_1_to,'the num of transponders used in shared protection ')
    saving_tranponders_1_to = (num_transponders_1_pus - num_transponders_1_to)/num_transponders_1_pus
    saving_tranponders_sp = (num_transponders_1_pus - num_transponders_sp)/num_transponders_1_pus

    saving_spectrum_1_to = (slots_1_plus - slots_1_to)/ slots_1_plus
    saving_spectrum_sp = (slots_1_plus - slots_sp) / slots_1_plus

    print(saving_spectrum_1_to)
    print(saving_spectrum_sp)
    print(saving_tranponders_1_to)
    print(saving_tranponders_sp)




