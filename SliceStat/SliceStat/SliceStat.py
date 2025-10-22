import os
import vtk
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import logging
import csv
import numpy as np
import ctk
import qt

#
# SliceStat
#
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Slice Statistics"
        self.parent.categories = ["VsData"]
        self.parent.dependencies = []
        self.parent.contributors = ["Sowwn (User) & AI Assistant"]
