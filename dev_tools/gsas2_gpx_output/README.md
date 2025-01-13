# gsas2_gpx_output

Gsas2_gpx_output is a galaxy tool with scripts written in python used to generate outputs after completing a GSASII Rietveld refinement from a GSASII gpx project file. This tool is intended to be used with and by the interactive refinement tool.

## Main Features

basic features include:
- generates CIF files of refined phases from a GSASII project
- can be called by the interactive refinement tool.

- outputs 
    - a collection of cif files
    - a collection of fitted powder histograms


## Prerequisites 
- requires a GSASII project .gpx file

## Usage 

This tool is intended to be ran from the interactive refinement tool, but can be used with statically in Galaxy aswell. 
This tool should be used when finished with GSASII rietveld refinements.
