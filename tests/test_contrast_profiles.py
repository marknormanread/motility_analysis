"""

To execute:
    $> python3 -m tests.test_contrast_profiles
"""
import motility_analysis.contrast_profiles
import os

__author__ = "Mark N. Read"
__copyright__ = "Copyright 2017, Mark N. Read."
__license__ = "GPL"
__email__ = "mark.norman.read@gmail.com"
__status__ = "Development"


data_prefix = 'sample_data'  # if calling from within this directory, $> python3 test_profiles.py, then change to '.'

levy1 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'Levy_rep0'), graphs=False,
                                                trim_displacement=10.)

levy2 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'Levy_rep1'), graphs=False,
                                                trim_displacement=10.)

levy3 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'Levy_rep2'), graphs=False,
                                                trim_displacement=10.)

crw1 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep0'), graphs=False,
                                               timestep_s=30.)

crw2 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep1'), graphs=False,
                                               timestep_s=40.)

crw3 = motility_analysis.profile.build_profile(directory=os.path.join(data_prefix, 'InvHeteroCRW_rep2'), graphs=False,
                                               timestep_s=50.)

levy = [levy1, levy2, levy3]
crw = [crw1, crw2]
crw_slow = [crw3]


out_dir = os.path.join('sample_data', 'levy_vs_crw')

motility_analysis.contrast_profiles.contrast(p1=levy, p2=crw, p3=crw_slow,
                                             label1='Levy', label2='CRW', label3='CRW 50s',
                                             out_dir=out_dir, p1_colour='b', p2_colour='g', p3_colour='r',
                                             a_stats=True, draw_graphs=True)

