#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :SPEP.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/13 23:53
@IDE     :PyCharm  
@Note    :
"""

import numpy as np

from RVPP import CalSFCReliaAndMin, UpdateComputerResource
from auxiliary_graph import AUXILIARYGRAPH, BuildAuxiliaryGraph, DetectErrorPaths, \
    CountErrorPathsNum
from data_process.data import COLORS, ReadDF
from entity.network import NETWORK
from entity.sfc import SFC
from entity.vnf import VNF, SearchVNFById


NODE_NUM = 11
VNF_TYPE_NUM = 7
df_fail_real = ReadDF()  # read dependent failure


def SPEP(Network_Graph, vnf_list, SFC_List, BlackLists, Backup_List, t, Df_SFC_NUM):
    next_time_frame_sfcs = []  # sfc will be process next time frame
    BlackLists.extend(df_fail_real[t-1]) if t >= 1 else None
    dp_sfc_id_set = []  # sfc set experiencing dependent failure

    # print(COLORS.RED, "df_fail_real:", df_fail_real, COLORS.RESET)
    # print(COLORS.RED, "dependent failure pairs is ", COLORS.RESET)
    # for df in df_fail_real[0]:
    #   print(df)

    while True:
        error_paths = DetectErrorPaths(vnf_list, df_fail_real[t - 1])
        print("error path")
        for e_p in error_paths:
            print("error path id is ", error_paths.index(e_p), [x.vnf_id for x in e_p])
        # ==================================================
        count_error_paths = CountErrorPathsNum(vnf_list, df_fail_real[t - 1])
        for e_p in count_error_paths:
            rvnf = e_p[-1]
            for s in rvnf.ser_sfc_list:
                if s.sfc_id not in dp_sfc_id_set:
                    dp_sfc_id_set.append(s.sfc_id)
        # ==================================================
        # valid place svnf
        AG = BuildAuxiliaryGraph(svnf_pla_lay=30, vnf_list=vnf_list, error_paths=error_paths)

        # cal weights to AG_
        AG_ = AUXILIARYGRAPH()
        for vnf_id, fow_vnf_list in AG.adjacency_list.items():
            AG_.add_vertex(vnf_id)
            fow_vnfs_id_set = []
            for fow_vnf in fow_vnf_list:
                if fow_vnf[0] not in fow_vnfs_id_set:
                    fow_vnfs_id_set.append(fow_vnf[0])

            # cal svnf benefit
            for fow_vnf_id in fow_vnfs_id_set:
                positive_w = 0
                err_p_ids = []
                for fow_vnf in fow_vnf_list:
                    if fow_vnf[0] == fow_vnf_id:
                        err_p_ids.append(fow_vnf[1])

                # Part01: positive weights
                for err_p_id in err_p_ids:
                    for rvnf_ser_s in error_paths[err_p_id][-1].ser_sfc_list:
                        s_relia, min_relia_vnf = CalSFCReliaAndMin(rvnf_ser_s, vnf_list)
                        if s_relia < rvnf_ser_s.relia_com:
                            positive_w += 1

                # Part02: negtive weights
                min_com_lay_node_id = None
                min_com_lay = 999999
                svnf = VNF(0)

                for node_id in range(0, NODE_NUM):
                    if SearchVNFById(vnf_list, vnf_id) is not None and SearchVNFById(vnf_list, fow_vnf_id) is not None:
                        node_jd = SearchVNFById(vnf_list, vnf_id).pla_node
                        node_kd = SearchVNFById(vnf_list, fow_vnf_id).pla_node
                    else:
                        print(COLORS.RED, "Can not find the vnf in vnf_list!", COLORS.RESET)

                    incre_com_lay = Network_Graph.latency_matrix[node_jd][node_id] \
                                    + Network_Graph.latency_matrix[node_id][node_kd]
                    if Network_Graph.nodes_remain_computer[node_id] >= svnf.vnf_computer_demand \
                            and incre_com_lay < min_com_lay:
                        min_com_lay = incre_com_lay
                        min_com_lay_node_id = node_id

                # a node for svnf
                if min_com_lay_node_id is None:
                    print(COLORS.RED, "can not find the node to place the svnf, bewteen vnf",
                          vnf_id, "and ", fow_vnf_id,
                          COLORS.RESET)
                    break
                svnf.pla_node = min_com_lay_node_id
                svnf.prior_vnf = SearchVNFById(vnf_list, vnf_id)
                svnf.follow_vnfs.append(SearchVNFById(vnf_list, fow_vnf_id))

                # sfc passing vnf and folvnf
                pass_edge_sfc = []
                # cal svnf process delay
                total_data = 0
                for s in SFC_List:
                    vnf_id_vnf_ins = SearchVNFById(vnf_list, vnf_id)
                    vnf_id_fol_vnf_ins = SearchVNFById(vnf_list, fow_vnf_id)
                    if s in vnf_id_vnf_ins.ser_sfc_list \
                            and s in vnf_id_fol_vnf_ins.ser_sfc_list \
                            and s.vnf_ins_set.index(vnf_id_fol_vnf_ins) - s.vnf_ins_set.index(vnf_id_vnf_ins) == 1:
                        total_data += s.data_volume
                    pass_edge_sfc.append(s)
                svnf_pro_lay = total_data * svnf.max_load_latency / svnf.max_load_data_vol

                # sfcs unmeet delay constraints
                negtive_w = 0
                for s in SFC_List:
                    vnf_id_vnf_ins = SearchVNFById(vnf_list, vnf_id)
                    vnf_id_fol_vnf_ins = SearchVNFById(vnf_list, fow_vnf_id)

                    if s in vnf_id_vnf_ins.ser_sfc_list \
                            and s in vnf_id_fol_vnf_ins.ser_sfc_list \
                            and s.vnf_ins_set.index(vnf_id_fol_vnf_ins) - s.vnf_ins_set.index(vnf_id_vnf_ins) == 1:
                        if min_com_lay + svnf_pro_lay + s.actual_latency > s.latency_com:
                            negtive_w += 1

                # add weights for edges
                AG_.add_edge(vnf_id, fow_vnf_id, positive_w - negtive_w)
                if positive_w - negtive_w > AG_.max_edge_weight:
                    AG_.max_edge_weight = positive_w - negtive_w
                    AG_.max_edge = (vnf_id, fow_vnf_id)
                    AG_.pass_max_edge_sfc = pass_edge_sfc
                    AG_.max_edge_svnf = svnf
                    AG_.max_edge_block_error_p = err_p_ids

        # print(COLORS.MAGENTA, "the number of sfc meeting reliability constraint:", COLORS.RESET)
        meet_relia_sfc_num = 0
        for s in SFC_List:
            s_relia, min_relia_vnf = CalSFCReliaAndMin(s, vnf_list)
            if s_relia >= s.relia_com:
                meet_relia_sfc_num += 1

        if meet_relia_sfc_num < len(SFC_List) and AG_.max_edge_weight > 0:
            print(COLORS.GREEN, "place svnf: ", COLORS.RESET)
            for blo_error_p_id in AG_.max_edge_block_error_p:
                # recover the reliability of RVNF
                error_paths[blo_error_p_id][-1].dep_fail = 0
                error_paths[blo_error_p_id] = []

            # update the preceding vnf and following vnf of svnf instance
            AG_.max_edge_svnf.prior_vnf.follow_vnfs.append(AG_.max_edge_svnf)
            AG_.max_edge_svnf.prior_vnf.follow_vnfs.remove(AG_.max_edge_svnf.follow_vnfs[0])
            AG_.max_edge_svnf.follow_vnfs[0].prior_vnf = AG_.max_edge_svnf
            # add svnf into VNF_List
            vnf_list[AG_.max_edge_svnf.vnf_type].append(AG_.max_edge_svnf)
            svnf_prior_vnf = AG_.max_edge_svnf.prior_vnf
            svnf_fow_vnf = AG_.max_edge_svnf.follow_vnfs[0]
            for s in SFC_List:
                if s in svnf_prior_vnf.ser_sfc_list \
                        and s in svnf_fow_vnf.ser_sfc_list:
                    s.vnf_ins_set.insert(s.vnf_ins_set.index(svnf_fow_vnf), AG_.max_edge_svnf)
                    AG_.max_edge_svnf.ser_sfc_list.append(s)

            UpdateComputerResource(NODE_NUM, Network_Graph, vnf_list, Backup_List)
            AG_.max_edge_weight = -999999
            AG_.max_edge = None
            AG_.pass_max_edge_sfc = []
            AG_.max_edge_svnf = None
            AG_.max_edge_block_error_p = []

            # evl sfc unmeeting latency constraints
            for s in reversed(SFC_List):
                lay = 0
                for v_ins in s.vnf_ins_set:
                    total_data = 0
                    for v_ins_ser_s in v_ins.ser_sfc_list:
                        total_data += v_ins_ser_s.data_volume
                    pro_lay = total_data * v_ins.max_load_latency / v_ins.max_load_data_vol
                    lay = lay + pro_lay
                for v_i in range(0, len(s.vnf_ins_set) - 1):
                    node_i = s.vnf_ins_set[v_i].pla_node
                    node_j = s.vnf_ins_set[v_i + 1].pla_node
                    com_lay = Network_Graph.latency_matrix[node_i][node_j]
                    lay = lay + com_lay

                # evl latency of sfc
                if lay > s.latency_com:
                    print(COLORS.RED, "del sfc ", s, COLORS.RESET)
                    for v_ins in s.vnf_ins_set:
                        del v_ins.ser_sfc_list[s]
                    s.vnf_ins_set = []
                    del SFC_List[s]
                    next_time_frame_sfcs.append(s)
        else:
            print("AG_.max_edge_weight is ", AG_.max_edge_weight, "meet_relia_sfc_num", meet_relia_sfc_num,
                  "len(SFC_List)", len(SFC_List))
            break

    UpdateComputerResource(NODE_NUM, Network_Graph, vnf_list, Backup_List)
    # update sfc vnf
    for sfc in reversed(SFC_List):
        if sfc in next_time_frame_sfcs:
            continue
        relia_sfc, min_relia_vnf_ins = CalSFCReliaAndMin(sfc, vnf_list)
        if relia_sfc < sfc.relia_com:
            print(COLORS.RED, "add sfc to Next_Frame_SFC", sfc.sfc_id, ", because of reliability constraints",
                  COLORS.RESET)
            print("relia_sfc, sfc.relia_com: ", relia_sfc, sfc.relia_com)
            next_time_frame_sfcs.append(sfc)
            sfc.vnf_ins_set = []
            sfc.actual_latency = 0
            sfc.plac_latency = 0
    next_frame_sfc_diff = []
    for sfc in reversed(next_time_frame_sfcs):
        if sfc.sfc_id not in next_frame_sfc_diff:
            next_frame_sfc_diff.append(sfc.sfc_id)
            sfc.actual_latency = 0
            sfc.vnf_ins_set = []
            sfc.actual_relia = 0
            sfc.plac_latency = 0
            for vnf_type in reversed(vnf_list):
                for vnf in reversed(vnf_type):
                    if sfc in vnf.ser_sfc_list:
                        vnf.ser_sfc_list.remove(sfc)
        else:
            next_time_frame_sfcs.remove(sfc)
    for vnf_type in reversed(vnf_list):
        for vnf in reversed(vnf_type):
            if len(vnf.ser_sfc_list) <= 0:
                for bvnf_vnf in vnf.bvnfs_list:
                    Backup_List.remove(bvnf_vnf)
                vnf_type.remove(vnf)

    UpdateComputerResource(NODE_NUM, Network_Graph, vnf_list, Backup_List)
    Df_SFC_NUM.append(dp_sfc_id_set)
    return next_time_frame_sfcs


if __name__ == '__main__':
    print()