#!/usr/bin/env python

import sys, os, shutil
import MDTConfigDBUtils
import cx_Oracle
import time

def exitWithStatus(dbInstance, status, statusStr, inputs):
  w = 10
  if len(dbInstance) > w: w = len(dbInstance)
  if status == 0:
    print("%*s : Inserting new device relation for <%s> and <%s> COMPLETE" % (w, dbInstance, inputs.chamberName,  inputs.deviceName))
  else:
    print("%*s : FAILED to insert new device relation for <%s> and <%s> [Status = %i]" % (w,
                                                                                          dbInstance,
                                                                                          inputs.chamberName,
                                                                                          inputs.deviceName,
                                                                                          int(status)))
    print("%*s  Cause of failure: %s" % (w+1, " " , statusStr))

  sys.exit(status)

#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
def insertNewDeviceRelation(dbInstance, inputs, status = ''):
  dbInstance = dbInstance.lower()
  user, passwd, tns, acct = MDTConfigDBUtils.getDBCredentials(dbInstance)
  try:
    connection = cx_Oracle.connect(user, passwd, tns)
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Connection problem")
    error, = exc.args
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  cursor = connection.cursor()
  # ------------------------------------------------------------------
  # Some setup
  confirmed  = False
  parentName = inputs.chamberName
  childName  = inputs.deviceName
  channel    = inputs.deviceChannel
  if len(channel) < 1: exitWithStatus(dbInstance, 9, '<channel> not defined properly', inputs)

  # ------------------------------------------------------------------
  # Let's check if our parent device is in DEVICES table
  queryBase = 'select count(*)\n' \
              'from {0}.devices d\n' \
              'where d.device_name = \'{1}\'\n'.format(acct, parentName)
  try:
    results = cursor.execute(queryBase).fetchall()
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Query problem")
    error, = exc.args
    print("| ----- Query")
    print(queryBase)
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  count = results[0][0]
  if count == 0:
    exitWithStatus(dbInstance, 10, "Device <%s> not found in MDT configuration DB" % parentName, inputs)
  elif count > 1:
    exitWithStatus(dbInstance, 20, "Too many devices with name <%s> in MDT configuration DB" % parentName, inputs)
  # ------------------------------------------------------------------
  # Let's check if our child device is in DEVICES table
  queryBase = 'select count(*)\n' \
              'from {0}.devices d\n' \
              'where d.device_name = \'{1}\'\n'.format(acct, childName)
  try:
    results = cursor.execute(queryBase).fetchall()
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Query problem")
    error, = exc.args
    print("| ----- Query")
    print(queryBase)
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  count = results[0][0]
  if count == 0:
    exitWithStatus(dbInstance, 11, "Device <%s> not found in MDT configuration DB" % childName, inputs)
  elif count > 1:
    exitWithStatus(dbInstance, 21, "Too many devices with name <%s> in MDT configuration DB" % childName, inputs)
  # ------------------------------------------------------------------
  # Let's check to make sure our wanted device_relation_type is defined
  queryBase = 'select count(*)\n' \
              'from {0}.devices pd,\n' \
              '     {0}.devices cd,\n' \
              '     {0}.device_relation_types rt\n' \
              'where pd.device_name = \'{1}\'\n' \
              '  and pd.type_id = rt.parent_type_id\n' \
              '  and cd.device_name = \'{2}\'\n' \
              '  and cd.type_id = rt.child_type_id\n'.format(acct, parentName, childName)
  try:
    results = cursor.execute(queryBase).fetchall()
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Query problem")
    error, = exc.args
    print("| ----- Query")
    print(queryBase)
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  count = results[0][0]
  if count == 0:
    exitWithStatus(dbInstance, 12, "Device relation type not found in MDT configuration DB" , inputs)
  elif count > 1:
    exitWithStatus(dbInstance, 22, "Too many device relation types in MDT configuration DB" , inputs)
  # ------------------------------------------------------------------
  # Let's check to make sure our wanted device_relation is NOT defined
  queryBase = 'select count(*)\n' \
              'from {0}.devices pd,\n' \
              '     {0}.devices cd,\n' \
              '     {0}.device_relations r\n' \
              'where pd.device_name = \'{1}\'\n' \
              '  and pd.device_oid = r.parent_id\n' \
              '  and cd.device_name = \'{2}\'\n' \
              '  and cd.device_oid = r.child_id\n' \
              '  and r.since < sysdate\n' \
              '  and r.until > sysdate\n'.format(acct, parentName, childName)
  try:
    results = cursor.execute(queryBase).fetchall()
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Query problem")
    error, = exc.args
    print("| ----- Query")
    print(queryBase)
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  count = results[0][0]
  if count == 1:
    queryBase = 'select  r.relation_oid, r.relation_type_id, r.channel\n' \
                'from {0}.devices pd,\n' \
                '     {0}.devices cd,\n' \
                '     {0}.device_relations r\n' \
                'where pd.device_name = \'{1}\'\n' \
                '  and pd.device_oid = r.parent_id\n' \
                '  and cd.device_name = \'{2}\'\n' \
                '  and cd.device_oid = r.child_id\n' \
                '  and r.since < sysdate\n' \
                '  and r.until > sysdate\n'.format(acct, parentName, childName)
    try:
      results = cursor.execute(queryBase).fetchall()
    except cx_Oracle.DatabaseError as exc:
      print("| ERROR Query problem")
      error, = exc.args
      print("| ----- Query")
      print(queryBase)
      print("| ----- Oracle Error Code", error.code)
      print("| ----- Oracle Error Message", error.message)
      sys.exit(3)
    rOID, rTypeID, rChannel = results[0]
    if rChannel == channel:
      print('Device relation between %s and %s already defined!  NO CHANGE' % (parentName, childName))
      exitWithStatus(dbInstance, 0, "All good!", inputs)
    elif not confirmed:
      prompt = '| PROMPT Device relation of %s and %s exists, continue? [Y/n] : ' % (parentName, childName)
      yesno = ''
      while yesno == '':
        yesno = str(raw_input(prompt)).lower()
        if yesno == '': yesno = 'y'
        if yesno == 'n' or yesno == 'no':
          sys.exit(0)
        elif yesno == 'y' or yesno == 'yes':
          confirmed = True
        else:
          yesno = ''
          print("| ERROR Try again!")
    # Outdate the current device_relation
    queryBase = 'update {0}.device_relations\n' \
                'set until = sysdate\n' \
                'where relation_oid in\n' \
                '(\n' \
                'select r.relation_oid\n' \
                'from {0}.devices pd,\n' \
                '     {0}.devices cd,\n' \
                '     {0}.device_relations r\n' \
                'where pd.device_name = \'{1}\'\n' \
                '  and pd.device_oid = r.parent_id\n' \
                '  and cd.device_name = \'{2}\'\n' \
                '  and cd.device_oid = r.child_id\n' \
                '  and r.since < sysdate\n' \
                '  and r.until > sysdate)\n'.format(acct, parentName, childName)
    try:
      cursor.execute(queryBase)
    except cx_Oracle.DatabaseError as exc:
      print("| ERROR Query problem")
      error, = exc.args
      print("| ----- Query")
      print(queryBase)
      print("| ----- Oracle Error Code", error.code)
      print("| ----- Oracle Error Message", error.message)
      sys.exit(3)
  elif count > 1:
    exitWithStatus(dbInstance, 23, "Too many device relations between %s and %s" % (parentName, childName), inputs)
  queryBase = 'insert into {0}.device_relations (\n' \
              'select null, rt.relation_type_oid, cd.device_oid, pd.device_oid, \'{1}\', \n' \
              'sysdate, to_date(\'01.01.3000 00:00:00\',\'DD.MM.YYYY HH24:MI:SS\'), null\n' \
              'from {0}.devices pd, {0}.devices cd, {0}.device_relation_types rt\n' \
              'where pd.device_name = \'{2}\'\n' \
              '  and pd.type_id = rt.parent_type_id\n' \
              '  and cd.device_name = \'{3}\'\n' \
              '  and cd.type_id = rt.child_type_id)\n'.format(acct, channel, parentName, childName)
  try:
    cursor.execute(queryBase)
  except cx_Oracle.DatabaseError as exc:
    print("| ERROR Query problem")
    error, = exc.args
    print("| ----- Query")
    print(queryBase)
    print("| ----- Oracle Error Code", error.code)
    print("| ----- Oracle Error Message", error.message)
    sys.exit(3)
  connection.commit()
  time.sleep(2)
  exitWithStatus(dbInstance, 0, "All good!", inputs)
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
  print("%30s: Insert new device relation in MDT configuration DB devices_relations table (ATONR and DEVDB11)." % os.path.basename(sys.argv[0])[1:])
  if len(sys.argv) < 4:
    print("%30s: %s <parentName> <childName> <channel>" % ("Usage", os.path.basename(sys.argv[0])[1:]))
    print("%30s: parent device name (case sensitive)" % "parentName")
    print("%30s: child device name (case sensitive)"  % "childName")
    print("%30s: channel in device_relations table"   % "channel")
    sys.exit(1)
  parentName = sys.argv[1]
  childName  = sys.argv[2]
  channel    = sys.argv[3].upper()
  if not MDTConfigDBUtils.isAllowedDomain():
    print("")
    print("| ERROR You are not logged in to an appropriate machine to insert a new device relation in the")
    print("| ----- MDT configuration DB. Please log in to a node at Point 1 to make changes.")
    print("")
    sys.exit(1)
  if not MDTConfigDBUtils.isAllowedUser():
    print("")
    print("| ERROR You are not allowed to insert a new device relation in the")
    print("| ----- MDT configuration DB. Please contact Tiesheng.Dai@cern.ch or Devin.Harper@cern.ch to ")
    print("| ----- request permission (include name , institute, and contact person).")
    print("")
    sys.exit(2)
  emailAddress   = MDTConfigDBUtils.getEmailAddressForUser()
  emailAddressCC = MDTConfigDBUtils.getEmailAddressesForCC(emailAddress)
  print("| INFO Sending summary e-mails to:", emailAddress)
  print("| INFO with cc to:", emailAddressCC)

  inputs = MDTConfigDBUtils.struct(
                                    chamberName       = parentName,
                                    deviceType        = '',
                                    deviceName        = childName,
                                    devicePin         = '',
                                    expectedDevicePin = '',
                                    parameterName     = '',
                                    deviceChannel     = channel,
                                    currentValue      = '',
                                    wantedValue       = ''
                                  )
  #statusDEVDB11 = insertNewDeviceRelation('devdb11', inputs)
  hostName = os.getenv("HOSTNAME")
  if hostName == 'None':
    print("| ERROR Variable HOSTNAME not set!")
    print("| ERROR This is needed to determine the DB you need to read/write!")
    print("| ERROR Please set this variable or contact harper@cern.ch")
    sys.exit(2)
  elif 'pc-atlas-' in hostName: dbInstance = 'atonr_w'
  elif 'pc-mu' in hostName: dbInstance = 'atonr_w'
  else: dbInstance = 'devdb11'
  status = insertNewDeviceRelation(dbInstance, inputs)