#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project :dependent_failure 
@File    :sfc.py
@Author  :LuckyD0g_shaodong
@Date    :2023/11/10 16:59
@IDE     :PyCharm  
@Note    :
"""


class SFC:
    def __init__(self, sfc_id=0, vnf_set=[]):
        self.sfc_id = sfc_id
        self.vnf_set = vnf_set  # VNFs consist of SFC
        self.latency_com = 0
        self.relia_com = 0
        self.data_volume = 0

        self.vnf_ins_set = []
        self.actual_latency = 0
        self.actual_relia = 0
        self.plac_latency = 0


