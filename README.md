# 1+1, 1:1 & Shared Protection

Reference implementations of three routing-and-spectrum-allocation (RSA) protection schemes for elastic optical networks, plus helper scripts for proactive path monitoring and topology visualization.

---

## Features

- **Protection Schemes**  
  - **1+1 Protection**: Primary and backup paths carry traffic simultaneously; immediate switchover on failure.  
  - **1:1 Protection**: Backup path reserved; traffic switches over only when primary fails.  
  - **Shared Protection**: Multiple demands share a common backup resource.

- **Core Functions (`function.py`)**  
  - Load a JSON‐formatted topology (NetworkX).  
  - Generate random traffic demands.  
  - Compute up to *k* edge‐disjoint paths.  
  - First-Fit RSA for each protection scheme.  
  - Spectrum management (clear/occupy/release slots).  
  - Transponder counting and savings calculation.

- **Proactive Monitoring (`run_function.py`)**  
  - Periodically test primary path Packet Loss Ratio (PLR).  
  - Automatic switchover to backup if PLR exceeds a threshold.

- **Topology Visualization (`topology_show.py`)**  
  - Draws a directed graph from `IT_21.json` using NetworkX + Matplotlib.

---

## Prerequisites

- Python 3.7+  
- [NetworkX](https://networkx.org/) (2.x)  
- [Matplotlib](https://matplotlib.org/) (for topology visualization)

---

## Installation

```bash
git clone https://github.com/LonghairXu/1-1_protection-1_to_1_protection-and-shared_protection.git
cd 1-1_protection-1_to_1_protection-and-shared_protection
python3 -m venv venv
source venv/bin/activate         # (Windows: venv\Scripts\activate.bat)
pip install networkx matplotlib
