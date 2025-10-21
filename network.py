#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :network.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/10 21:32
@IDE     :PyCharm  
@Note    :
"""
import random
import pandas as pd
import numpy as np
from entity import VNF


class NETWORK:
    def __init__(self, node_num=11):
        self.node_num = node_num  # the number of edge nodes
        self.latency_matrix = np.zeros((node_num, node_num), dtype=int)
        self.unit_computer_cost = 0.03
        self.unit_trans_cost = 0.01
        self.nodes_computer = [180, 200, 150, 300, 280, 170, 130, 210, 240, 190, 120]
        self.nodes_remain_computer = [180, 200, 150, 300, 280, 170, 130, 210, 240, 190, 120]
        self.com_cost_matrix = np.zeros((node_num, node_num), dtype=int)
        self.syn_cost_ratio = 0.2
        self.SOURCE_VNF = VNF(-1)
        self.SOURCE_VNF.pla_node = 4

class SERVICENETWORK:
    def __init__(self):
        self.adj_matrix = None
    def BuildNetwork(self, node_num, vnf_list):
        for vnf_type_list in vnf_list:
            for vnf in vnf_type_list:
                print("yes")

