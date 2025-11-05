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
        # Single Sample Area
        #
        singleSampleCollapsibleButton = ctk.ctkCollapsibleButton()
        singleSampleCollapsibleButton.text = "Single Sample"
        self.layout.addWidget(singleSampleCollapsibleButton)

        # Layout within the collapsible button
        singleSampleFormLayout = qt.QFormLayout(singleSampleCollapsibleButton)

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
        singleSampleFormLayout.addRow("Source volume: ", self.referenceVolumeSelector)

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
        singleSampleFormLayout.addRow("Segmentation: ", self.segmentationSelector)

        #
        # Output file selector
        #
        self.outputFileContainer = qt.QWidget()
        self.outputFileLayout = qt.QHBoxLayout(self.outputFileContainer)
        self.outputFileLayout.setContentsMargins(0, 0, 0, 0)
        self.outputFileLineEdit = qt.QLineEdit()
        self.outputFileLineEdit.setToolTip("Path for the output CSV file. Click '...' to browse. If file exists, data will be appended.")
        self.outputFileButton = qt.QPushButton("...")
        self.outputFileButton.toolTip = "Select output CSV file."
        self.outputFileLayout.addWidget(self.outputFileLineEdit)
        self.outputFileLayout.addWidget(self.outputFileButton)
        singleSampleFormLayout.addRow("Output File: ", self.outputFileContainer)

        #
        # Apply Button for Single Sample
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the analysis and save the CSV file."
        self.applyButton.enabled = False
        singleSampleFormLayout.addRow(self.applyButton)

        #
        # Multi Sample Area
        #
        multiSampleCollapsibleButton = ctk.ctkCollapsibleButton()
        multiSampleCollapsibleButton.text = "Multi Sample"
        self.layout.addWidget(multiSampleCollapsibleButton)

        # Layout within the collapsible button
        multiSampleFormLayout = qt.QFormLayout(multiSampleCollapsibleButton)

        # Info label for Multi Sample
        multiSampleInfoLabel = qt.QLabel()
        multiSampleInfoLabel.setText("Automatically processes all volumes (.nii.gz) with their matching segments (.seg.nrrd or (final).seg.nrrd)")
        multiSampleInfoLabel.setWordWrap(True)
        multiSampleFormLayout.addRow("", multiSampleInfoLabel)

        #
        # Output file selector for Multi Sample
        #
        self.multiOutputFileContainer = qt.QWidget()
        self.multiOutputFileLayout = qt.QHBoxLayout(self.multiOutputFileContainer)
        self.multiOutputFileLayout.setContentsMargins(0, 0, 0, 0)
        self.multiOutputFileLineEdit = qt.QLineEdit()
        self.multiOutputFileLineEdit.setToolTip("Path for the output CSV file. Click '...' to browse. If file exists, data will be appended.")
        self.multiOutputFileButton = qt.QPushButton("...")
        self.multiOutputFileButton.toolTip = "Select output CSV file."
        self.multiOutputFileLayout.addWidget(self.multiOutputFileLineEdit)
        self.multiOutputFileLayout.addWidget(self.multiOutputFileButton)
        multiSampleFormLayout.addRow("Output File: ", self.multiOutputFileContainer)

        #
        # Apply Button for Multi Sample
        #
        self.applyMultiButton = qt.QPushButton("Apply")
        self.applyMultiButton.toolTip = "Export all volumes in the scene with their matching segments. Volumes without matching segments will be shown in warnings."
        self.applyMultiButton.enabled = False
        multiSampleFormLayout.addRow(self.applyMultiButton)

        # Connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.applyMultiButton.connect('clicked(bool)', self.onApplyMultiButton)
        self.segmentationSelector.currentNodeChanged.connect(self.onSegmentationChanged)
        self.referenceVolumeSelector.currentNodeChanged.connect(self.updateApplyButtonState)
        self.outputFileLineEdit.textChanged.connect(self.updateApplyButtonState)
        self.outputFileButton.connect('clicked(bool)', self.onSelectOutputFile)
        self.multiOutputFileLineEdit.textChanged.connect(self.updateMultiApplyButtonState)
        self.multiOutputFileButton.connect('clicked(bool)', self.onSelectMultiOutputFile)

        # Add vertical spacer
        self.layout.addStretch(1)

        self.onSegmentationChanged() # To set initial reference volume
        self.updateApplyButtonState()
        self.updateMultiApplyButtonState()

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

    def onSelectMultiOutputFile(self):
        saveDialog = qt.QFileDialog()
        saveDialog.setFileMode(qt.QFileDialog.AnyFile)
        saveDialog.setAcceptMode(qt.QFileDialog.AcceptSave)
        saveDialog.setNameFilter("CSV (*.csv)")
        if saveDialog.exec_():
            selectedFile = saveDialog.selectedFiles()[0]
            self.multiOutputFileLineEdit.setText(selectedFile)

    def updateApplyButtonState(self):
        # A reference volume is required, either selected manually or implicitly from the segmentation
        hasReference = self.referenceVolumeSelector.currentNode() is not None or \
                       (self.segmentationSelector.currentNode() and self.logic.getReferenceVolume(self.segmentationSelector.currentNode()))

        canApply = self.segmentationSelector.currentNode() is not None and \
                   self.outputFileLineEdit.text != "" and \
                   hasReference
        self.applyButton.enabled = canApply

    def updateMultiApplyButtonState(self):
        canApply = self.multiOutputFileLineEdit.text != ""
        self.applyMultiButton.enabled = canApply

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button for Single Sample.
        """
        progressDialog = None
        try:
            segmentationNode = self.segmentationSelector.currentNode()
            referenceVolumeNode = self.referenceVolumeSelector.currentNode()
            outputPath = self.outputFileLineEdit.text

            # Auto-add extension if not present
            if not outputPath.lower().endswith(".csv"):
                outputPath += ".csv"

            # Determine append mode based on file existence
            appendMode = os.path.exists(outputPath)

            # Show a progress dialog
            progressDialog = slicer.util.createProgressDialog(labelText="Analyzing segments...", windowTitle="Slice Statistics", maximum=0)

            self.logic.run(segmentationNode, outputPath, referenceVolumeNode, appendMode)

            progressDialog.close()
            mode = "appended to" if appendMode else "saved to"
            slicer.util.infoDisplay(f"Processing completed successfully! Results {mode}:\n{outputPath}")

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

    def onApplyMultiButton(self):
        """
        Run processing when user clicks "Apply" button for Multi Sample.
        """
        progressDialog = None
        try:
            outputPath = self.multiOutputFileLineEdit.text

            # Auto-add extension if not present
            if not outputPath.lower().endswith(".csv"):
                outputPath += ".csv"

            # Determine append mode based on file existence
            appendMode = os.path.exists(outputPath)

            # Show a progress dialog
            progressDialog = slicer.util.createProgressDialog(labelText="Analyzing all volumes...", windowTitle="Slice Statistics", maximum=0)

            warnings = self.logic.run_export_all(None, outputPath, appendMode)
            
            progressDialog.close()
            mode = "appended to" if appendMode else "saved to"
            message = f"Processing completed successfully! Results {mode}:\n{outputPath}"
            if warnings:
                message += f"\n\nWarnings:\n" + "\n".join(warnings)
                slicer.util.warningDisplay(message, windowTitle="Slice Statistics")
            else:
                slicer.util.infoDisplay(message)

        except ValueError as e:
            if progressDialog:
                progressDialog.close()
            errorMessage = str(e)
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

    def run(self, segmentationNode, outputPath, referenceVolumeNode=None, appendMode=False):
        """
        Run the actual algorithm for Single Sample mode
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

        # Get the source volume name for ID
        sourceVolumeName = referenceVolumeNode.GetName()

        segmentResults = self.process_segmentation(segmentationNode, referenceVolumeNode)

        # 4. Write results to CSV
        slicer.util.showStatusMessage(f"Writing {os.path.basename(outputPath)} file...")
        slicer.app.processEvents()  # Update GUI

        try:
            self.write_csv(segmentResults, outputPath, appendMode, sourceVolumeName)
        except IOError as e:
            raise IOError(f"Could not write to file {outputPath}: {e}")

        logging.info('Processing completed')
        return True

    def process_segmentation(self, segmentationNode, referenceVolumeNode):
        """
        Process a segmentation node and return segment results
        """
        # Do not rely on visibility-dependent merged labelmaps.
        # Process each segment independently to avoid label value mismatches.
        slicer.util.showStatusMessage("Converting volume to array...")
        slicer.app.processEvents()  # Update GUI

        segmentation = segmentationNode.GetSegmentation()
        numberOfSegments = segmentation.GetNumberOfSegments()
        segmentResults = {}

        for i in range(numberOfSegments):
            segment = segmentation.GetNthSegment(i)
            segmentName = segment.GetName()
            segmentId = segmentation.GetNthSegmentID(i)

            slicer.util.showStatusMessage(f"Processing segment: {segmentName}...")
            slicer.app.processEvents()  # Update GUI

            # Preferred: get binary labelmap array directly; fallback to single-segment export
            binaryArray = None
            try:
                binaryArray = slicer.util.arrayFromSegmentBinaryLabelmap(segmentationNode, segmentId, referenceVolumeNode)
            except Exception:
                binaryArray = None

            if binaryArray is None:
                tempLabelmap = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "TempLabelmap_Single")
                try:
                    ids = vtk.vtkStringArray()
                    ids.InsertNextValue(segmentId)
                    ok = slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsToLabelmapNode(
                        segmentationNode,
                        ids,
                        tempLabelmap,
                        referenceVolumeNode
                    )
                    if not ok:
                        raise RuntimeError("Failed to export single segment to labelmap.")
                    tempArray = slicer.util.arrayFromVolume(tempLabelmap)
                    binaryArray = (tempArray > 0)
                finally:
                    slicer.mrmlScene.RemoveNode(tempLabelmap)

            # Compute slice indices along axis 0 where any voxel is present
            presence = (binaryArray > 0) if binaryArray.dtype != np.bool_ else binaryArray
            slices_with_segment = np.any(presence, axis=(1, 2))
            slice_indices = np.where(slices_with_segment)[0]

            segmentResults[segmentName] = [int(idx) for idx in slice_indices]

        # Print results to Python console for immediate feedback
        print("\n--- Slice Statistics Results ---")
        for segmentName, sliceNumbers in segmentResults.items():
            sliceNumbersStr = ",".join(map(str, sliceNumbers)) if sliceNumbers else "None"
            print(f"  Segment '{segmentName}': Slices [{sliceNumbersStr}]")
        print("--------------------------------\n")

        return segmentResults

    def write_csv(self, segmentResults, outputPath, appendMode=False, sourceVolumeName=None):
        """
        Write segment results to CSV file for Single Sample mode
        ID column: only first row has value (source volume name), other rows are empty but keep comma
        """
        file_exists = os.path.exists(outputPath) and appendMode

        with open(outputPath, 'a' if appendMode else 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write header if not appending or if file doesn't exist
            if not file_exists:
                writer.writerow(['ID', 'SegmentName', 'SliceNumbers', 'SliceCount'])
            
            # Write data rows - only first row has ID, others have empty ID
            first_segment = True
            for segmentName, sliceNumbers in segmentResults.items():
                if first_segment:
                    # First row: use source volume name as ID
                    segmentId = sourceVolumeName if sourceVolumeName else segmentName
                    # Add tab prefix to prevent Excel SYLK format detection
                    if segmentId and not segmentId.startswith('\t'):
                        segmentId = '\t' + str(segmentId)
                    first_segment = False
                else:
                    # Other rows: empty ID but keep comma
                    segmentId = ""
                
                sliceNumbersStr = ",".join(map(str, sliceNumbers)) if sliceNumbers else ""
                sliceCount = len(sliceNumbers) if sliceNumbers else 0
                writer.writerow([segmentId, segmentName, sliceNumbersStr, sliceCount])

    def run_export_all(self, segmentationNode, outputPath, appendMode=False):
        """
        Export all volumes in the scene that match segment IDs (Multi Sample mode)
        Automatically matches volumes (.nii.gz) with corresponding segments (.seg.nrrd or .seg[final].nrrd)
        segmentationNode parameter is not used anymore as auto-matching is done internally
        """
        if not outputPath:
            raise ValueError("Invalid output path provided.")

        logging.info('Export all mode started')

        warnings = []
        allResults = {}

        # Get all volume nodes in the scene
        volumeNodes = slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")
        
        # Get all segmentation nodes in the scene
        segmentationNodes = slicer.util.getNodesByClass("vtkMRMLSegmentationNode")
        
        # Process each volume
        for volumeNode in volumeNodes:
            volumeName = volumeNode.GetName()
            
            # Try to find matching segmentation for this volume
            matchingSegNode = None
            
            # Get the file path from storage node to extract original filename
            volumeBaseName = None
            storageNode = volumeNode.GetStorageNode()
            if storageNode:
                filePath = storageNode.GetFileName()
                if filePath:
                    # Extract base name from file path
                    fileName = os.path.basename(filePath)
                    # Remove extensions: .nii.gz or .nii
                    if fileName.endswith('.nii.gz'):
                        volumeBaseName = fileName[:-7]
                    elif fileName.endswith('.nii'):
                        volumeBaseName = fileName[:-4]
                    else:
                        volumeBaseName = fileName
            
            # Fallback to node name if no file path available
            if not volumeBaseName:
                volumeBaseName = volumeName
            
            # Try to find matching segmentation by prefix of the source base name
            # Collect all candidates that start with the volumeBaseName (allow arbitrary suffix),
            # prefer ones containing "(final)" in the name if multiple exist.
            candidateSegNodes = []
            finalPreferredSegNodes = []
            for segNode in segmentationNodes:
                segStorageNode = segNode.GetStorageNode()
                segIdentifier = None
                if segStorageNode and segStorageNode.GetFileName():
                    segIdentifier = os.path.basename(segStorageNode.GetFileName())
                else:
                    segIdentifier = segNode.GetName()

                if not segIdentifier:
                    continue

                if segIdentifier.startswith(volumeBaseName):
                    # Any suffix allowed (e.g., .seg.nrrd, _v2.seg.nrrd, (final).seg.nrrd, etc.)
                    candidateSegNodes.append(segNode)
                    if ' (final)' in segIdentifier:
                        finalPreferredSegNodes.append(segNode)

            if finalPreferredSegNodes:
                matchingSegNode = finalPreferredSegNodes[0]
            elif candidateSegNodes:
                matchingSegNode = candidateSegNodes[0]
            
            if not matchingSegNode:
                warnings.append(f"Volume '{volumeName}' has no matching segmentation")
                continue
            
            slicer.util.showStatusMessage(f"Processing volume: {volumeName} with segment: {matchingSegNode.GetName()}...")
            slicer.app.processEvents()

            try:
                # Process this volume with its matching segmentation
                segmentResults = self.process_segmentation(matchingSegNode, volumeNode)
                
                # Check if any segments were found
                found_any = any(sliceNumbers for sliceNumbers in segmentResults.values())
                
                if found_any:
                    # Store results with volume name as ID
                    allResults[volumeName] = segmentResults
                else:
                    warnings.append(f"Volume '{volumeName}' has no matching segments")
                    
            except Exception as e:
                warnings.append(f"Failed to process volume '{volumeName}': {str(e)}")
                logging.warning(f"Failed to process volume {volumeName}: {e}")

        # Write all results to CSV
        if allResults or appendMode:
            slicer.util.showStatusMessage(f"Writing {os.path.basename(outputPath)} file...")
            slicer.app.processEvents()

            try:
                self.write_csv_all(allResults, outputPath, appendMode)
            except IOError as e:
                raise IOError(f"Could not write to file {outputPath}: {e}")

        logging.info('Export all mode completed')
        return warnings

    def write_csv_all(self, allResults, outputPath, appendMode=False):
        """
        Write all volume results to CSV file for Multi Sample mode
        ID column: only first row of each volume group has value (volume name), other rows are empty but keep comma
        """
        file_exists = os.path.exists(outputPath) and appendMode

        with open(outputPath, 'a' if appendMode else 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write header if not appending or if file doesn't exist
            if not file_exists:
                writer.writerow(['ID', 'SegmentName', 'SliceNumbers', 'SliceCount'])
            
            # Write data rows for each volume
            for volumeId, segmentResults in allResults.items():
                first_segment = True
                for segmentName, sliceNumbers in segmentResults.items():
                    if first_segment:
                        # First row of volume: use volume name as ID
                        segmentId = volumeId
                        # Add tab prefix to prevent Excel SYLK format detection
                        if segmentId and not segmentId.startswith('\t'):
                            segmentId = '\t' + str(segmentId)
                        first_segment = False
                    else:
                        # Other rows of same volume: empty ID but keep comma
                        segmentId = ""
                    
                    sliceNumbersStr = ",".join(map(str, sliceNumbers)) if sliceNumbers else ""
                    sliceCount = len(sliceNumbers) if sliceNumbers else 0
                    writer.writerow([segmentId, segmentName, sliceNumbersStr, sliceCount])

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
