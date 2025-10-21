#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :RVPP.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/10 16:46
@IDE     :PyCharm  
@Note    :
"""
from turtledemo.nim import COLOR

from auxiliary_graph import HavePath
from data_process.data import ReadNetwork, ReadSFC, COLORS
from entity.vnf import VNF, BACKUPVNF
from entity.sfc import SFC
from entity.network import NETWORK
import numpy as np
import copy
from test.GAP import BackupPla

def ExcessLatencyDemand(Network_Graph, source_vnf, target_vnf, sfc):
    com_latency = Network_Graph.latency_matrix[source_vnf.pla_node][target_vnf.pla_node]
    total_data_volume = 0
    for s_i in target_vnf.ser_sfc_list:
        total_data_volume += s_i.data_volume
    pro_latency = target_vnf.max_load_latency * total_data_volume / target_vnf.max_load_data_vol  # 代表着加上该SFC,VNF的处理时延
    if sfc.actual_latency + com_latency + pro_latency > sfc.latency_com:
        return False
    return True

# comm cost ? place cost
def CostDemand(Network_Graph, source_vnf, target_vnf, sfc):
    com_cost = sfc.data_volume * Network_Graph.com_cost_matrix[source_vnf.pla_node][target_vnf.pla_node]
    pla_cost = target_vnf.vnf_computer_demand * Network_Graph.unit_computer_cost
    if com_cost < pla_cost:
        return True
    print("com_cost >= pla_cost:")
    return False


# judge whether exiting the connected error pair
def InBlackLists(source_vnf, target_vnf, vnf_list, BlackLists):
    source_vnf.follow_vnfs.append(target_vnf)
    vnf_list[target_vnf.vnf_type].append(target_vnf)
    in_black_list = False
    for pair in BlackLists:
        for vnf_i in vnf_list[pair[1]]:
            if vnf_i.pla_node == pair[0]:
                for vnf_j in vnf_list[pair[3]]:
                    if vnf_j.pla_node == pair[2]:
                        path = HavePath(vnf_i, vnf_j)
                        if path:
                            in_black_list = True
    source_vnf.follow_vnfs.remove(target_vnf)
    vnf_list[target_vnf.vnf_type].remove(target_vnf)
    return in_black_list


def SearchVNF(Network_Graph, source_vnf, target_vnf_type, vnf_list, sfc, BlackLists):
    cand_target_vnf = []
    for vnf in vnf_list[target_vnf_type]:
        if source_vnf != Network_Graph.SOURCE_VNF:
            if (vnf.prior_vnf == source_vnf or vnf.prior_vnf is None) \
                    and ExcessLatencyDemand(Network_Graph, source_vnf, vnf, sfc) \
                    and CostDemand(Network_Graph, source_vnf, vnf, sfc) \
                    and not InBlackLists(source_vnf, vnf, vnf_list, BlackLists):
                cand_target_vnf.append(vnf)
        else:
            if ExcessLatencyDemand(Network_Graph, source_vnf, vnf, sfc) \
                    and CostDemand(Network_Graph, source_vnf, vnf, sfc) \
                    and not InBlackLists(source_vnf, vnf, vnf_list, BlackLists):
                cand_target_vnf.append(vnf)
    return cand_target_vnf


def CalSFCReliaAndMin(sfc, vnf_list):
    relia_sfc = 1
    min_relia_vnf = 2
    min_relia_vnf_ins = None

    for vnf_type in vnf_list:
        for vnf in vnf_type:
            if sfc in vnf.ser_sfc_list:
                vnf_fail = vnf.single_fail + vnf.dep_fail
                # cal reliability under backups
                bvnfs_fail = 1
                for bvnf in vnf.bvnfs_list:
                    bvnfs_fail = bvnfs_fail * bvnf.single_fail
                relia_sfc = relia_sfc * (1 - vnf_fail * bvnfs_fail)
                # find vnf with the lowest reliability
                if (1 - vnf_fail * bvnfs_fail) < min_relia_vnf:
                    min_relia_vnf = (1 - vnf_fail * bvnfs_fail)
                    min_relia_vnf_ins = vnf

    return relia_sfc, min_relia_vnf_ins


def UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List):
    node_com_res = [0] * NODE_NUM
    for vnf_type in reversed(VNF_List):
        for vnf in reversed(vnf_type):
            if len(vnf.ser_sfc_list) <= 0:
                vnf_type.remove(vnf)
            else:
                node_com_res[vnf.pla_node] += vnf.vnf_computer_demand
    for bvnf_i in reversed(Backup_List):
        if bvnf_i.pla_node == -1 or bvnf_i.pla_node is None:
            Backup_List.remove(bvnf_i)
            bvnf_i.pro_vnf.bvnfs_list.remove(bvnf_i)
        else:
            node_com_res[bvnf_i.pla_node] += bvnf_i.vnf_computer_demand
    for node in range(0, NODE_NUM):
        Network_Graph.nodes_remain_computer[node] = Network_Graph.nodes_computer[node] - node_com_res[node]


def RVPP(Network_Graph, NODE_NUM, SFC_List, VNF_List, BlackLists, Backup_List, Served_SFC_List, BACKUP_MAX_NUM):
    Next_Frame_SFC = []
    # place vnfs for sfcs
    for s in SFC_List:
        print(COLORS.GREEN, "The RVPP starts to process sfc ", s.sfc_id, "===>", s.vnf_set, COLORS.RESET)
        s_ins_set = []  # vnf instance set for the sfc s
        source_vnf = Network_Graph.SOURCE_VNF  # source vnf instance

        for f in s.vnf_set:
            cand = SearchVNF(Network_Graph, source_vnf, f, VNF_List, s, BlackLists)
            if len(cand) > 0:
                cand[0].ser_sfc_list.append(s)
                s.vnf_ins_set.append(cand[0])
                if cand[0].prior_vnf is None:
                    if source_vnf != Network_Graph.SOURCE_VNF:
                        cand[0].prior_vnf = source_vnf
                        source_vnf.follow_vnfs.append(cand[0])
                source_vnf = cand[0]
            else:
                new_vnf_ins = VNF(f)
                cand_nodes_set = []
                for node in range(0, NODE_NUM):
                    new_vnf_ins.pla_node = node
                    if Network_Graph.nodes_remain_computer[node] >= new_vnf_ins.vnf_computer_demand \
                            and not InBlackLists(source_vnf, new_vnf_ins, VNF_List, BlackLists):
                        cand_nodes_set.append(node)

                if cand_nodes_set == []:
                    print(COLORS.RED, "can not provide service sfc ", s.sfc_id, COLORS.RESET)
                    for v in s.vnf_ins_set:
                        v.ser_sfc_list.remove(s)
                        for fol_v in reversed(v.follow_vnfs):
                            break_follow_relation = True
                            for served_sfc in v.ser_sfc_list:
                                if served_sfc in fol_v.ser_sfc_list:
                                    break_follow_relation = False
                            if break_follow_relation:
                                v.follow_vnfs.remove(fol_v)

                    s.vnf_ins_set = []
                    Next_Frame_SFC.append(s)
                    for s_vnf_ins in s_ins_set:
                        for vnf_type in reversed(VNF_List):
                            for vnf in reversed(vnf_type):
                                if vnf == s_vnf_ins:
                                    vnf_type.remove(s_vnf_ins)
                    break

                min_cost_com = Network_Graph.com_cost_matrix[source_vnf.pla_node][cand_nodes_set[0]]
                best_node = cand_nodes_set[0]
                for cand_node in cand_nodes_set:
                    if Network_Graph.com_cost_matrix[source_vnf.pla_node][cand_node] < min_cost_com:
                        best_node = cand_node

                new_vnf_ins.pla_node = best_node  # set edge node for new vnf instance
                VNF_List[f].append(new_vnf_ins)
                s_ins_set.append(new_vnf_ins)
                s.vnf_ins_set.append(new_vnf_ins)
                new_vnf_ins.ser_sfc_list.append(s)

                # update the preceding and following vnf list of a vnf
                if s.vnf_set.index(f) == 0:
                    new_vnf_ins.prior_vnf = None
                else:
                    new_vnf_ins.prior_vnf = source_vnf
                    source_vnf.follow_vnfs.append(new_vnf_ins)

                source_vnf = new_vnf_ins
            UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)

            # update sfcs
            for s_k in SFC_List:
                com_latency = 0
                pro_latency = 0
                for v_i in range(0, len(s_k.vnf_ins_set) - 1):
                    com_latency += Network_Graph.latency_matrix[s_k.vnf_ins_set[v_i].pla_node][
                        s_k.vnf_ins_set[v_i + 1].pla_node]
                    total_data_volume = 0
                    for sfc_j in s_k.vnf_ins_set[v_i].ser_sfc_list:
                        total_data_volume += sfc_j.data_volume
                    pro_latency += s_k.vnf_ins_set[v_i].max_load_latency * total_data_volume / s_k.vnf_ins_set[
                        v_i].max_load_data_vol
                s_k.actual_latency = pro_latency + com_latency

        UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)

        # cal sfc latency
        for s_k in SFC_List:
            com_latency = 0
            pro_latency = 0
            for v_i in range(0, len(s_k.vnf_ins_set) - 1):
                com_latency += Network_Graph.latency_matrix[s_k.vnf_ins_set[v_i].pla_node][
                    s_k.vnf_ins_set[v_i + 1].pla_node]
                total_data_volume = 0
                for sfc_j in s_k.vnf_ins_set[v_i].ser_sfc_list:
                    total_data_volume += sfc_j.data_volume
                pro_latency += s_k.vnf_ins_set[v_i].max_load_latency * total_data_volume / s_k.vnf_ins_set[
                    v_i].max_load_data_vol
            s_k.actual_latency = pro_latency + com_latency + s_k.plac_latency

    UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)
    # judge the latency of SFC
    for s_k in SFC_List:
        com_latency = 0
        pro_latency = 0
        for v_i in range(0, len(s_k.vnf_ins_set) - 1):
            com_latency += Network_Graph.latency_matrix[s_k.vnf_ins_set[v_i].pla_node][
                s_k.vnf_ins_set[v_i + 1].pla_node]
            # process latency
            total_data_volume = 0  # a vnf process data
            for sfc_j in s_k.vnf_ins_set[v_i].ser_sfc_list:
                total_data_volume += sfc_j.data_volume
            pro_latency += s_k.vnf_ins_set[v_i].max_load_latency * total_data_volume / s_k.vnf_ins_set[
                v_i].max_load_data_vol
        s_k.actual_latency = pro_latency + com_latency + s_k.plac_latency
        # add unmet sfc to next frame
        if (len(s_k.vnf_ins_set) == 0 or s_k.actual_latency > s_k.latency_com) \
                and s_k not in Next_Frame_SFC:
            Next_Frame_SFC.append(s_k)
            print(COLORS.RED, "add sfc to Next_Frame_SFC", s_k.sfc_id, ", because of latency constraints", COLORS.RESET)
            s_k.vnf_ins_set = []
            s_k.actual_latency = 0
            s_k.plac_latency = 0
    # judge the reliability of SFC
    for sfc in SFC_List:
        if sfc in Next_Frame_SFC:
            continue
        backup_List_cur = []
        relia_sfc, min_relia_vnf_ins = CalSFCReliaAndMin(sfc, VNF_List)

        while relia_sfc < sfc.relia_com:
            bvnf = BACKUPVNF(min_relia_vnf_ins.vnf_type)
            min_relia_vnf_ins.bvnfs_list.append(bvnf)
            backup_List_cur.append(bvnf)
            bvnf.pro_vnf = min_relia_vnf_ins

            bvnf.nodes_cost = np.zeros(NODE_NUM, dtype=int)
            for node_i in range(0, NODE_NUM):
                # BVNF pla cost
                pro_cost = bvnf.vnf_computer_demand * Network_Graph.unit_computer_cost
                all_data = 0
                for s_i in bvnf.pro_vnf.ser_sfc_list:
                    all_data += s_i.data_volume
                # BVNF comm cost
                com_cost = Network_Graph.com_cost_matrix[bvnf.pro_vnf.pla_node][
                               node_i] * all_data * Network_Graph.syn_cost_ratio
                bvnf.nodes_cost[node_i] = com_cost + pro_cost
            relia_sfc, min_relia_vnf_ins = CalSFCReliaAndMin(sfc, VNF_List)

        # backup_List_cur, backup with the node to place under GAP algorithm
        BackupPla(backup_List_cur, NODE_NUM, Network_Graph)
        sucess_backup = True
        for bvnf_i in reversed(backup_List_cur):
            if bvnf_i.pla_node == -1:
                sucess_backup = False
        # for a sfc, the number of backups cannot excedd max_num
        if len(backup_List_cur) > BACKUP_MAX_NUM:
            sucess_backup = False
        if sucess_backup:
            Backup_List.extend(backup_List_cur)
        else:
            for bvnf_i in backup_List_cur:
                bvnf_i.pro_vnf.bvnfs_list.remove(bvnf_i)
            backup_List_cur.clear()
        UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)

    # add sfc that unmet the reliability constraint after backups to Next_Frame_SFC
    for sfc in SFC_List:
        if sfc in Next_Frame_SFC:
            continue
        relia_sfc, min_relia_vnf_ins = CalSFCReliaAndMin(sfc, VNF_List)
        if relia_sfc < sfc.relia_com:
            print(COLORS.RED, "add sfc to Next_Frame_SFC", sfc.sfc_id, ", because of reliability constraints",
                  COLORS.RESET)
            Next_Frame_SFC.append(sfc)
            sfc.vnf_ins_set = []
            sfc.actual_latency = 0
            sfc.plac_latency = 0

    # organize the service list of vnfs for sfcs
    next_frame_sfc_diff = []
    for sfc in reversed(Next_Frame_SFC):
        if sfc.sfc_id not in next_frame_sfc_diff:
            next_frame_sfc_diff.append(sfc.sfc_id)
            sfc.actual_latency = 0
            sfc.vnf_ins_set = []
            sfc.actual_relia = 0
            sfc.plac_latency = 0
            for vnf_type in reversed(VNF_List):
                for vnf in reversed(vnf_type):
                    if sfc in vnf.ser_sfc_list:
                        vnf.ser_sfc_list.remove(sfc)
        else:
            Next_Frame_SFC.remove(sfc)

    # close backups of idle VNF
    for vnf_type in reversed(VNF_List):
        for vnf in reversed(vnf_type):
            if len(vnf.ser_sfc_list) <= 0:
                for bvnf_vnf in vnf.bvnfs_list:
                    Backup_List.remove(bvnf_vnf)
                vnf_type.remove(vnf)
    UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)
    return VNF_List, Next_Frame_SFC, Backup_List

"""
    for s in SFC_List:
        print("s id is ", s.sfc_id)
        print([v.pla_node for v in s.vnf_ins_set])

    for sfc in SFC_List:
        if sfc in Next_Frame_SFC:
            continue
        relia_sfc, min_relia_vnf_ins = CalSFCReliaAndMin(sfc, VNF_List)
        print("sfc.sfc_id, sfc_relia, sfc.relia_com", sfc.sfc_id, relia_sfc, sfc.relia_com)
"""

"""
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print(COLORS.MAGENTA, "vnf list", COLORS.RESET)
    for vnf_type in VNF_List:
        print(COLORS.MAGENTA, VNF_List.index(vnf_type), COLORS.RESET)
        for vnf in vnf_type:
            print("vnf.vnf_id, vnf_type, vnf.pla_node", vnf.vnf_id, vnf.vnf_type, vnf.pla_node)

    print(COLORS.MAGENTA, "bvnf list", COLORS.RESET)
    for bvnf in Backup_List:
        print("bvnf.bvnf_id, bvnf.vnf_type, bvnf.pla_node:", bvnf.bvnf_id, bvnf.vnf_type, bvnf.pla_node)

    print(COLORS.MAGENTA, "sfc list", COLORS.RESET)
    for s in SFC_List:
        print(s.sfc_id, "vnf ins is ", [x.vnf_id for x in s.vnf_ins_set])


"""