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

class SliceStat(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Slice Statistics"
        self.parent.categories = ["VsData"]
        self.parent.dependencies = []
        self.parent.contributors = ["Sowwn (User) & AI Assistant"]
        self.parent.helpText = """
This module exports the slice numbers for each segment in a segmentation node to a CSV file.
See flow.md for more details on the process.
"""
        self.parent.acknowledgementText = """
This module was created based on the user's request.
"""

#
# SliceStatWidget
#

class SliceStatWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets
        self.logic = SliceStatLogic()

        #
        # Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # Reference Volume selector
        #
        self.referenceVolumeSelector = slicer.qMRMLNodeComboBox()
        self.referenceVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.referenceVolumeSelector.selectNodeUponCreation = True
        self.referenceVolumeSelector.addEnabled = False
        self.referenceVolumeSelector.removeEnabled = True
        self.referenceVolumeSelector.noneEnabled = True
        self.referenceVolumeSelector.showHidden = False
        self.referenceVolumeSelector.showChildNodeTypes = False
        self.referenceVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.referenceVolumeSelector.setToolTip("Pick the reference volume for geometry information. If not selected, the segmentation's source volume will be used.")
        parametersFormLayout.addRow("Source volume: ", self.referenceVolumeSelector)

        #
        # Segmentation selector
        #
        self.segmentationSelector = slicer.qMRMLNodeComboBox()
        self.segmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.segmentationSelector.selectNodeUponCreation = True
        self.segmentationSelector.addEnabled = False
        self.segmentationSelector.removeEnabled = False
        self.segmentationSelector.noneEnabled = False
        self.segmentationSelector.showHidden = False
        self.segmentationSelector.showChildNodeTypes = False
        self.segmentationSelector.setMRMLScene(slicer.mrmlScene)
        self.segmentationSelector.setToolTip("Pick the segmentation to analyze.")
        parametersFormLayout.addRow("Segmentation: ", self.segmentationSelector)

        #
        # Output file selector
        #
        self.outputFileContainer = qt.QWidget()
        self.outputFileLayout = qt.QHBoxLayout(self.outputFileContainer)
        self.outputFileLayout.setContentsMargins(0, 0, 0, 0)
        self.outputFileLineEdit = qt.QLineEdit()
        self.outputFileLineEdit.setToolTip("Path for the output CSV file. Click '...' to browse.")
        self.outputFileButton = qt.QPushButton("...")
        self.outputFileButton.toolTip = "Select output CSV file."
        self.outputFileLayout.addWidget(self.outputFileLineEdit)
        self.outputFileLayout.addWidget(self.outputFileButton)
        parametersFormLayout.addRow("Output File: ", self.outputFileContainer)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the analysis and save the CSV file."
        self.applyButton.enabled = False
        parametersFormLayout.addRow(self.applyButton)

        # Connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.segmentationSelector.currentNodeChanged.connect(self.onSegmentationChanged)
        self.referenceVolumeSelector.currentNodeChanged.connect(self.updateApplyButtonState)
        self.outputFileLineEdit.textChanged.connect(self.updateApplyButtonState)
        self.outputFileButton.connect('clicked(bool)', self.onSelectOutputFile)

        # Add vertical spacer
        self.layout.addStretch(1)

        self.onSegmentationChanged() # To set initial reference volume
        self.updateApplyButtonState()

    def onSegmentationChanged(self):
        segmentationNode = self.segmentationSelector.currentNode()
        if segmentationNode:
            # Automatically select the source volume of the segmentation as the default reference
            sourceVolume = self.logic.getReferenceVolume(segmentationNode)
            if sourceVolume:
                self.referenceVolumeSelector.setCurrentNode(sourceVolume)
        self.updateApplyButtonState()

    def onSelectOutputFile(self):
        saveDialog = qt.QFileDialog()
        saveDialog.setFileMode(qt.QFileDialog.AnyFile)
        saveDialog.setAcceptMode(qt.QFileDialog.AcceptSave)
        saveDialog.setNameFilter("CSV (*.csv)")
        if saveDialog.exec_():
            selectedFile = saveDialog.selectedFiles()[0]
            self.outputFileLineEdit.setText(selectedFile)

    def updateApplyButtonState(self):
        # A reference volume is required, either selected manually or implicitly from the segmentation
        hasReference = self.referenceVolumeSelector.currentNode() is not None or \
                       (self.segmentationSelector.currentNode() and self.logic.getReferenceVolume(self.segmentationSelector.currentNode()))

        canApply = self.segmentationSelector.currentNode() is not None and \
                   self.outputFileLineEdit.text != "" and \
                   hasReference
        self.applyButton.enabled = canApply

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        progressDialog = None
        try:
            segmentationNode = self.segmentationSelector.currentNode()
            referenceVolumeNode = self.referenceVolumeSelector.currentNode()
            outputPath = self.outputFileLineEdit.text

            # Auto-add extension if not present
            if not outputPath.lower().endswith(".csv"):
                outputPath += ".csv"

            # Show a progress dialog
            progressDialog = slicer.util.createProgressDialog(labelText="Analyzing segments...", windowTitle="Slice Statistics", maximum=0)

            self.logic.run(segmentationNode, outputPath, referenceVolumeNode)

            progressDialog.close()
            slicer.util.infoDisplay(f"Processing completed successfully! Results saved to:\n{outputPath}")

        except ValueError as e:
            if progressDialog:
                progressDialog.close()
            errorMessage = str(e)
            if "master volume" in errorMessage or "reference volume" in errorMessage:
                errorMessage = ("Could not determine the geometry for the segmentation.\n\n"
                                "Please either select a 'Reference Volume' manually in the module UI, "
                                "or go to the 'Segmentations' module and set the 'Source volume' for the selected segmentation.")
            slicer.util.errorDisplay(f"Processing failed: {errorMessage}")
        except Exception as e:
            if progressDialog:
                progressDialog.close()
            slicer.util.errorDisplay(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

    def onInstallDependencies(self):
        slicer.util.confirmOkCancelDisplay(
            "This will install the openpyxl package into Slicer's Python environment. "
            "Slicer may freeze during installation and will need to be restarted. Continue?",
            self.onConfirmInstall)

    def onConfirmInstall(self, confirmed):
        if confirmed:
            try:
                slicer.util.showStatusMessage("Installing package...")
                slicer.app.processEvents()
                slicer.util.pip_install("openpyxl")
                slicer.util.confirmOkCancelDisplay(
                    "Package installed successfully. Please restart Slicer for the changes to take effect.",
                    slicer.app.restart)
            except Exception as e:
                slicer.util.errorDisplay(f"Failed to install packages: {e}")


#
# SliceStatLogic
#

class SliceStatLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.
    """

    def run(self, segmentationNode, outputPath, referenceVolumeNode=None):
        """
        Run the actual algorithm
        """
        if not segmentationNode:
            raise ValueError("Invalid segmentation node provided.")
        if not outputPath:
            raise ValueError("Invalid output path provided.")

        logging.info('Processing started')

        # 1. Determine the reference volume and create a labelmap from the segmentation
        if not referenceVolumeNode:
            referenceVolumeNode = self.getReferenceVolume(segmentationNode)

        if not referenceVolumeNode:
            raise ValueError("A reference volume is required for geometry information.")

        labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "TempLabelmap")

        slicer.util.showStatusMessage("Exporting segmentation to labelmap...")
        slicer.app.processEvents()  # Update GUI

        if not slicer.vtkSlicerSegmentationsModuleLogic.ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelmapVolumeNode, referenceVolumeNode):
            slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
            raise RuntimeError("Failed to export segmentation to labelmap.")

        # 2. Convert labelmap to NumPy array
        slicer.util.showStatusMessage("Converting volume to array...")
        slicer.app.processEvents()  # Update GUI

        volumeArray = slicer.util.arrayFromVolume(labelmapVolumeNode)

        # 3. Get segments and iterate
        segmentation = segmentationNode.GetSegmentation()
        numberOfSegments = segmentation.GetNumberOfSegments()
        segmentResults = {}

        for i in range(numberOfSegments):
            segment = segmentation.GetNthSegment(i)
            segmentName = segment.GetName()

            # The labelmap value is the segment index + 1
            segmentLabelValue = i + 1

            slicer.util.showStatusMessage(f"Processing segment: {segmentName}...")
            slicer.app.processEvents()  # Update GUI

            # Find slices where this segment exists by checking along the slice axis (axis 0)
            slices_with_segment = np.any(volumeArray == segmentLabelValue, axis=(1, 2))
            slice_indices = np.where(slices_with_segment)[0]

            segmentResults[segmentName] = [int(idx) for idx in slice_indices]

        # Print results to Python console for immediate feedback
        print("\n--- Slice Statistics Results ---")
        for segmentName, sliceNumbers in segmentResults.items():
            sliceNumbersStr = ",".join(map(str, sliceNumbers)) if sliceNumbers else "None"
            print(f"  Segment '{segmentName}': Slices [{sliceNumbersStr}]")
        print("--------------------------------\n")

        # 4. Write results to CSV
        slicer.util.showStatusMessage(f"Writing {os.path.basename(outputPath)} file...")
        slicer.app.processEvents()  # Update GUI

        try:
            self.write_csv(segmentResults, outputPath)
        except IOError as e:
            slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
            raise IOError(f"Could not write to file {outputPath}: {e}")
        
        # 5. Clean up temporary nodes
        slicer.mrmlScene.RemoveNode(labelmapVolumeNode)

        logging.info('Processing completed')
        return True

    def write_csv(self, segmentResults, outputPath):
        with open(outputPath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['SegmentName', 'SliceNumbers'])
            for segmentName, sliceNumbers in segmentResults.items():
                sliceNumbersStr = ",".join(map(str, sliceNumbers))
                writer.writerow([segmentName, sliceNumbersStr])

    def getReferenceVolume(self, segmentationNode):
        """
        Gets the reference volume used for the segmentation's geometry.
        """
        sourceVolumeID = segmentationNode.GetNodeReferenceID(slicer.vtkMRMLSegmentationNode.GetReferenceImageGeometryReferenceRole())
        if sourceVolumeID:
            return slicer.mrmlScene.GetNodeByID(sourceVolumeID)
        
        # Fallback for older Slicer versions or if not explicitly set
        masterVolumeNode = getattr(segmentationNode, 'GetMasterVolumeNode', lambda: None)()
        if masterVolumeNode:
            return masterVolumeNode

        return None
