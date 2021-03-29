"""
If running this script with the motility_analysis package uninstalled (ie, just from local copies of the source that you
downloaded) do:

$> cd whereever/I/downloaded/motility_analysis
this directory should contain the sample_data folder. Then run:

$> python3 -m tests.test_profiles.py

If you have installed motility_analysis on your system, then you can run this script in a more conventional manner:

$> cd whereever/I/downloaded/motility_analysis
$> python3 -m test.test_profiles.py

The former method is needed to ensure all package imports resolve correctly if you haven't installed motility_analysis,
otherwise python won't know where to look for them. The latter needs to be called from the parent directory so that the
paths to the data resolve correctly. Of course, you can also just change them, there are only 6.
"""
import motility_analysis.build
import os


__author__ = "Mark N. Read"
__copyright__ = "Copyright 2017, Mark N. Read."
__license__ = "GPL"
__email__ = "mark.norman.read@gmail.com"
__status__ = "Development"


data_prefix = 'sample_data'

# levy1 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'Levy_rep0'), graphs=True,
#                                                 trim_displacement=10.)

# levy2 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'Levy_rep1'), graphs=True,
#                                                 trim_displacement=10.)

# levy3 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'Levy_rep2'), graphs=True,
#                                                 trim_displacement=10.)

crw1 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep0'), graphs=True,
                                               timestep_s=30.)

# crw2 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep1'), graphs=True,
#                                                timestep_s=40.)

# crw3 = motility_analysis.build.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep2'), graphs=True,
#                                                timestep_s=50.)


