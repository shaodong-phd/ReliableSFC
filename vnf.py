#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :vnf.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/10 16:32
@IDE     :PyCharm  
@Note    :
"""

# -1 is control center; 0 is svnf
PLA_LATENCY = {'-1': 0, '0': 10, '1': 10, '2': 10, '3': 10, '4': 10, '5': 10, '6': 10}
COMPUTER_DEMAND = {'-1': 0, '0': 20, '1': 26, '2': 30, '3': 48, '4': 28, '5': 34, '6': 40}
SINGLE_FAILURE = {'-1': 0, '0': 0, '1': 0.02, '2': 0.08, '3': 0.1, '4': 0.11, '5': 0.04, '6': 0.03}


class VNF:
    instance_count = 0
    def __init__(self, vnf_type):
        VNF.instance_count += 1
        self.vnf_id = VNF.instance_count  # VNF instance ID
        self.vnf_type = vnf_type
        self.vnf_computer_demand = COMPUTER_DEMAND[str(vnf_type)]
        self.pla_node = -1  # the placement node of VNF
        self.pla_time = PLA_LATENCY[str(vnf_type)]
        self.ser_sfc_list = []  # the sfcs provided by the VNF
        self.prior_vnf = []  # the preceding VNFs of the VNF
        self.follow_vnfs = []  # the preceding VNFs of the VNF
        self.single_fail = SINGLE_FAILURE[str(vnf_type)]
        self.dep_fail = 0  # dependent failure
        self.protected_relia = 0
        self.visited = 0
        self.max_load_latency = 10
        self.max_load_data_vol = 3
        self.bvnfs_list = []


class BACKUPVNF:
    instance_count = 0
    def __init__(self, vnf_type):
        BACKUPVNF.instance_count += 1
        self.bvnf_id = BACKUPVNF.instance_count
        self.vnf_type = vnf_type  # BVNF instance type
        self.pro_vnf = None  # The VNF protected the bvnf
        self.vnf_computer_demand = COMPUTER_DEMAND[str(vnf_type)]  # the computer command of VNF instance
        self.pla_node = -1  # the node of placement
        self.nodes_cost = None  # the cost of placement and comm
        self.single_fail = SINGLE_FAILURE[str(vnf_type)]  # single failure


def SearchVNFById(vnf_list, id):
    for vnf_type in vnf_list:
        for vnf in vnf_type:
            if vnf.vnf_id == id:
                return vnf
    return None
