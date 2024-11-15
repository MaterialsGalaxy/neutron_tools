# gsas2_refinement_atoms

Gsas2_refinement_atoms is a galaxy tool with scripts written in python used to add atom refinement flags to a GSASII project to improve the Rietveld refinement used to analyse neutron powder diffraction data. 

## Main Features

basic features include:
- sections to input files for GSASII for the following categories
    - a GSASII project with a phase already loaded

- an interactive tool to view the histograms (TODO)

- will complete a refinement using the configured parameters.

- outputs 
    - a refined GSASII project .gpx file
    - a refinement details .lst file
    - backup .gpx files


## Prerequisites 
- requires a GSASII project .gpx file with a phase already loaded
- This can be taken from the ouput of the upload_gsas2_refinement tool

--TODO--

## Usage 

This tool is intended to be used as an intermediate stage of a refinement workflow and will produce outputs which can be passed onto further GSAS refinement tools. 
