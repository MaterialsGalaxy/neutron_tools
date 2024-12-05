# gsas2_gpx_refinement

Gsas2_gpx_refinement is a galaxy tool with scripts written in python used execute a GSASII Rietveld refinement from a GSASII gpx project file to analyse neutron powder diffraction data. This tool is intended to be used with and by the interactive refinement tool.

## Main Features

basic features include:
- runs a refinement on a GSASII project.
- can be called by the interactive refinement tool.

- outputs 
    - a refined GSASII project .gpx file
    - a refinement details .lst file
    - backup .gpx files


## Prerequisites 
- requires a GSASII project .gpx file with a phase already loaded

## Usage 

This tool is intended to be ran from the interactive refinement tool, so inputs and refinement flags for the project file are made in teh interactive tool with the refinement itself executed by this tool in galaxy. 
