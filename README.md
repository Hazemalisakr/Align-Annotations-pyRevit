# Align Annotations for pyRevit

A custom pyRevit tool designed to streamline Revit workflows by automating the alignment of annotations (like Room Tags, Text Notes, and Independent Tags). When dealing with massive projects, aligning annotations one by one across hundreds of sheets becomes tedious. This tool allows you to select an entire row or column of tags and snap them into a perfect line instantly.

## Features

* **Three Alignment Modes:**
  * **Pick Reference on Screen:** Click exactly which tag you want to act as the master anchor line.
  * **Left-most / Top-most Element (Auto):** The tool automatically calculates the leftmost (for horizontal) or topmost (for vertical) tag in your selection and aligns everything to it.
  * **Average of All Selected:** Calculates the mathematical center line of all selected tags and snaps them to it.
* **Smart Revit Boundary Handling:** Bypasses Revit's annoying habit of sprouting unwanted leader lines when moving tags near room boundaries by cleanly moving the `Location.Point` data.
* **Horizontal & Vertical Support:** Choose between aligning elements horizontally or vertically.

## Installation

1. Ensure you have [pyRevit](https://github.com/eirannejad/pyRevit) installed on your machine.
2. Click the green **Code** button at the top of this repository and select **Download ZIP**.
3. Extract the downloaded ZIP file.
4. Rename the extracted folder to exactly `AlignAnnotations.extension`.
5. Open your Windows File Explorer and type `%appdata%` into the address bar at the top, then hit **Enter**.
6. Navigate to `pyRevit\Extensions` (If the `Extensions` folder doesn't exist, simply right-click and create a new folder named `Extensions`).
7. Move the `AlignAnnotations.extension` folder into this `Extensions` directory.
8. Open Revit (or if it's already open, go to the **pyRevit** tab on the ribbon and click the **Reload** button). 

A new **Sakr Tools** tab will automatically appear in your Revit ribbon containing the Align Annotations tool!
