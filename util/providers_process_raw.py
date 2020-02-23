# Parse Downloaded TSV files and convert into JSON 
# files to allow providers to be retrieved by state + TIN
# Also produce index for auto complete by token on 
# first and last name.   Also produce sample search
# result file that can be used to drive the basic
# search function.    Generates files on static 
# disk to approximate interacting with a list of
# providers from intelligent services.
#
# NOTE: This utiliity creates a search index file by unique token
#  and auto suggest tokens for last_name,first name, license number
#  npi.  we would normaly use server side functionality and a
#  more compact storage format but we wanted the basic search
#  to run with only client side search logic off the static gitpages
#  server so used this brute force mechanism.
#
# WARNING: After these files are generated you may need to
#  manually add them with git from the command line because
#  sourcetree panics with this many files.
#
# TODO: Modify the logic to use 3 letter seprate for deeper
# directory tree instead of having a lot of files in a single
# directory.
#

import json
import time
import glob
import os

tab = "\t"
def parseBool(avar):
  if avar == "Y":
    return True
  elif avar == "N":
    return False
  else:
    return None

def makeFiNameSafe(astr):
      # TODO: Modify to use RegEx instead of
      # duplicate replaces.  NOTE:
      # This method must be synchronized to
      # produce same output as mforms.js->makeSafeFiName()
      tout = astr.strip().upper()
      tout = tout.replace("/","_").replace("\\","_")
      tout = tout.replace(" ","_").replace("? ","_")
      tout = tout.replace("@","_").replace("#","_")
      tout = tout.replace("(","_").replace(")","_")
      tout = tout.replace("[","_").replace("]","_")
      tout = tout.replace("<","_").replace(">","_")
      tout = tout.replace("=","_").replace("|","_")
      tout = tout.replace("{","_").replace("}","_")
      tout = tout.replace("%","_").replace("$","_")
      tout = tout.replace("^","_").replace("+","_")
      tout = tout.replace(",","_").replace("?","_")
      tout = tout.replace("\n","").replace("\t","_")
      tout = tout.replace("\r","").replace("\c","")
      tout = tout.replace("\f","").replace("\"","_")
      tout = tout.replace("\'","_").replace("\`","_")
      tout = tout.replace("~","_").replace("!","_")
      tout = (tout.replace("._", "_")
                .replace("_.", "_")
                .replace("....",".")
                .replace("...",".")
                .replace("..",".")
                .replace("____","_")
                .replace("___", "_")
                .replace("__", "_")
                .replace("---","-")
                .replace("--", "-")                
              )
      return tout

        
def loadZips(fiName):
  FPZip = 0
  FPLat = 5
  FPLon = 6
  tout = {}
  fi = open(fiName)
  head = fi.readline()
  buffer = []
  totRecAdd = 0
  while True:
    aline = fi.readline().strip()
    if aline <= "":
      break
    try:
      fvals = aline.split("\t")
      zipcode = "%05d" % int(fvals[FPZip])
      lat = float(fvals[FPLat])
      lon = float(fvals[FPLon])
      tout[zipcode] = { "lat" : lat, "lon" : lon }
    except ValueError:
      pass # Some military zipcodes are known to fail
  return tout


indexByFirstName = {}
indexByLastName = {}
#indexByName = {}
indexByLicNum = {}
indexByNPI = {}
indexByCity = {}
indexBySpecial = {}
indexByBusinessName = {}
indexByState = {}
indexByZip = {}

start = time.time()
zipcodes = loadZips("../data/raw-download/zipcodes-geo.tsv")
totRecAdd = 0
recNum = -1
outNames = []
errCnt = 0

def updateIndex(ndx, fval, trec):
  # Add a record index by last name
  fval = fval.upper().strip();
  if fval in ndx:
    ndx[fval].append(trec)
  else:
    ndx[fval] = [trec]
    

# Produce a JSON file for each dentist in the import file.
# with TIN as the file name.  Also create a index by unique
# name token to approximate a search when we have only
# a static file server.
def processFile(fiName, outDir, doWrite):
  global recNum, errCnt, totRecAdd
  print("InputFiName=", fiName, " outDir=", outDir)
  f = open(fiName)
  
  if not os.path.exists(outDir):
    os.makedirs(outDir)
      
  errFi = open(fiName + ".err", "w")
  firstLine = f.readline().strip()
  fldNames = firstLine.split("\t")
  print ("fldNames=", fldNames)
  useNames = []
  fldPos = {}
  fldNdx = 0
  for aname in fldNames:
    tname = aname.strip().replace("(","_").replace(")","").replace("__","_")
    useNames.append(tname)
    fldPos[tname] = fldNdx
    print ("ndx=", fldNdx, tname)
    fldNdx = fldNdx + 1
    
  numFldHead = len(useNames)
  print("colNames=", useNames)

  pNamePrefix = fldPos["Name Prefix"]
  pNameSuffix = fldPos["Name Suffix"]
  pCredential = fldPos["Credential"]
  pNameLast = fldPos["Last Name"]
  pNameFirst = fldPos["First Name"]
  pNameMiddle = fldPos["Middle Name"]
  pGender = fldPos["Gender"]
  pOrgName = fldPos["Organization Name"]
  
  
  pMailAddr1 = fldPos["Mailing Address 1st Line"]
  pMailAddr2 = fldPos["Mailing Address 2nd Line"]
  pMailAddrCity = fldPos["Mailing Address City"]
  pMailAddrState = fldPos["Mailing Address State"]
  pMailAddrZip = fldPos["Mailing Address Zip Code"]
  pMailAddrPhone = fldPos["Mailing Address Phone"]
  pMailAddrFax = fldPos["Mailing Address Fax"]

  pBusAddr1 = fldPos["Business Address 1st Line"]
  pBusAddr2 = fldPos["Business Address 2nd Line"]
  pBusAddrCity = fldPos["Business Address City"]
  pBusAddrState = fldPos["Business Address State"]
  pBusAddrZip = fldPos["Business Address Zip Code"]
  pBusAddrPhone = fldPos["Business Address Phone"]
  pBusAddrFax = fldPos["Business Address Fax"]

  pClassification = fldPos["Classification"]
  pSpecial = fldPos["Specialization"]
  pLicNum = fldPos["License Number"]
  pLastUpdate = fldPos["Last Update Date"]
  pNPI = fldPos["NPI"]

  searchResFlds = [pNameLast, pNameFirst, pLicNum, pMailAddrState]


  buffer = [] 
  while True:
    recNum = recNum + 1
    aline = f.readline()
    #print ("aline=", aline)
    if aline <= "":
      break
    try:
      fvals = aline.split("\t")    
      numFld = min(len(fvals), numFldHead)
      if numFld <= pNPI:
        print("recNum=", recNum , " not enough fields found=", numFld, " needed=", pNPI, " line=", aline, " fvals=", fvals)
        continue
                   
      trec = {}
      trec["licNum"] = fvals[pLicNum].strip()
      trec["npi"] = fvals[pNPI].strip()
      if trec["licNum"] < " " and trec["npi"] > " ":
        trec["licNum"] = trec["npi"]
        
      if trec["licNum"] < " ":
        print("recNum=", recNum, "licNum can not be empty ", " line=", aline, " fvals=", fvals)
        continue
      
      trec["credential"] = fvals[pCredential].strip()
      trec["class"] =  fvals[pClassification].strip()
      trec["specialization"] = fvals[pSpecial].strip()
      trec["gender"] = fvals[pGender].strip()
      trec["updated"]= fvals[pLastUpdate].strip()
                 
      orgName = fvals[pOrgName].strip()
      if orgName > " ":
        fvals["orgName"] = orgName

      name = {}
      trec["name"] = name
      name["first"] = fvals[pNameFirst].strip()
      name["last"] = fvals[pNameLast].strip()
      if fvals[pNameMiddle] > " ":
        name["middle"]=fvals[pNameMiddle].strip()
      if fvals[pNamePrefix] > " ":
        name["prefix"]=fvals[pNamePrefix].strip()
      if fvals[pNameSuffix] > " ":
        name["suffix"]=fvals[pNameSuffix].strip()

      # Build a Index by Combined Name so we
      # can use it to build out the other indexes.
      # to approximate auto suggest and key fullfillment
      combName = name["last"]
      if "first" in name:
         combName +=  "," + name["first"]
      if "middle" in name:
         combName += "," + name["middle"]

      trec["orgName"] = fvals[pOrgName].strip()
         

      #TODO: Need to Find a Data source to approximate TIN
      #  For now we will construct a TIN from combination
      #  of NPI + Licesnse + phone
      trec["tin"] = fvals[pNPI].strip() + fvals[pLicNum].strip() + fvals[pBusAddrPhone].strip()
      trec["tin"] = trec["tin"].replace(" ", "")[:13]

      # Make Mailing address        
      zipcode = fvals[pMailAddrZip].strip()
      zip5 = zipcode[0:5]
      if zip5 in zipcodes:
        trec["loc"] = zipcodes[zip5]
      addr = {}
      trec["addr"]=addr
      cda = {}
      addr["mail"] =  cda
      cda["street_1"] = fvals[pMailAddr1].strip()
      if fvals[pMailAddr2] > " ":
        cda["street_2"] = fvals[pMailAddr2].strip()
                   
      cda["city"] = fvals[pMailAddrCity].strip()
      cda["state"] = fvals[pMailAddrState].strip()
      cda["zip"] = zipcode
      cda["zip5"]= zip5

      if fvals[pMailAddrPhone] > " ":
        cda["phone"] = fvals[pMailAddrPhone].strip()
      if fvals[pMailAddrFax] > " ":                   
        cda["fax"] = fvals[pMailAddrFax].strip()


      # Make Practice address
      zipcode = fvals[pBusAddrZip].strip()
      zip5 = zipcode[0:5]
      if zip5 in zipcodes:
        trec["loc"] = zipcodes[zip5]
      cda = {}
      addr["bus"] =  cda
      cda["street_1"] = fvals[pBusAddr1].strip()
      if fvals[pBusAddr2] > " ":
        cda["street_2"] = fvals[pBusAddr2].strip()
                   
      cda["city"] = fvals[pBusAddrCity].strip()
      cda["state"] = fvals[pBusAddrState].strip()
      cda["zip"] = zipcode
      cda["zip5"]= zip5

      if fvals[pBusAddrPhone] > " ":
        cda["phone"] = fvals[pBusAddrPhone].strip()
      if fvals[pBusAddrFax] > " ":                   
        cda["fax"] = fvals[pBusAddrFax].strip()

      # Add a record index by first name
      updateIndex(indexByFirstName,  name["first"], trec)
      updateIndex(indexByLastName,  name["last"], trec)
      updateIndex(indexByLicNum,  trec["licNum"], trec)
      updateIndex(indexByNPI,  trec["npi"], trec)
      updateIndex(indexBySpecial,  trec["specialization"], trec)
      updateIndex(indexByBusinessName,  trec["orgName"], trec)
      updateIndex(indexByState,  trec["addr"]["bus"]["state"], trec)
      updateIndex(indexByCity,  trec["addr"]["bus"]["city"], trec)
      updateIndex(indexByZip,   trec["addr"]["bus"]["zip5"], trec)


      #trec["combName"] = stn["last"] + ", " + stn["first"] + " " + stn["middle"]
      #trec["combName"] = trec["combName"].replace("  ", " ").strip()
      #if trec["orgName"] < " ":
      #  trec["orgName"] = trec["combName"]

      jsonRecStr = json.dumps(trec)

      # Save individual JSON file for practioner
      if doWrite == True:
        safeId=makeFiNameSafe(trec["licNum"])        
        fiOutName = outDir + "/" + safeId + ".json"
        fout = open(fiOutName, "w")
        fout.write(jsonRecStr)
        fout.close()
        print("wrote ", len(jsonRecStr), " bytes to " + fiOutName)
                     
      totRecAdd += 1
                   
    except ValueError:
      errCnt += 1
      errFi.write("errCnt=" + str(errCnt) + " parse error aLine=" +  aline + "\tfvals=" + str(fvals) + "\n")

  #outFi.close()
  errFi.close()



# Generate a series of files that for each unique
# value Last Name write a set of search records
# in tab delimited format to make rendering
# a search screen easy
def makeIndexByKey(index, outDir):
  if not os.path.exists(outDir):
     os.makedirs(outDir)
  for key, recs in index.items():
    #print("key=", key)
    safeKey = makeFiNameSafe(key)
    safeKey = safeKey.replace("_cma_", "").replace("_sq_", "").replace("_dq_","").replace("_per_","")
    toutName = outDir + "/" + safeKey + ".txt"
    
    fo = open(toutName, "w")
    fo.write("lastName\tfirstName\tlicNum\ttin\taddress\tcity\tstate\n")
    for rec in recs:
      addr = rec["addr"]["bus"]
      tstr = (rec["name"]["last"] + tab + rec["name"]["first"] + tab 
              + rec["licNum"] + tab + rec["tin"] + tab
              + addr["street_1"] + tab
              + addr["city"] + tab
              + addr["state"]
              + "\n")
      fo.write(tstr)      
    fo.close

  

# Generate a series of files that for each unique
# value Last Name write a set of search records
# in tab delimited format to make rendering
# a search screen easy
def makeStemIndex(index, stemOutDir, maxStemToken):
  if not os.path.exists(stemOutDir):
     os.makedirs(stemOutDir)
  stemNdx = {}
  for key, recs in index.items():
    #print("key=", key)
    safeKey = makeFiNameSafe(key)
    safeKey = safeKey.replace("_cma_", "").replace("_sq_", "").replace("_dq_","").replace("_per_","")    
    for rec in recs:
      # Update our stemming index for the
      # current safeKey
      wrkStr = ""
      for tchar in safeKey:
        wrkStr += str(tchar)
        #print("tchar=", tchar, "wrkStr=", wrkStr)
        if wrkStr in stemNdx:
          tokenCnts = stemNdx[wrkStr]
          if safeKey in tokenCnts:
            tokenCnts[safeKey] += 1
            #print("increment key wrkStr=", wrkStr, " safeKey=", safeKey, "cnt=", tokenCnts[safeKey])
          else:
            tokenCnts[safeKey] = 1
            #print("fist safekey=", safeKey, " for stem=", wrkStr)
        else:
          #print ("first use of stem=", wrkStr)
          stemNdx[wrkStr] = {}
          stemNdx[wrkStr][safeKey]=1
  
  # Save our Stem Index
  for aStem, tokens in stemNdx.items():
    #print("aStem=", aStem, " tokens=", tokens)
    sname = stemOutDir + "/" + aStem + ".txt"
    fo = open(sname, "w")
    # Sort Tokens into which Token had highest count
    tarr = []
    for atkn, tknCnt in tokens.items():
      #print("atkn=", atkn, "tknCnt=", tknCnt)
      tarr.append([999999999 - tknCnt, atkn,tknCnt])
    tarr.sort()
    
    # Write the sorted list out to the token
    numRow = 0
    for ele in tarr:
      #print("ele=", ele)
      numRow += 1
      fo.write(ele[1] + tab + str(ele[2]) + "\n")
      if numRow >= maxStemToken:
        break;
    fo.close()
  
  return stemNdx
      

##############
## MAIN
##############
  
inDir = "../data/raw-download/dental/provider/*.txt"
fnames = glob.glob(inDir)
print("inDir=", inDir, " fnames=", fnames)

for fname in fnames:
  print ("fname=", fname)
  processFile(fname, "../docs/data/dental/provider/recs", True)



curr = time.time()
elap = curr - start
print ("totTime=", elap,  "totRecAdd=", totRecAdd, " recsPerSec=", totRecAdd / elap, " errCnt=", str(errCnt))

print("make search indexes")

makeIndexByKey(indexByFirstName, "../docs/data/dental/provider/index/first_name")
makeIndexByKey(indexByLastName, "../docs/data/dental/provider/index/last_name")
makeIndexByKey(indexByCity, "../docs/data/dental/provider/index/city")
makeIndexByKey(indexByZip, "../docs/data/dental/provider/index/zip")
makeIndexByKey(indexByLicNum, "../docs/data/dental/provider/index/license")

makeStemIndex(indexByFirstName, "../docs/data/dental/provider/autosug/first_name", 100)
makeStemIndex(indexByLastName, "../docs/data/dental/provider/autosug/last_name", 100)
makeStemIndex(indexByNPI,  "../docs/data/dental/provider/autosug/npi", 50)
makeStemIndex(indexByLicNum, "../docs/data/dental/provider/autosug/lic_num", 50)
makeStemIndex(indexBySpecial, "../docs/data/dental/provider/autosug/specialty", 50)
makeStemIndex(indexByBusinessName, "../docs/data/dental/provider/autosug/bus_name", 50)
makeStemIndex(indexByState, "../docs/data/dental/provider/autosug/state", 50)
makeStemIndex(indexByCity, "../docs/data/dental/provider/autosug/city", 50)
makeStemIndex(indexByZip, "../docs/data/dental/provider/autosug/zip", 50)



curr = time.time()
elap = curr - start
print ("totTime=", elap,  "totRecAdd=", totRecAdd, " recsPerSec=", totRecAdd / elap, " errCnt=", str(errCnt))

      
    
   

