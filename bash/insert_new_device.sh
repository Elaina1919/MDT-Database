#!/bin/sh
#
#source /det/muon/MDT/MDTConfigDB/.setup.sh
SCRIPT=`basename $0`
CURRDIR=`/bin/pwd`
PYSCRIPT=.insertNewDevice.py
SCRIPTDIR=${CURRDIR}/scripts

if test $# -lt 3; then
  ${SCRIPTDIR}/${PYSCRIPT}
  echo "| ERROR $SCRIPT: please provide all required inputs"
  exit
fi

DTYPE=$1
DNAME=$2
DPIN=$3

while test $# -gt 0
do
  case $1 in
    -h|-H|-help|-HELP)
      ${SCRIPTDIR}/${PYSCRIPT}
      exit;;
    -*) echo "| ERROR unknown option: $1" 1>&2; exit;;
     *) STRING="$STRING $1";;
  esac
  shift
done

#if test "$STRING"; then
#  set $STRING
#  DTYPE=$1; DNAME=$2; DPIN=$3; shift
#else
#  ${SCRIPTDIR}/${PYSCRIPT}
#  echo "| ERROR $SCRIPT: please provide all required inputs"
#  exit 1;
#fi
#while test $# -gt 0
#do
#  shift
#done

echo 1 $DTYPE 2 $DNAME 3 $DPIN

${SCRIPTDIR}/${PYSCRIPT} "${DTYPE}" "${DNAME}" "${DPIN}"