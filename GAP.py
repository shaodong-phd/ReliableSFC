#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :GAP.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/13 15:19
@IDE     :PyCharm  
@Note    :
"""

import numpy as np

def knapsack_max_value_with_decision(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    decisions = [[False] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if weights[i - 1] <= w:
                if values[i - 1] + dp[i - 1][w - weights[i - 1]] > dp[i - 1][w]:
                    dp[i][w] = values[i - 1] + dp[i - 1][w - weights[i - 1]]
                    decisions[i][w] = True
                else:
                    dp[i][w] = dp[i - 1][w]
            else:
                dp[i][w] = dp[i - 1][w]
    selected_items = []
    i, j = n, capacity
    while i > 0 and j > 0:
        if decisions[i][j]:
            selected_items.append(i - 1)
            j -= weights[i - 1]
        i -= 1
    return dp[n][capacity], selected_items

# ===========================================
def BackupPla(backup_list, node_num, network_graph):
    weights = []
    P = []
    for backup in backup_list:
        P.append(backup.nodes_cost.copy())
        weights.append(backup.vnf_computer_demand)
    for i in range(len(backup_list)):
        for j in range(node_num):
            P[i][j] = P[i][j] * -1 + 1000
    # decision
    T = np.zeros(len(backup_list), dtype=int)
    T[:] = -1
    for j in range(0, node_num):
        # Pj, benift for vnf to node j
        Pj = np.zeros(len(backup_list), dtype=int)
        for i in range(0, len(backup_list)):
            if T[i] == -1:
                Pj[i] = P[i][j]
            else:
                Pj[i] = P[i][j] - P[i][T[i]]
        max_value, put_decision = knapsack_max_value_with_decision(weights, Pj, network_graph.nodes_remain_computer[j])
        for item_id in put_decision:
            T[item_id] = j
    for backup_seq in range(0, len(backup_list)):
        backup_list[backup_seq].pla_node = T[backup_seq]
    return backup_list




