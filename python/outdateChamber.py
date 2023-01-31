{\rtf1\ansi\ansicpg1252\cocoartf2706
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww15660\viewh11640\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import sys, os, shutil, time\
import MDTConfigDBUtils\
import cx_Oracle\
import time\
\
localtime = time.asctime( time.localtime(time.time()) )\
\
\
\
def generator(dbInstance,MDT):\
    dbInstance = dbInstance.lower()\
    user, passwd, tns, acct = MDTConfigDBUtils.getDBCredentials(dbInstance)\
    connection = cx_Oracle.connect(user, passwd, tns)\
    cursor = connection.cursor()\
    queryBase = "select * from \{0\}.device_types".format(acct)\
    results = cursor.execute(queryBase).fetchall()\
    dic=\{\}\
    for i, name in results:\
        dic[name] = i\
    mezz_dic = \{\}\
    csm_dic = \{\}\
    MDM_dic = \{\}\
    cb_dic = \{\}\
    lv_dic = \{\}\
    emdt_dic = \{\}\
    ml_dic = \{\}\
    hv_dic = \{\}\
    gas_dic = \{\}\
    filename = 'outdate_\{0\}_\{1\}.job'.format(MDT, dbInstance)\
    f = open(filename,'w')\
    f.write('#!/bin/bash\\n')\
    f.write('# Author        : Shuzhou Zhang\\n')\
    f.write('# Time/Location : \{0\}/CERN,Geneva\\n'.format(localtime))\
    f.write('#HostName : \{0\}\\n'.format(os.getenv("HOSTNAME")))\
    f.write('#Description: remove old chamber \{0\} from DB in \{1\}\\n'.format(MDT,dbInstance))\
    f.write('\\n')\
    f.write('##outdate MDT and Effective MDT\\n')\
    ##get EMDT and channel\
    queryBase = """select de.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and dm.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['MDT'],dic['Effective MDT'],MDT)\
    results = cursor.execute(queryBase).fetchall()\
    for name, i in results:\
        emdt_dic[name] = [MDT,i]\
        f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(name,MDT,i))\
    ##get multilayer and channel\
    f.write('\\n')\
    f.write('#outdate relation between multilayer and MDT\\n')\
    queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Multilayer'],dic['MDT'],MDT)\
    results = cursor.execute(queryBase).fetchall()\
    for name, i in results:\
        ml_dic[name] = [MDT,i]\
        f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(MDT,name,i))\
    f.write('\\n')\
    f.write('#outdate relation between multilayer and HV board\\n')\
    for ml in ml_dic.keys():\
        ##get HV board and channel\
        queryBase = """select de.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and dm.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Multilayer'],dic['Power Board HV'],ml)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            f.write("./bin/outdate_device_relation '\{0\}' \{1\} \{2\}\\n".format(name,ml,i))\
    f.write('\\n')\
    f.write('#outdate relation between multilayer and Gas Rack Channel\\n')\
    for ml in ml_dic.keys():\
        ##get Gas and channel\
        queryBase = """select de.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and dm.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Multilayer'],dic['Gas Channel'],ml)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            f.write("./bin/outdate_device_relation '\{0\}' \{1\} \{2\}\\n".format(name,ml,i))\
\
\
\
    for EMDT in emdt_dic.keys():\
        ## get mezz card name and channel\
        f.write('\\n')\
        f.write('#outdate Mezz card and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Mezzanine Card'],dic['Effective MDT'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
\
        for name, i in results:\
            mezz_dic[name] = [EMDT,i]\
            f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(EMDT,name,i))\
        ## get csm name and channel\
        f.write('\\n')\
        f.write('#outdate relation between CSM and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['CSM'],dic['Effective MDT'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            csm_dic[name] = [EMDT,i]\
            f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(EMDT,name,i))\
        ##get MDM name and channel\
        f.write('\\n')\
        f.write('#outdate relation between MDM and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.child_id\
                       and de.device_oid = r.parent_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['MDM'],dic['Effective MDT'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            MDM_dic[name] = [EMDT,i]\
            f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(EMDT,name,i))\
        ##get can bus and channel\
        f.write('\\n')\
        f.write('#outdate relation between can bus and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.parent_id\
                       and de.device_oid = r.child_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Effective MDT'],dic['CAN Bus'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            cb_dic[name] = [EMDT,i]\
            f.write('./bin/outdate_device_relation \{0\} \{1\} \{2\}\\n'.format(name,EMDT,i))\
        ##get LV board and channel\
        f.write('\\n')\
        f.write('#outdate relation between LV board and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.parent_id\
                       and de.device_oid = r.child_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Effective MDT'],dic['Power Board LV'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            lv_dic[name] = [EMDT,i]\
            f.write("./bin/outdate_device_relation '\{0\}' \{1\} \{2\}\\n".format(name,EMDT,i))\
        ##get MROAD and channel\
        f.write('\\n')\
        f.write('#outdate relation between MRODX and EMDT\\n')\
        queryBase = """select dm.device_name, r.channel\
                       from \{0\}.devices dm,\
                       \{0\}.devices de,\
                       \{0\}.device_relations r,\
                       \{0\}.device_relation_types t\
                       where r.relation_type_id = t.relation_type_oid\
                       and t.child_type_id = \{1\}\
                       and t.parent_type_id = \{2\}\
                       and dm.device_oid = r.parent_id\
                       and de.device_oid = r.child_id\
                       and de.device_name = '\{3\}'\
                       and r.until > sysdate\
                     """.format(acct, dic['Effective MDT'],dic['MRODX'],EMDT)\
        results = cursor.execute(queryBase).fetchall()\
        for name, i in results:\
            f.write("./bin/outdate_device_relation '\{0\}' \{1\} \{2\}\\n".format(name,EMDT,i))\
        ##emdt and config set items\
        f.write('\\n')\
        f.write("#outdate device config set items\\n")\
        f.write('./bin/outdate_config_set_items \{0\} "EdgeN1G1300" "EdgeN1G1300"'.format(EMDT))\
\
    f.close()\
    print('file saved to \{0\}'.format(filename))\
\
\
\
if __name__ == "__main__":\
    hostName = os.getenv("HOSTNAME")\
    print(hostName)\
    if hostName == 'None':\
        print("| ERROR Variable HOSTNAME not set!")\
        print("| ERROR This is needed to determine the DB you need to read/write!")\
        print("| ERROR Please set this variable or contact harper@cern.")\
        sys.exit(2)\
    elif 'pc-atlas-' in hostName: dbInstance = 'atonr_r'\
    elif 'pc-mu' in hostName: dbInstance = 'atonr_r'\
    else: dbInstance = 'devdb11'\
    generator(dbInstance, sys.argv[1])}