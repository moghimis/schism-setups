#!/bin/bash

#SBATCH --job-name=hmergeschism     # Specify job name
#SBATCH --comment="SCHISM postprocessing"
#SBATCH --partition=prepost   # Specify partition name
#SBATCH --ntasks=6 
#SBATCH --ntasks-per-node=6
#SBATCH --time=00:60:00        # Set a limit on the total run time
#SBATCH --wait-all-nodes=1     # start job, when all nodes are available
#SBATCH --mail-type=FAIL       # Notify user by email in case of job failure
#SBATCH --mail-user=richard.hofmeister@hzg.de  # Set your e−mail address
#SBATCH --account=gg0877       # Charge resources on this project account
#SBATCH --output=log_hotstart_merge_g.o    # File name for standard output
#SBATCH --error=log_hotstart_merge_g.e     # File name for standard error output
#SBATCH --share

id=nwshelf$1
mstr=$2
resdir=/scratch/g/$USER/schism-results/$id/$mstr/
module load python/2.7-ve0

## move log-files of output:
#mv $HOME/schism/setups/nwshelf/log.e $resdir
#mv $HOME/schism/setups/nwshelf/log.o $resdir

cd $resdir/outputs

# get step number:
days=$(python ~/schism/setups/nwshelf/mistral/get_rnday.py $mstr 2012-01)
iteration=$(python -c "print('%d'%int( ($days*86400./240.) ))")

# combine hotstart
$HOME/schism/svn-code/trunk/build/bin/combine_hotstart7 -i $iteration

# rename to avoid it=*
mv hotstart_it*.nc hotstart.nc

