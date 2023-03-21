#!/bin/sh
#
#source /det/muon/MDT/MDTConfigDB/.setup.sh
SCRIPT=`basename $0`
CURRDIR=`/bin/pwd`
PYSCRIPT=.modifyEMDTParameter.py
SCRIPTDIR=${CURRDIR}/scripts

# Check that we have adequation N_arg
if test $# -lt 3; then
  ${SCRIPTDIR}/${PYSCRIPT}
  echo "| ERROR $SCRIPT: please provide all required inputs"
  exit
fi

CHNAME=$1; PNAME=$2; PVAL=$3;

# Gather arguments
while test $# -gt 0
do
  case $1 in
    -h|-H|-help|-HELP)
      ${SCRIPTDIR}/${PYSCRIPT}
      exit;;
    #-*) echo "| ERROR unknown option: $1" 1>&2; exit;;
     *) STRING="$STRING $1";;
  esac
  shift
done


## Parse arguments
#if test "$STRING"; then
#  set $STRING
#  CHNAME=$1; PNAME=$2; PVAL=$3; CSMNAME=$4; CSMPIN=$5; shift
#else
#  ${SCRIPTDIR}/${PYSCRIPT}
#  echo "| ERROR $SCRIPT: please provide all required inputs"
#  exit 1;
#fi
#while test $# -gt 0
#do
#  shift
#done

${SCRIPTDIR}/${PYSCRIPT} "$CHNAME" "$PNAME" "$PVAL"