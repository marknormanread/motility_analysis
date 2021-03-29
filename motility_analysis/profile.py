"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Mark N. Read, 2016.


This module builds a statistical motility profile based of motility data.

Mark N. Read, 2017
"""

import math
import numpy as np
import scipy.stats
import sys  # provides access to command line arguments.
from . import track
from . import geometry


class Profile:
    """
    Constructs a profile of the tracks in a movie/experiment. A Profile encapsulates, and summarises,
    many tracks.
    """

    class TeleportPoint:
        """
        Class for encapsulating data pertaining to track starts and finishes that appear/disappear in the middle
        of the imaging volume, in the middle of the experiment.
        """
        def __init__(self, x, y, z, time, track, start=False):
            self.x = x
            self.y = y
            self.z = z
            self.time = time   # timestamp of when this track occurred.
            self.track = track
            self.start = start  # if false, represents the end of a track.

    def __init__(self, tracks, trim_displacement=False, trim_observations=None, trim_duration=None,
                 trim_arrest_coefficient=None, analyse_teleports=False):
        """
        :param tracks: list of Track objects to include in the Profile
        :param trim_displacement: filter (omit) tracks less than this net displacement
        :param trim_observations: filter (omit) tracks comprising fewer than this many Positions
        :param trim_duration: filter (omit) tracks of duration lower than specified
        :param analyse_teleports: if True, analyse cells that appear or disappear ("teleports") from the volume, but not
        by migrating out of view. This is a sanity-checking routine, as I've whitnessed weird behaviour from Imaris

          trimDisplacement: set to true, tracks are discarded if their displacement is too small.
        """
        self.tracks = tracks
        # retain only tracks that meet specified minimum filter requirements
        if trim_displacement:
            len_before = len(self.tracks)
            self.tracks = [t for t in self.tracks if t.displacement >= trim_displacement]
            print('Excluding {:d} tracks, out of {:d}, that failed to meet displacement threshold of {:f}.'
                  .format(len_before-len(self.tracks), len_before, trim_displacement))
        if trim_observations:
            len_before = len(self.tracks)
            self.tracks = [t for t in self.tracks if len(t.positions) >= trim_observations]
            print('Excluding {x:d} tracks, out of {y:d}. on the basis of insufficient observations.'
                  .format(x=len_before-len(self.tracks), y=len_before))
        if trim_duration:
            len_before = len(self.tracks)
            self.tracks = [t for t in self.tracks if t.duration_min >= trim_duration]
            print('Excluding {x:d} tracks, out of {y:d}. on the basis of insufficient duration.'
                  .format(x=len_before - len(self.tracks), y=len_before))
        if trim_arrest_coefficient:
            len_before = len(self.tracks)
            self.tracks = [t for t in self.tracks if t.arrest_coefficient < trim_arrest_coefficient]
            print('Excluding {x:d} tracks, out of {y:d}. on the basis of high arrest coefficient.'
                  .format(x=len_before - len(self.tracks), y=len_before))

        # if the track doesn't have enough data to calculate a median speed, throw it out
        self.tracks = [t for t in self.tracks if not np.isnan(t.median_speed())]
        # same for track median turns
        self.tracks = [t for t in self.tracks if not np.isnan(t.median_turn())]

        broken = [t for t in self.tracks if t.broken]
        if len(self.tracks):
            percent_broken = 100.0 * len(broken) / len(self.tracks)
        else:
            percent_broken = -1.0
        print('{:d} broken tracks in profile, out of {:d}, = {:.2f} percent.'
              .format(len(broken), len(self.tracks), percent_broken))
        # calculate metrics based on tracks in profile.
        self.duration = [t.duration_min for t in self.tracks]        
        self.length = [t.length for t in self.tracks]
        self.displacement = [t.displacement for t in self.tracks]
        self.meander = [t.meander for t in self.tracks]
        self.medSpd = [t.median_speed() for t in self.tracks if not math.isnan(t.median_speed())]
        self.irqSpd = [t.irq_speed() for t in self.tracks if not math.isnan(t.irq_speed())]
        self.medTurn = [t.median_turn() for t in self.tracks if not math.isnan(t.median_turn())]
        self.irqTurn = [t.irq_turn() for t in self.tracks if not math.isnan(t.irq_turn())]
        self.medRoll = [t.median_roll() for t in self.tracks if not math.isnan(t.median_roll())]
        self.irqRoll = [t.irq_roll() for t in self.tracks if not math.isnan(t.irq_roll())]

        # stores a list of tracks that either start or end in the imaging volume, part way through experiment (not the
        # start or end!)
        self.teleport_tracks = []
        self.teleport_ends = []
        self.teleport_starts = []
        if analyse_teleports:
            self.analyse_teleportations()

    def analyse_cell_entries_imaging_volume(self):
        """
        Performs analysis of how many agents become tracked after time zero. For cellular imaging data, this likely
        reflects cells entering the imaging volume.
        """
        starters = [t for t in self.tracks if t.positions[0].time_s == 0.0]
        num_starters = len(starters)
        num_entries = len(self.tracks) - num_starters
        print('')
        print('calculating cell entries into the imaging volume...')
        print(str(num_starters) + ' cells resided in the imaging volume at time 0.')
        print(str(num_entries) + ' cells subsequently entered the imaging volume thereafter.')
        print(str(len(self.tracks)) + ' cells in total.')
        print('')

    def collate_speeds(self):
        """
        Collects together all the speeds from all the tracks in this profile.
        Filters invalid values, and those associated with cell blebbing (fails to meet instantaneous velocity threshold.
        """
        all_speeds = [p.speed for t in self.tracks for p in t.positions
                      if (p.speed is not None and not math.isnan(p.speed) and p.meets_arrest_coeff_threshold)]
        return all_speeds

    def collate_turns(self):
        """
        Collects together all the turns from all the tracks (that have turn info) in this profile.
        Filters invalid values, and those associated with cell blebbing (fails to meet instantaneous velocity threshold.
        """
        all_turns = [p.turn for t in self.tracks for p in t.positions
                     if (p.turn is not None and not math.isnan(p.turn) and p.meets_arrest_coeff_threshold)]
        return all_turns

    def collate_instantaneous_fmi(self):
        """
        Filters invalid values, and those associated with cell blebbing (fails to meet instantaneous velocity threshold.
        """
        all_fmi = [p.instant_fmi for t in self.tracks for p in t.positions
                   if p.instant_fmi is not None and p.meets_arrest_coeff_threshold]
        return all_fmi

    def collate_rolls(self):
        """ Collects together all the roll rotational velocities for all the tracks in this profile. """
        return [p.roll for t in self.tracks for p in t.positions
                if (p.roll is not None and not math.isnan(p.roll))]

    def collate_meanders(self):
        """ Returns all meandering indexes for tracks in this profiles (only unbroken tracks). """
        return [t.meander for t in self.tracks if t.meander]

    def collate_lengths(self):
        """ Returns all lengths for unbroken tracks in this profile. """
        return [t.length for t in self.tracks if t.length]

    def collate_displacements(self):
        """ Returns all displacements for tracks in this profile. """
        return [t.displacement for t in self.tracks if t.displacement]

    def check_for_duplicates(self):
        """
        Checks across all tracks in this profile, to ensure that there are no duplicate Position objects. This is a
        check to ensure that track data is not being recorded twice. This is unlikely to be the case, if the input data
        has been carefully curated, but I have seen it happen at least once. I think this was because IMARIS did
        something weird, and hence this safety check was created.
        """
        print('\n\nCHECKING FOR DUPLICATE TRACK DATA\n\n')
        for i in range(0, len(self.tracks)):
            j_indexes = list(range(0, len(self.tracks)))
            j_indexes.remove(i)     # avoid comparison with self.
            for i_pos in self.tracks[i].positions:
                for j in j_indexes:
                    for j_pos in self.tracks[j].positions:
                        duplicate = (i_pos.x == j_pos.x and i_pos.x is not None) and \
                                    (i_pos.y == j_pos.y and i_pos.y is not None) and \
                                    (i_pos.z == j_pos.z and i_pos.z is not None)
                        if duplicate:
                            print('duplicate track position found:')
                            print('   x = {}'.format(i_pos.x))
                            print('   y = {}'.format(i_pos.y))
                            print('   z = {}'.format(i_pos.z))
                            print('   time = {}'.format(i_pos.time_s))
                            print('   i = {}, j = {}'.format(i, j))
        print('\n\nFINISHED\n\n')

    def analyse_teleportations(self, margin=0.1):
        """
        Another safety check for strange data I have encountered coming from IMARIS. This checks if cells are
        disappearing in the middle of the imaging volume (ie, they have (probably) not migrated out of view). To
        investigate the possibility that cells are legitimately leaving the imaging volume, we consider only a sub-volume
        defined as being some margin from the boundaries of the total imaging volume. The total imaging volume is
        estimated (does not need to be unput by user) based on observed data.

        The data assembled here can be used to join track segments into one, assuming that the disappearances and
        appearances reflect IMARIS temporarily losing the signal and not being able to reconstruct the tracks itself.
        """
        def inside_imaging_volume(xpos, ypos, zpos):
            if xpos < x_low or xpos > x_high:
                return False
            if ypos < y_low or ypos > y_high:
                return False
            if zpos < z_low or zpos > z_high:
                return False
            return True

        print('\nAnalysing tracks that appear and disappear in the middle of the imaging volume.')
        xs = [p.x for t in self.tracks for p in t.positions if p.x]
        ys = [p.y for t in self.tracks for p in t.positions if p.y]
        zs = [p.z for t in self.tracks for p in t.positions if p.z]

        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)
        z_range = max(zs) - min(zs)

        # calculate the sub-volume within which disappearing cells will be logged
        x_low  = min(xs) + (margin * x_range)
        x_high = max(xs) - (margin * x_range)
        y_low  = min(ys) + (margin * y_range)
        y_high = max(ys) - (margin * y_range)
        z_low  = min(zs) + (margin * z_range)
        z_high = max(zs) - (margin * z_range)

        print('the following boundaries are assumed to outline the imaging volume')
        print('  x: from ' + str(x_low) + ' to ' + str(x_high))
        print('  y: from ' + str(y_low) + ' to ' + str(y_high))
        print('  z: from ' + str(z_low) + ' to ' + str(z_high))

        track_end_times = [t.positions[-1].time_s for t in self.tracks]
        end_time = max(track_end_times)
        print('assuming end time was {:.2f} seconds ({:.2f} minutes), based on largest time stamp in supplied track '
              'data'.format(end_time, end_time / 60.0))
        for t in self.tracks:
            # two conditions of interest:
            # 1) track appeared part way through the simulation, and appeared in the middle of the volume.
            # 2) track ended part way through the simulation, and ended in the middle of the volume.
            p_start = t.positions[0]
            p_end = t.positions[-1]
            if p_start.time_s != 0.0 and inside_imaging_volume(p_start.x, p_start.y, p_start.z):
                self.teleport_starts.append(
                    self.TeleportPoint(x=p_start.x, y=p_start.y, z=p_end.z, time=p_start.time_s, track=t, start=True)
                )
            if p_end.time_s < end_time and inside_imaging_volume(p_end.x, p_end.y, p_end.z):
                self.teleport_ends.append(
                    self.TeleportPoint(x=p_end.x, y=p_end.y, z=p_end.z, time=p_end.time_s, track=t, start=False)
                )
        tele_points = self.teleport_starts + self.teleport_ends
        # get a unique list of tracks associated with tele_points (using set, and convert back to list thereafter).
        self.teleport_tracks = list(set([p.track for p in tele_points]))

        proportion = float(len(self.teleport_tracks)) / float(len(self.tracks))
        print('{:d} tracks either appeared or disappeared in the middle of the tissue volume.'
              .format(len(self.teleport_tracks)))
        print('there were {:d} tracks in total.'.format(len(self.tracks)))
        print('hence, {:.2f} of all tracks.\n'.format(proportion))

        all_points = self.teleport_starts + self.teleport_ends
        all_points.sort(key=lambda point: point.time_s)
        for i, p in enumerate(all_points):
            start_string = 'start'
            if not p.start:
                start_string = 'end'
            print('{:s}; time = {:f}; x = {:ff}; y = {:f}; z = {:f}'.format(start_string, p.time_s, p.x, p.y, p.z))
            if i != len(all_points) - 1:
                q = all_points[i + 1]
                print('   euclidean distance to next = {:f}'
                      .format(geometry.distance_between_points(p.x, p.y, p.z, q.x, q.y, q.z)))
                time_diff_min = (q.time_s - p.time_s) / 60.0
                print('   time distance to next = ' + str(time_diff_min))

    @staticmethod
    def calculate_msd(profiles=None, msd=None, max_dt=None, method='allT'):
        """
        Calculates the Mean Squared Displacement (MSD) values for a given list of profiles. Two methods can be
        employed, 'allT' will ascertain MSD values based on given delta-t taken from anywhere in the timeseries. In
        the alternative method the time difference is always from time zero onwards. The first method is much more
        robust and results in MSD being based on much more data.

        :param profiles: a list of Profile objects
        :param max_dt: maximum delta-t to base MSD calculations on.
        :return: a dictionary, with keys: ['msd']= a list of tuples being (delta-t, msd value); ['slope']= gradient of
        linear equation fitted to msd data; ['intercept']= msd value at delta-t = 0 (result of linear regression used
        in fitting a straight line to the data); ['r']= quality of linear regression fit to data; ['p']= likewise, but
        a p-value; ['stderr']= the standard error of the regression fit; ['msd_time_cutoff']=maximum delta-t value on
        which msd calculations are based; ['linearPlot'] and ['linearTimes']= y and x-axis values (respectively) values
        of the fitted straight line plot.
        """
        # Calculate if not user-supplied.
        if not msd:
            msd_dict = dict()  # Dictionary (<time> : <[msd values]>)
            if method is 'allT':
                # Collate all data together.
                for p in profiles:
                    for t in p.tracks:
                        deltaT_displacements_sq = t.get_deltaT_displacements_sq()
                        for dt in deltaT_displacements_sq.keys():
                            if dt not in msd_dict.keys():
                                msd_dict[dt] = []
                            msd_dict[dt].extend(deltaT_displacements_sq[dt])
            else:
                for prof in profiles:  # Populate the dictionary with data from the profiles supplied.
                    for t in prof.tracks:
                        for pos in t.positions:
                            if pos.time_s is not None and pos.time_s > 0.0:
                                # Protection against None times, can happen for missing data items with no interpolation
                                if pos.time_s not in msd_dict:
                                    msd_dict[pos.time_s] = []  # No record for this time, so adding one now.
                                msd_dict[pos.time_s].append(pos.total_displacement_squared)
            # Get list of sample times (keys), sorted in ascending order.
            ks = sorted(msd_dict.keys())
            msd = []  # Will create an array of tuples: (<time>, <msd value>)
            for key in ks:
                msd.append((key, np.mean(msd_dict[key])))

        if max_dt is None:
            # Calculate if not user-supplied. Standard practice is to plot only the first 25% of available data (as the
            # number of tracks being represented decreases at longer periods.
            biggest_time = msd[-1][0]
            max_dt = 0.25 * biggest_time
        elif max_dt != float('inf'):
            # Filter. Keep only those msd values for which time is less than the cutoff.
            msd = [tup for tup in msd if tup[0] <= max_dt]
        else:
            # Cutoff time of infinity means don't filter.
            pass

        times = [r[0] for r in msd]
        msds = [r[1] for r in msd]
        # Can't take log of 0.
        if len(times) > 0 and min(times) > 0. and min(msds) > 0.:
            # Log transform the data to find the slope.
            dts_log = [math.log(x) for x in times]
            msds_log = [math.log(x) for x in msds]
            # Linear regression on log transformed data.
            slope, intercept, r, p, stderr = scipy.stats.linregress(x=dts_log, y=msds_log)
            # Data to plot regression line on the plot. Plot will be log-transformed, so need to raise all values here
            # to e, otherwise it ends up double-log-transformed.
            linear = [math.exp((x * slope) + intercept) for x in dts_log]
            # Score results in a dictionary, and return.
            # 'msd' is a list of tuples, being (time, msd value).
            # 'linearPlot' contains y-axis values to be plotted against 'msd' time values (msd[:][0]) to obtain the
            # fitted straight line plot.
            return {'msd': msd, 'slope': slope, 'intercept': intercept, 'r': r, 'p': p, 'stderr': stderr,
                    'msd_time_cutoff': max_dt, 'linearPlot': linear, 'linearTimes': times}
        return {'msd': [[0., 0.]], 'slope': 0.0, 'intercept': 0.30, 'r': 0.0, 'p': 0.0, 'stderr': 0.0,
                'msd_time_cutoff': 100.0, 'linearPlot': [], 'linearTimes': []}

    @staticmethod
    def calculate_msd_vs_max_dt(profiles, upper_max_dt=float('inf')):
        """
        MSD slope seems sensitive to the maximum time interval examined.
        This establishes that relationship.
        upper_max_dt can be used to restict analyses to the same time ranges for different experiments.
        """
        # calculate the msd over all possible time intervals
        msd_results = Profile.calculate_msd(profiles, max_dt=float('inf'))
        # the time intervals possible (when no max dt is specified, above)
        dts = [msd[0] for msd in msd_results['msd'] if msd[0] <= upper_max_dt]
        # leave off the first value when investigating max dts, as it raises a runtime warning. Not clear what raises
        # it, buy my guess is an inability to perform linear regression on a single dt data point.
        dts = dts[1:]
        # calculate how the slopes change in response to differing max dts
        slopes = []
        for max_dt in dts:
            msd_results = Profile.calculate_msd(profiles, max_dt=max_dt)
            slopes.append(msd_results['slope'])
        return dts, slopes

    @staticmethod
    def collate_displacement_autocorrelation(profiles):
        """
        see Banigan 15, PLOS Computational Biology, for details and calculation.
        This finds the correlation between time-step displacements a given time apart.
        There's a lot going on here, so, some specifics.
        Firstly, a single autocorrelation value is calculated individually for each cell individually.
        Hence, for a given time interval, all possible correlations in the time series are calculated for a given cell.
        The mean correlation is extracted from this, and normalised against the mean directional movement (all
        displacements at any time correlated with themselves).
        These data are then pooled for all the cells. Hence, for any given time-distance, say, 3 min, a distribution
        of correlations are returned, with one value per cell.
        :param profiles:
        :return: a dictionary: [dt] = list( autocorrelations, one value per cell ).
                 dt = time distance used in correlation.
        """
        dac = dict()  # [deltaT] = list( autocorrelation )
        for p in profiles:
            for t in p.tracks:
                # store in the structure for all tracks
                for deltaT in t.displacement_autocorrelation.keys():
                    if deltaT not in dac.keys():
                        dac[deltaT] = []  # initialise if this is the first encounter of dt
                    dac[deltaT].append(t.displacement_autocorrelation[deltaT])
        return dac

    @staticmethod
    def _collate_deltaT_displacements_helper(profiles, series_retriever):
        """
        See Banigan 15, PLoS Computational Biology, for details.
        :param profiles:
        :param series_retriever: a function that takes as argument a track, and returns a dictionary. The dictionary
        takes as key a time interval and returns a list of displacements observed for that time interval. This can be
        done for net displacement, and displacement along each component axis.
        :return: a dictionary: [dt] = list( displacements over given delta T ).
                 dt = time distance used in correlation.
        """
        disps = dict()  # [deltaT] = list(displacements over given delta T)
        for p in profiles:
            for t in p.tracks:
                for delta_t in series_retriever(t).keys():
                    if delta_t not in disps.keys():
                        disps[delta_t] = list()
                    disps[delta_t].extend(series_retriever(t)[delta_t])
        return disps

    @staticmethod
    def collate_deltaT_displacements(profiles):
        """
        See Banigan 15, PLoS Computational Biology, for details.
        :param profiles:
        :return: a dictionary: [dt] = list( displacements over given delta T ).
                 dt = time distance used in correlation.
        """
        # use a lambda function to extract the exact deltaT_displacement data needed.
        return Profile._collate_deltaT_displacements_helper(profiles, lambda tr: tr.get_deltaT_displacements())

    @staticmethod
    def collate_deltaT_displacements_X(profiles):
        """ See collate_deltaT_displacements. """
        # use a lambda function to extract the exact deltaT_displacement data needed.
        return Profile._collate_deltaT_displacements_helper(profiles, lambda tr: tr.get_deltaT_displacements_X())

    @staticmethod
    def collate_deltaT_displacements_Y(profiles):
        """ See collate_deltaT_displacements. """
        # use a lambda function to extract the exact deltaT_displacement data needed.
        return Profile._collate_deltaT_displacements_helper(profiles, lambda tr: tr.get_deltaT_displacements_Y())

    @staticmethod
    def collate_deltaT_displacements_Z(profiles):
        """ See collate_deltaT_displacements. """
        # use a lambda function to extract the exact deltaT_displacement data needed.
        return Profile._collate_deltaT_displacements_helper(profiles, lambda tr: tr.get_deltaT_displacements_Z())
