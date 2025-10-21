#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :auxiliary_graph.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/14 13:47
@IDE     :PyCharm  
@Note    :
"""
from data_process.data import COLORS
from entity.vnf import VNF

class AUXILIARYGRAPH:
    def  __init__(self):
        self.adjacency_list = {}
        self.max_edge_weight = -999999
        self.max_edge = None
        self.pass_max_edge_sfc = []
        self.max_edge_svnf = None
        self.max_edge_block_error_p = []

    def add_vertex(self, vertex):
        # add vertex
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []

    def add_edge(self, start_vertex, end_vertex, weight):
        # add edge with weights
        self.add_vertex(start_vertex)
        self.add_vertex(end_vertex)
        self.adjacency_list[start_vertex].append((end_vertex, weight))

    def display(self):
        for v in self.adjacency_list:
            print("v:", v, "=>", self.adjacency_list[v])

def BuildAuxiliaryGraph(svnf_pla_lay, vnf_list, error_paths):
    # error_paths[i] ith error pair
    # build eff_paths, valid path to place svnf
    eff_paths = []
    # error_p error path consist of VNF instances
    for error_p in error_paths:
        lay = 0
        path = []
        for vnf_i in range(0, len(error_p)-1):
            vnf_pro_lay = ReadProDelay(vnf_i)
            vnf_com_lay = ReadComDelay(vnf_i, vnf_i+1)
            lay = lay + vnf_pro_lay + vnf_com_lay
            if lay >= svnf_pla_lay:
                for eff_i in range(vnf_i+1, len(error_p)):
                    path.append(error_p[eff_i])
                break
        eff_paths.append(path)

    cant_protect_rvnf = []
    for eff_p_i in range(0, len(eff_paths)):
        if len(eff_paths[eff_p_i]) < 2:
            rvnf = error_paths[eff_p_i][-1]
            cant_protect_rvnf.append(rvnf)

    for eff_p in reversed(eff_paths):
        if len(eff_p) > 0 and eff_p[-1] in cant_protect_rvnf:
            eff_p.clear()

    print(COLORS.MAGENTA, "for eff_p in eff_paths", COLORS.RESET)
    for i in range(0, len(eff_paths)):
        print("eff_p id is ", i, "and it includes ", [x.vnf_id for x in eff_paths[i]])

    pro_graph = AUXILIARYGRAPH()
    for eff_p_i in range(0, len(eff_paths)):
        for p_v_i in range(0, len(eff_paths[eff_p_i])-1):
            pro_graph.add_edge(eff_paths[eff_p_i][p_v_i].vnf_id,
                               eff_paths[eff_p_i][p_v_i+1].vnf_id,
                                eff_p_i)
    # pro_graph.display()
    return pro_graph

# find the path to svnf
def HavePath(pvnf, rvnf, path=[]):
    path = path + [pvnf]
    if pvnf == rvnf:
        return path
    for fol_vnf in pvnf.follow_vnfs:
        if fol_vnf not in path and fol_vnf.vnf_type != 0:
            new_path = HavePath(fol_vnf, rvnf, path)
            if new_path:
                return new_path
    return None

# detect path between PVNF and RVNF
def DetectErrorPaths(vnf_list, df_fail_real):
    error_paths = []
    for df_pair in df_fail_real:
        for pvnf in vnf_list[df_pair[1]]:
            if pvnf.pla_node == df_pair[0]:
                for rvnf in vnf_list[df_pair[3]]:
                    if rvnf.pla_node == df_pair[2]:
                        path = HavePath(pvnf, rvnf)
                        if path:
                            error_paths.append(path)
                            rvnf.dep_fail = 1 - rvnf.single_fail
    return error_paths

def CountHavePath(pvnf, rvnf, path=[]):
    path = path + [pvnf]
    if pvnf == rvnf:
        return path

    for fol_vnf in pvnf.follow_vnfs:
        if fol_vnf not in path:
            new_path = CountHavePath(fol_vnf, rvnf, path)
            if new_path:
                return new_path
    return None

def CountErrorPathsNum(vnf_list, df_fail_real):
    error_paths = []
    for df_pair in df_fail_real:
        for pvnf in vnf_list[df_pair[1]]:
            if pvnf.pla_node == df_pair[0]:
                for rvnf in vnf_list[df_pair[3]]:
                    if rvnf.pla_node == df_pair[2]:
                        path = CountHavePath(pvnf, rvnf)
                        if path:
                            error_paths.append(path)
    return error_paths
