# ReliableSFC


Edge networks (ENs) possess the capability to deliver low-latency network services for users by allowing the flexible placement of Virtual Network Functions (VNFs) on edge nodes with limited computing resources and close to users. The VNFs can be arranged to form Service Function Chains (SFCs), processing traffic in specified orders based on services requested by users. Unfortunately, VNFs are susceptible to generate errors due to internal and external factors (e.g., malicious traffic), which can propagate with uncertain range through the SFCs. To prevent dependent failures caused by error propagation, secure VNFs (SVNFs, e.g., intrusion detection systems) should be placed and inserted strategically between certain pairs of VNFs in SFCs to detect and clear errors. However, owing to the uncertain range of error propagation, it is challenging to make the optimal decisions of placing VNFs and SVNFs to form SFCs with the minimum costs of placement and communication in real-time while the latency and reliability requirements of the services can be guaranteed. Therefore, we proposed an online scheme TTSP with provable competitive ratios to solve the problem, which decouples it into two subproblems of VNFs and SVNFs placement. 



We will describe the role of the important files, along with the experimental parameters and execution steps, to provide researchers with the opportunity to reproduce and extend the scheme TTSP.

### Files Description:

- **vnf.py** and **sfc.py** are files containing classes for VNF and SFC, respectively. They describe the attributes of these two classes, such as computational resource requirements and reliability.

  ```python
  COMPUTER_DEMAND = {'-1': 0, '0': 20, '1': 26, '2': 30, '3': 48, '4': 28, '5': 34, '6': 40}
  SINGLE_FAILURE = {'-1': 0, '0': 0, '1': 0.02, '2': 0.08, '3': 0.1, '4': 0.11, '5': 0.04, '6': 0.03}
  ```

- **network.py** describes the number and structure of network nodes, such as the one-hop latency between nodes.

  ```python
  self.unit_computer_cost = 0.03
  self.unit_trans_cost = 0.01
  self.nodes_computer = [180, 200, 150, 300, 280, 170, 130, 210, 240, 190, 120]
  self.nodes_remain_computer = [180, 200, 150, 300, 280, 170, 130, 210, 240, 190, 120]
  ```

- **RVPP.py** makes the VNF placement, selection, and BVNF placement decisions.

- **SPEP.py** makes the SVNF placement and insertion decisions.

- **TSP.py** integrates the RVPP and SPEP algorithms, making placement decisions for each service's corresponding SFC in each time slot.

- The **Dataset** file contains data on different SFC lengths and quantities, as well as dependency failure datasets, based on the Canadian Security Center dataset. For example, the information about SFCs is described as follow: 

  ```python
  id,vnf_set,latency_com,relia_com,data_volumn,source_node,des_node
  0,"4, 2, 5, 1",145,0.855874148,1.7,8,2
  1,"4, 6, 1, 3",140,0.826540415,1.2,4,6
  2,"3, 1, 2, 6",146,0.971008848,0.9,5,1
  3,"2, 5, 4, 1",175,0.900961818,1.9,9,10
  4,"5, 3, 2, 6",142,0.972656593,1.9,9,8
  5,"4, 3, 5, 2",160,0.936574139,1,9,2
  ```

### Execution Steps:
**Step 01**: Researchers download the code files and configure the basic Python environment. For example, researchers need to import numpy as np.

**Step 02**: Load the dataset information.

**Step 03**: Run the TSP.py to test TTSP algorithm.
