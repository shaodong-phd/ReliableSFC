#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :TSP.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/25 22:02
@IDE     :PyCharm  
@Note    :

"""
from RVPP import RVPP, CalSFCReliaAndMin, UpdateComputerResource
from SPEP import SPEP
from data_process.data import ReadSFC, ReadNetwork, COLORS
from entity import VNF
import copy
import time

TIME = 0  # the number of time slot e.g., 20 21 22.
TIME_FRAME = 0  # the length of time frame e.g., 5.
NODE_NUM = 11  # the number of edge node

VNF_TYPE_NUM = 7
BACKUP_MAX_NUM = 6
SFC_NUM = 11

Network_Graph = ReadNetwork()
SFC_List = ReadSFC(SFC_NUM)
VNF_List = [[] for _ in range(VNF_TYPE_NUM)]  # instance for eache VNF
BlackLists = []
Backup_List = []  # backup instance
Next_Frame_SFC_List = copy.copy(SFC_List)  # sfc provided at next time frame
Df_SFC_NUM = []  # attacked sfc id at each time slot
# ======================================


if __name__ == '__main__':
    # ========================================
    total_cost = 0  # total cost in multi-slot
    cost_list = []  # cost in each slot
    meet_require_sfc_length_list = []  # sfc meeting requirement
    start_time = time.time()  # record TTSP start time
    # ========================================
    for t in range(0, TIME):
        print(COLORS.BLUE, "The SPEP is executed to server SFC_List/Next_Frame_SFC_List "
                           "at the begin of time frame", t, COLORS.RESET)
        next_time_frame_sfcs = SPEP(Network_Graph, VNF_List,
                                    [sfc for sfc in SFC_List if sfc not in Next_Frame_SFC_List],
                                    BlackLists, Backup_List, t, Df_SFC_NUM)
        print(COLORS.RED, "time2 can not server sfc is ", len(next_time_frame_sfcs), COLORS.RESET)

        for next_time_sfc in next_time_frame_sfcs:
            if next_time_sfc not in Next_Frame_SFC_List:
                Next_Frame_SFC_List.append(next_time_sfc)
        UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)


        if t % TIME_FRAME == 0:
            # RVPP for Next_Frame_SFC_List
            print(COLORS.BLUE, "The RVPP is executed to server Next_Frame_SFC_List "
                               "at the begin of time frame", t, COLORS.RESET)
            VNF_List, Next_Frame_SFC_List, Backup_List = RVPP(Network_Graph, NODE_NUM,
                                                              Next_Frame_SFC_List, VNF_List,
                                                              BlackLists, Backup_List,
                                                              [sfc for sfc in SFC_List if
                                                               sfc not in Next_Frame_SFC_List], BACKUP_MAX_NUM)
            print(COLORS.RED, "time1 can not server sfc is ", len(Next_Frame_SFC_List), ", that is Next_Frame_SFC_List", COLORS.RESET)
            UpdateComputerResource(NODE_NUM, Network_Graph, VNF_List, Backup_List)

        # ================evaluate==================
        the_slot_cost = 0
        # placement cost in a time slot
        for vnf_type in VNF_List:
            for vnf in vnf_type:
                if vnf.pla_node != -1:
                    the_slot_cost = the_slot_cost + (vnf.vnf_computer_demand * Network_Graph.unit_computer_cost)
                    data_volumns = 0
                    for ser_sfc in vnf.ser_sfc_list:
                        data_volumns += ser_sfc.data_volume
                    for bvnf in vnf.bvnfs_list:
                        if bvnf.pla_node != -1:
                            the_slot_cost += \
                                (Network_Graph.com_cost_matrix[vnf.pla_node][bvnf.pla_node]
                                 * data_volumns * Network_Graph.syn_cost_ratio)
        # backups cost in a time slot
        for bvnf in Backup_List:
            if bvnf.pla_node != -1:
                the_slot_cost = the_slot_cost + (bvnf.vnf_computer_demand * Network_Graph.unit_computer_cost)
        # comm cost in a time slot
        for sfc in [sfc for sfc in SFC_List if sfc not in Next_Frame_SFC_List]:
            for vnf_index in range(0, len(sfc.vnf_ins_set)-1):
                vnf_i_ins = sfc.vnf_ins_set[vnf_index]
                vnf_j_ins = sfc.vnf_ins_set[vnf_index+1]
                the_slot_cost += \
                    (sfc.data_volume * Network_Graph.com_cost_matrix[vnf_i_ins.pla_node][vnf_j_ins.pla_node])

        # the number of sfc meeting requirement at each time slot
        meet_require_sfc_length_list.append(SFC_NUM - len(Next_Frame_SFC_List))
        print("the solt cost is ", the_slot_cost, "at time ", t)
        total_cost += the_slot_cost
        cost_list.append(the_slot_cost)

    end_time = time.time()  # TTSP end time

    # result of experiment
    for s in SFC_List:
        print("s id is ", s.sfc_id)
        print("s includes the vnf_type set is ", [vnf.vnf_type for vnf in s.vnf_ins_set])
        print("s includes the vnf_pla_node set is ", [vnf.pla_node for vnf in s.vnf_ins_set])

    for vnf_type in VNF_List:
        for vnf in vnf_type:
            print("vnf id and vnf type and vnf_pla are ", vnf.vnf_id, vnf.vnf_type, vnf.pla_node)

    for bvnf in Backup_List:
        print("bvnf id and bvnf type and bvnf_pla are ", bvnf.bvnf_id, bvnf.vnf_type, bvnf.pla_node)

    # ========================================

    print("cost_list:", cost_list)
    print("total_cost:", total_cost)
    print("average cost is ", total_cost/TIME)
    print("meet_require_sfc_length_list", meet_require_sfc_length_list)
    print("average meet_require_sfc_length", sum(meet_require_sfc_length_list)/(SFC_NUM*TIME) * SFC_NUM)
    print("the process time is ", end_time - start_time)
    print("Df_SFC_NUM", Df_SFC_NUM)
    total_df_sfc = 0
    max_df_sfc_num = -9999
    for df_sfc in Df_SFC_NUM:
        total_df_sfc += len(df_sfc)
        max_df_sfc_num = max(max_df_sfc_num, len(df_sfc))
    print("average ratio in multiple time slots ", total_df_sfc / (TIME*SFC_NUM))
    print("max ratio in multiple time slots ", max_df_sfc_num/SFC_NUM)

