import sys, os, shutil
import MDTConfigDBUtils
import cx_Oracle

def exitWithStatus(dbInstance, status, statusStr, inputs):
  w = 10
  if len(dbInstance) > w: w = len(dbInstance)
  if status == 0:
    print("%*s : Insertion of <%s %s> COMPLETE" % (w, dbInstance, inputs.deviceType, inputs.deviceName))
  else:
    print("%*s : FAILED to insert <%s %s> [Status = %i]" % (w,
                                                            dbInstance,
                                                            inputs.deviceType,
                                                            inputs.deviceName,
                                                            int(status)))
    print("%*s  Cause of failure: %s" % (w+1, " " , statusStr))

  sys.exit(status)

#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
def insertNewDevice(dbInstance, inputs, status = ''):
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
  # Let's check if our deviceType is in DEVICE_TYPES
  queryBase = 'select count(*)\n' \
              'from {0}.device_types d_t\n' \
              'where d_t.type_name = \'{1}\'\n'.format(acct, inputs.deviceType)
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
    exitWithStatus(dbInstance, 10, "Device type <%s> not found in MDT configuration DB" % inputs.deviceType, inputs)
  elif count > 1:
    exitWithStatus(dbInstance, 20, "Too many device types with name <%s> in MDT configuration DB" % inputs.deviceType, inputs)
  # ------------------------------------------------------------------
  # Let's check if this device is already in the DEVICES table
  queryBase = 'select count(*)\n' \
              'from {0}.devices d,\n' \
              '     {0}.device_types d_t\n' \
              'where d_t.type_name = \'{1}\'\n' \
              '  and d.type_id = d_t.type_oid\n' \
              '  and d.device_name = \'{2}\'\n'.format(acct, inputs.deviceType, inputs.deviceName)
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
    exitWithStatus(dbInstance, 11, "Device <%s> already exists in MDT configuration DB" % inputs.deviceName, inputs)
  elif count > 1:
    exitWithStatus(dbInstance, 21, "Too many devices with name <%s> in MDT configuration DB" % inputs.deviceName, inputs)
  # ------------------------------------------------------------------
  # Let's make sure the device pin is not used by others
  queryBase = 'select count(*)\n' \
              'from {0}.devices d \n' \
              'where d.device_pin = \'{1}\'\n'.format(acct, inputs.devicePin)
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
  if count > 0:
    # The pin is already in use!  Get the name of the device and exit
    queryBase = 'select d.device_name\n' \
                'from {0}.devices d\n' \
                'where d.device_pin = \'{1}\'\n'.format(acct, inputs.devicePin)
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
    deviceNameForUsedPin = results[0][0]
    exitWithStatus(dbInstance, 17, "Pin <%s> already used by <%s> in MDT configuration DB" % (inputs.devicePin, deviceNameForUsedPin), inputs)

  # ------------------------------------------------------------------
  # Let's insert this device into DEVICES table
  queryBase = 'insert into {0}.devices(\n' \
              'select null, t.type_oid, \'{1}\', \'{2}\'\n' \
              'from {0}.device_types t\n' \
              'where t.type_name = \'{3}\')\n'.format(acct, inputs.devicePin, inputs.deviceName, inputs.deviceType)
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
  exitWithStatus(dbInstance, 0, "All good!", inputs)
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
  print("%30s: Insert new device into MDT configuration DB devices table (ATONR and DEVDB11)." % os.path.basename(sys.argv[0])[1:])
  if len(sys.argv) < 4:
    print("%30s: %s <deviceType> <deviceName> <devicePin>" % ("Usage", os.path.basename(sys.argv[0])[1:]))
    print("%30s: device type (case sensitive; e.g., one of [MDT, CSM, Mezzanine Card, CAN Bus, ... ])" % "deviceType")
    print("%30s: device name"                                                                          % "deviceName")
    print("%30s: device pin"                                                                           % "devicePin")
    sys.exit(1)
  deviceType  = sys.argv[1]
  deviceName  = sys.argv[2]
  devicePin   = sys.argv[3]
  if not MDTConfigDBUtils.isAllowedDomain():
    print("")
    print("| ERROR You are not logged in to an appropriate machine to insert a new device into the")
    print("| ----- MDT configuration DB. Please log in to a node at Point 1 to make changes.")
    print("")
    sys.exit(1)
  if not MDTConfigDBUtils.isAllowedUser():
    print("")
    print("| ERROR You are not allowed to insert a new device into the")
    print("| ----- MDT configuration DB. Please contact Tiesheng.Dai@cern.ch or Devin.Harper@cern.ch to ")
    print("| ----- request permission (include name , institute, and contact person).")
    print("")
    sys.exit(2)
  emailAddress   = MDTConfigDBUtils.getEmailAddressForUser()
  emailAddressCC = MDTConfigDBUtils.getEmailAddressesForCC(emailAddress)
  print("| INFO Sending summary e-mails to:", emailAddress)
  print("| INFO with cc to:", emailAddressCC)

  if deviceType in ['MDT', 'MDM', 'CAN Bus', 'CSM', 'MRODX', 'Mezzanine Card']:
    if 'xx' not in deviceName:
      deviceName = deviceName.upper()
    if 'xx' not in devicePin:
      devicePin  = devicePin.upper()
  elif deviceType in ['Effective MDT', 'Multilayer']:
    deviceName = deviceName.lower()
    devicePin  = devicePin.upper()
  elif deviceType in ['CAN Bus PC', 'MROD Crate', 'MROD Rack', 'Power Mainframe',
                      'Power Branch', 'Power Crate', 'HV Board', 'LV Board',
                      'Gas System', 'Gas Rack', 'Gas Channel']:
    devicePin = devicePin.upper()

  inputs = MDTConfigDBUtils.struct(
                                    chamberName       = '',
                                    deviceType        = deviceType,
                                    deviceName        = deviceName,
                                    devicePin         = devicePin,
                                    expectedDevicePin = devicePin,
                                    parameterName     = '',
                                    deviceChannel     = '',
                                    currentValue      = '',
                                    wantedValue       = ''
                                  )
  #statusDEVDB11 = insertNewDevice('devdb11', inputs)
  hostName = os.getenv("HOSTNAME")
  if hostName == 'None':
    print("| ERROR Variable HOSTNAME not set!")
    print("| ERROR This is needed to determine the DB you need to read/write!")
    print("| ERROR Please set this variable or contact harper@cern.ch")
    sys.exit(2)
  elif 'pc-atlas-' in hostName: dbInstance = 'atonr_w'
  elif 'pc-mu' in hostName: dbInstance = 'atonr_w'
  else: dbInstance = 'devdb11'
  status = insertNewDevice(dbInstance, inputs)