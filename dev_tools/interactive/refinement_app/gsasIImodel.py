import sys
sys.path.append("/home/mkscd/miniconda3/envs/GSASII/GSAS-II/GSASII")
import GSASIIscriptable as G2sc  # type: ignore
test_proj_dir = "YAG.gpx"

gpx = G2sc.G2Project(gpxfile=test_proj_dir, newgpx="test_proj.gpx")
gpx.save()
# get the sample and instrument parameters from previous refinement in
# dictionaries.

# h.getHistEntryValue(['Sample Parameters', 'Type'], 'Bragg-Brentano')
histnum = len(gpx.histograms())
h = gpx.histograms()[0]

sampleparams = {
    "Scale": h.getHistEntryValue(['Sample Parameters', 'Scale']),
    "DisplaceX": h.getHistEntryValue(['Sample Parameters', 'DisplaceX']),
    "DisplaceY": h.getHistEntryValue(['Sample Parameters', 'DisplaceY']),
    "Absorption": h.getHistEntryValue(['Sample Parameters', 'Absorption']),
}
sampreflist = []
instreflist = []

for param in sampleparams:
    if sampleparams[param][1] is True:
        sampreflist.append(param)
print(h.getHistEntryValue(['Instrument Parameters'])[0]['Lam'])
print(h.getHistEntryValue(['Sample Parameters']))

instdict = h.getHistEntryValue(['Instrument Parameters'])[0]

instparams = {
    "Lam": instdict['Lam'],
    "Zero": instdict['Zero'],
    "U": instdict['U'],
    "V": instdict['V'],
    "W": instdict['W'],
    "X": instdict['X'],
    "Y": instdict['Y'],
    "Z": instdict['Z'],
    # "SH/L": instdict['SH/L'],
}
print(instparams)

for param in instparams:
    if instparams[param][1] is True:
        instreflist.append(param)
