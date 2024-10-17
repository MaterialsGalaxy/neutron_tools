# GSASII refinement Sample and Instrument Parameters

gsas2_refinement_sample_instrument_prms is a galaxy tool with scripts written in python used to execute an Reitveld refinement in a GSASII project after changing the refinement settings for sample and instrument parameters. 

## Main Features

- Takes a GSASII project as input from a previous stage of refinement

- contains all options from the instrument and sample parameters data tree from GSASII

- will complete a refinement and produce outputs for the next stage of refinement including
    - more plots for inspection
    - a GSAS project to pass to the next stage
    - the refinement lst

## Prerequisites 
- The upload_gsas2_refinement tool would ideally be used in the workflow at some point before this tool is used

## Usage 
- This tool is intended to be used as an intermediate stage of a GSAS2 refinement workflow, but can be used with suitable file inputs.
- this tool requires a GSASII gpx project file 
- this tool outputs:
    a GSASII gpx file
    a refinement lst file
    plots of the refinements

## Development notes
### multiple phases and histograms
- will have to add a parser method to input lists for each phase / histogram, or have all the inputs create an input text file read into the script
- python script works locally and any added refinement parameters remain checked in the output gpx. For sequences of refinements important to remember whats checked.
- tool also works locally. Need to add the config file functionality .  
- i think the lst file has all the config that we need. 