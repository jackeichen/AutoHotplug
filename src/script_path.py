#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#############################################################################
#Author: Gao Zhihua
#Date: 2021/11/28
#Description: 
# script_path.py
# This is script path declare file, changed by this tool maintainer.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# personal.
#
# Author(s): Eric Gao <gaozh3@163.com>
############################################################################# 
import os
import sys
##
src_path = os.path.dirname(os.path.abspath(__file__))
tool_top_path = os.path.dirname(src_path)
##
tools_path = os.path.join(src_path, 'tools')
devcon_path = os.path.join(tools_path, 'devcon.exe')
vdbench_tool_path = os.path.join(tools_path, 'vdbench50407','vdbench')
lspci_win_path = os.path.join(tools_path,'pciutils-3.5.5-win32','lspci.exe')
setpci_win_path = os.path.join(tools_path,'pciutils-3.5.5-win32','setpci.exe')
##
vdbench_path = os.path.join(src_path,'vdbench')
vdbench_para_file_path = os.path.join(vdbench_path, "para_files")
## config file
config_file_path = os.path.join(tool_top_path,'config','config.yml')
##
LOGS_path = os.path.join(tool_top_path,"LOGS")
##
temp_path = os.path.join(tool_top_path,"Temp")
