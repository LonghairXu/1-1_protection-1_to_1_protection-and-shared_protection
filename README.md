Next-generation optical transport networks require robust protection schemes to ensure uninterrupted service in case of fiber cuts or node failures. This repository contains reference implementations of:

1. 1+1, 1:1 Protection: Each working path has a dedicated protection path; switchover occurs immediately upon fault detection.

2. Shared Protection: Multiple working paths share a pool of protection resources; only one protection path is used at a time if a fault occurs.

Specify any language versions, libraries, or tools required. For example:

Python 3.8 or higher

NetworkX (for topology modeling)

PyTest (for running automated tests)

(Optional) gRPC or REST frameworks if integrating with external control planes

Make or GNU Makefiles (if you provide Make targets)

Project Structure
├── configs/
│   ├── topology_mesh.json
│   ├── topology_ring.json
│   ├── working_path_A.json
│   ├── working_path_B.json
│   └── shared_pool.json
├── examples/
│   ├── demo_1to1_protection.py
│   └── demo_shared_protection.py
├── protection/
│   ├── __init__.py
│   ├── base.py               # Common abstractions (Topology, Path, FaultInjector)
│   ├── protection_1to1.py     # 1:1 protection implementation
│   └── protection_shared.py   # Shared protection implementation
├── tests/
│   ├── test_1to1.py
│   └── test_shared.py
└── README.md                 # ← You are here
