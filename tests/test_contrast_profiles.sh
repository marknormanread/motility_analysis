#
# Execute as
#
# $> chmod +x tests/test_contrast_profiles.sh
# $> ./tests/test_contrast_profiles.sh
#
# You can run the script through other means, as long as all the paths resolve correctly.


pwd
# To demonstrate the ways in which time step size information can be supplied, these directories do not contain this
# information in a file form (rather, it is passed as a procedure argument from within python). Note that whilst I
# am accommodating this in the code, I consider it bad practice. All data pertaining to an experiment should be
# contained within the said directory. Supply this information for now, and delete after the test.
echo 30 > sample_data/InvHeteroCRW_rep0/_TimeStepSec.txt
echo 50 > sample_data/InvHeteroCRW_rep2/_TimeStepSec.txt

python3 -m scripts.contrast_profiles -i1 sample_data/InvHeteroCRW_rep0 -i2 sample_data/InvHeteroCRW_rep2 -l1 fast -l2 slow -o sample_data/crw_fast_vs_crw_slow -ow -g

# clean up
rm sample_data/InvHeteroCRW_rep0/_TimeStepSec.txt
rm sample_data/InvHeteroCRW_rep2/_TimeStepSec.txt
