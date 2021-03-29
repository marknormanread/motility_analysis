"""
Execute as 
$> python -m scripts.contrast_profiles [arguments]

!!! Note the lack of ".py" at the end of contrast_profiles. 
"""
import os
import glob
import datetime
import sys
import motility_analysis.contrast_profiles as contrast_profiles
import motility_analysis.profile as profile

def main():
    """
    Lets profile comparison be launched from the command line.
    """
    dir1 = None
    dir2 = None
    label1 = None
    label2 = None
    overWrite = False
    drawGraphs = False
    profileGraphs = False  
    outDir = None
    duration = None
    # read in command line args.
    i = 1   # index into args. Ignore the first one, since it's the name of the python module being run.
    while i < len(sys.argv):
        if sys.argv[i] == '-i1':     # the first directory containing cell motion data.
            i += 1
            dir1 = sys.argv[i]
        elif sys.argv[i] == '-i2':   # the second directory containing cell motion data.
            i += 1
            dir2 = sys.argv[i]
        elif sys.argv[i] == '-o':    # output directory where analysis data is written to.
            i += 1
            outDir = sys.argv[i]
        elif sys.argv[i] == '-l1':   # label for the first data set, used in graphing.
            i += 1
            label1 = sys.argv[i]
        elif sys.argv[i] == '-l2':   # label for the second data set, used in graphing.
            i += 1
            label2 = sys.argv[i]
        elif sys.argv[i] == '-ow':   # non-safe, overwrite existing data if it is found.
            overWrite = True
        elif sys.argv[i] == '-g':    # draw graphs if specified.
            drawGraphs = True
        elif sys.argv[i] == '-dur':  # filter based on duration (minutes)
            i += 1
            duration = float(sys.argv[i])
        i += 1

    if dir1 is None or dir2 is None:
        raise Exception('Must supply both directories for program profile input.')

    p1 = []
    reps = glob.glob(dir1 + '/rep*')
    reps = [r for r in reps if os.path.isdir(r)]
    if reps:
        print('found multiple replicate experiments, processing them all in batch.')
        for rep in reps:
            print(rep)
            p1.append(profile.build_profile(rep, graphs=profileGraphs, interpolate=True, trim_duration=duration))
    else:
        p1 = [profile.build_profile(dir1, graphs=profileGraphs, interpolate=True, trim_duration=duration)]

    p2 = []
    reps = glob.glob(dir2 + '/rep*')
    reps = [r for r in reps if os.path.isdir(r)]
    if reps:
        print('found multiple replicate experiments, processing them all in batch.')
        for rep in reps:
            print(rep)
            p2.append(profile.build_profile(rep, profileGraphs, interpolate=True, trim_duration=duration))
    else:
        p2 = [profile.build_profile(dir2, graphs=profileGraphs, interpolate=True, trim_duration=duration)]

    if label1 is None:
        label1 = dir1
        if dir1.find('/'):  # will find the index of the first occurrence.
            label1 = dir1[:dir1.find('/')]  # slice everything up to, but not including, the index of character.
    if label2 is None:
        label2 = dir2
        if dir2.find('/'):
            label2 = dir2[:dir2.find('/')]

    if outDir is None:
        outDir = label1 + '_Vs_' + label2
    # if the directory already exists, then append the date and time to prevent over writing.
    if os.path.exists(outDir):
        if overWrite:
            print('WARNING! Output directory already exists, but script running in -ow state, so data may be '
                  'overwritten.')
        else:
            date = datetime.datetime.today().strftime('%Y%m%d-%H_%M')
            outDir = outDir + '-' + date
    else:
        os.makedirs(outDir)

    # write the arguments used to generate this profile information to the filesystem.
    with open(outDir + '/arguments', 'w') as file:
        file.write(str(sys.argv))
        file.close()

    contrast_profiles.contrast(profile1=p1, profile2=p2, label1=label1, label2=label2, out_dir=outDir, draw_graphs=drawGraphs)


# python main method hook.
if __name__ == '__main__':
    main()
