# SliceStat Extension for 3D Slicer

## Overview

`SliceStat` is a module for 3D Slicer that analyzes a segmentation and exports a list of slice numbers where each segment appears. The output is saved as a `.csv` file, providing a clear and simple chart of segment distribution along the slices.

This is useful for quickly identifying which slices contain specific anatomical structures or regions of interest that have been segmented.

## Installation

This method allows you to use the module without building it into your 3D Slicer application.

1.  **Open 3D Slicer.**
2.  Go to `Edit` -> `Application Settings`.
3.  Select the `Modules` section on the left.
4.  Click to >> icon next to `Additional module paths` box, click the `Add` button.
5.  Navigate to and select the **root folder** of this project (the folder containing this `README.md` file and the `SliceStat` subfolder).
6.  Click `OK` to close the settings window.
7.  **Restart 3D Slicer.** This step is mandatory.

After restarting, you will find the **Slice Statistics** module in the module selection dropdown, under the **VsData** category.

### Install from GitHub Release (.zip)

If you prefer to download a packaged zip:

1. Download the latest `SliceStat-<version>.zip` from the GitHub Releases page.
2. Extract the zip to a folder.
3. In 3D Slicer, add that extracted folder to `Additional module paths` as described above.
4. Restart 3D Slicer.

## Usage

1.  Load your source volume (e.g., CT, MRI) and the corresponding segmentation file into 3D Slicer.
2.  Navigate to the **Slice Statistics** module (under the **VsData** category).
3.  **Source Volume:** The module will try to automatically select the correct source volume. If it's incorrect or not found, select it from this dropdown menu.
4.  **Segmentation:** Select the segmentation node you want to analyze from this dropdown.
5.  **Output File:** Click the `...` button to open a "Save" dialog. Choose a location and name for your output `.csv` file.
6.  Click the **Apply** button.
7.  The analysis will run. A summary will be printed to the Python console, a success message will pop up, and the `.csv` file will be saved to your chosen location.

## Author and Contact

This application was developed by VStarData.
For support or inquiries, please contact hoangson.vothanh@gmail.com.
