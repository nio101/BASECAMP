#!/usr/bin/env python3
# coding: utf-8

"""
BC_operator - handles vocal interactions and presence/absence detection
and applicable corresponding rules/actions

- depends on other services: logbook, PIR_scanner, BT_scanner
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

# =======================================================
# Imports

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import BC_commons

print("hello from test")
