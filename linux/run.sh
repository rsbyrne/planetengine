# #!/bin/bash
# umask 0000
# CORES=${1:-1}
# DIR=${2:-$(dirname "$(readlink -f "$0")")}
# JOBDIR=$DIR"/jobs/"
# LOGSDIR=$DIR"/logs/"
# RUNSCRIPT=${3:-$DIR"/run.py"}
# JOBFILE=${4:-$(ls $JOBDIR"pejob_"*".json" | sort -n | head -1)}
# PLANETENGINEDIR=${5:-"/home/jovyan/workspace/planetengine/"}
# mkdir -p $JOBDIR
# mkdir -p $LOGSDIR
# chmod -R 777 $JOBDIR
# chmod -R 777 $LOGSDIR
# OUTFILE=$LOGSDIR"/run.out"
# ERRORFILE=$LOGSDIR"/run.error"
# SCRIPTSDIR=$PLANETENGINEDIR"/linux"
# SINGLERUNSH=$SCRIPTSDIR"/singlerun.sh"
# if [ "$(ls -A $JOBDIR)" ]; then
#   sh $SINGLERUNSH $RUNSCRIPT $JOBFILE $CORES >> $OUTFILE 2>> $ERRORFILE &
# else
#   echo "No jobs to do!"
# fi
