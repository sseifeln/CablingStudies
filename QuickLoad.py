import pandas as pd
import requests
import io
import numpy as np
import matplotlib.pyplot as plt

tkLayout = 'http://ghugo.web.cern.ch/ghugo/layouts/T15/'
#tkLayout='http://cms-tklayout.web.cern.ch/cms-tklayout/layouts/reference/'

referenceLayout='OT616_200_IT613'
#referenceLayout='OT616_IT613'
phiSectorName = 'DTC Phi Sector Ref'
#phiSectorName = 'DTC_Phi_Sector_Ref'
dtcName = 'DTC name'
nPhiSectors = 9 

phiName = 'Module phi_deg'
#phiName = 'Module_phi'

# modules in the 
def getModMap(pLayoutId = referenceLayout ): 
	moduleMap = tkLayout + pLayoutId + '/allCoordinates.csv'
	s=requests.get(moduleMap).content
	return pd.read_csv(io.StringIO(s.decode('utf-8'))) 

def getRadMap(pLayoutId = referenceLayout ) :
	moduleMap = tkLayout + pLayoutId + '/sensorsIrradiationOuter.csv'
	s=requests.get(moduleMap).content
	return pd.read_csv(io.StringIO(s.decode('utf-8'))) 

def getMap(pLayoutId = referenceLayout, pSide = 'positive') : 
    cablingMap = tkLayout + pLayoutId + '/ModulesToDTCs' + ("Pos" if (pSide == 'positive') else "Neg") + 'Outer.csv'
    s=requests.get(cablingMap).content
    return pd.read_csv(io.StringIO(s.decode('utf-8'))) 

def getCablingMap( pLayoutId = referenceLayout ) :
	cMapPositive = getMap(pSide = 'positive')
	cMapPositive['Side']=1
	cMapNegative = getMap(pSide = 'negative')
	cMapNegative['Side']=-1
	cMap = pd.concat([cMapNegative,cMapPositive])
	cColNames = [s.strip().split('/', 1)[0] for s in list(cMap.columns)]
	cMap = cMap.set_axis(cColNames, axis=1, inplace=False)
	df_obj = cMap.select_dtypes(['object'])
	cMap[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
	#cMap[df_obj.columns] = df_obj.apply(lambda x : "_".join( x.str.split() ) )
	return cMap 

def mergeMaps( pLayoutId = referenceLayout , modType = "PS10G" ) : 
	cCablingMap = getCablingMap(pLayoutId)
	cRadMap = getRadMap(pLayoutId) 
	cMerged = pd.merge(cCablingMap, cRadMap, how='inner', on="Module DetId")
	df =  cMerged.loc[cMerged['DTC name'].str.contains(modType)].loc[:, ['DTC CMSSW Id', 'DTC name', ' sensorsFluenceMean_Hb',' sensorsFluenceMax_Hb']]
	# min fluence (mean and max)
	df_min  = df.groupby('DTC CMSSW Id').min().add_suffix('min').reset_index()
	df_max  = df.groupby('DTC CMSSW Id').max().add_suffix('max').reset_index()
	df_mean = df.groupby('DTC CMSSW Id').mean().add_suffix('max').reset_index()
	# module count 
	df1 = cMerged.loc[:, ['DTC CMSSW Id']]
	df1['Module Count'] = np.zeros(len(cMerged))
	df1 = df1.loc[ cMerged['DTC name'].str.contains(modType)].groupby(["DTC CMSSW Id"]).count().sort_values(by=['DTC CMSSW Id'])
	# then merge with module count 
	df_m1 = pd.merge(df1, df_min, how='inner', on="DTC CMSSW Id")
	df_m2 = pd.merge(df_m1, df_max, how='inner', on="DTC CMSSW Id")
	return pd.merge(df_mean, df_max, how='inner', on="DTC CMSSW Id")

	


def countModules(pLayoutId = referenceLayout , modType = "PS10G") :
	cMap = getCablingMap(pLayoutId)
	df = cMap.loc[:, ['DTC CMSSW Id']]
	
	df['Module Count'] = np.zeros(len(cMap))
	df = df.loc[ cMap['DTC name'].str.contains(modType)].groupby(["DTC CMSSW Id"]).count().sort_values(by=['DTC CMSSW Id']) 
	return df;