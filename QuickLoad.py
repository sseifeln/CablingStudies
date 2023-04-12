import pandas as pd
import requests
import io
import numpy as np
import matplotlib.pyplot as plt


tkLayout = 'http://ghugo.web.cern.ch/ghugo/layouts/T15/'
#tkLayout='http://cms-tklayout.web.cern.ch/cms-tklayout/layouts/reference/'

referenceLayoutIT = 'http://ghugo.web.cern.ch/ghugo/layouts/it_cabling/OT800_IT701_cabling'
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

def getCablingMapIT (pLayoutId = referenceLayoutIT ) :
	cablingMap = pLayoutId + '/InnerTrackerModulesToDTCs.csv'
	s=requests.get(cablingMap).content
	cMap = pd.read_csv(io.StringIO(s.decode('utf-8')))
	cColNames = [s.strip().split('/', 1)[0] for s in list(cMap.columns)]
	cMap = cMap.set_axis(cColNames, axis=1, inplace=False)
	df_obj = cMap.select_dtypes(['object'])
	cMap[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
	return cMap 

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
	df =  cMerged.loc[cMerged['DTC name'].str.contains(modType)].loc[:, ['DTC CMSSW Id',' sensorsFluenceMean_Hb',' sensorsFluenceMax_Hb']]
	# min fluence (mean and max)
	df_min  = df.groupby('DTC CMSSW Id').min().add_suffix('min').reset_index()
	df_max  = df.groupby('DTC CMSSW Id').max().add_suffix('max').reset_index()
	df_mean = df.groupby('DTC CMSSW Id').mean().add_suffix('mean').reset_index()
	# module count 
	df1 = cMerged.loc[:, ['DTC CMSSW Id']]
	df1['Module Count'] = np.zeros(len(cMerged))
	df1 = df1.loc[ cMerged['DTC name'].str.contains(modType)].groupby(["DTC CMSSW Id"]).count().sort_values(by=['DTC CMSSW Id'])
	# then merge with module count 
	df_m1 = pd.merge(df1, df_min, how='inner', on="DTC CMSSW Id")
	df_m2 = pd.merge(df_m1, df_max, how='inner', on="DTC CMSSW Id")
	return pd.merge(df_m2, df_mean, how='inner', on="DTC CMSSW Id")


def countITChips( pLayoutId = referenceLayoutIT ) : 
	cMap = getCablingMapIT(pLayoutId)
	# number of chips 
	df_Nchips = cMap.loc[:, ['DTC_CMSSW_Id','N_Chips_Per_Module']]
	df_Nchips = df_Nchips.groupby(["DTC_CMSSW_Id"]).sum()
	# number of lpGBTs 
	df_lpGBTs = cMap.groupby('DTC_CMSSW_Id')['LpGBT_Id'].nunique()
	df = pd.merge(df_lpGBTs, df_Nchips, how='inner', on="DTC_CMSSW_Id")
	df.rename(columns = {'LpGBT_Id':'N_lpGBTs'}, inplace = True)
	df.rename(columns = {'N_Chips_Per_Module':'N_CROCs'}, inplace = True)
	return df

# new visualizer of IT plot 
# code based on example found online on how to draw a polar bar chart  
# https://www.learnui.design/tools/data-color-picker.html#palette
def drawITMap() :
	df = countITChips()
	df['Id']=df.index
	# sort values by number of CROCs
	df = df.sort_values(by=['N_CROCs'])
	# Get key properties for colours and labels
	max_value_full_ring = max(df['N_CROCs'])

	ring_colours = ['#003f5c','#2f4b7c','#665191'
			,'#a05195'
			,'#d45087'
			,'#f95d6a'
			,'#ff7c43'
			,'#ffa600']

	ring_labels = [f'   DTC_{x}  ({v}) ' for x, v in zip(list(df['Id']), 
													list(df['N_CROCs']))]
	data_len = len(df)

	# Begin creating the figure
	fig = plt.figure(figsize=(4,4), linewidth=10,
					edgecolor='#393d5c', 
					facecolor='#25253c')

	rect = [0.1,0.1,0.8,0.8]

	# Add axis for radial backgrounds
	ax_polar_bg = fig.add_axes(rect, polar=True, frameon=False)
	ax_polar_bg.set_theta_zero_location('N')
	ax_polar_bg.set_theta_direction(1)

	# Loop through each entry in the dataframe and plot a grey
	# ring to create the background for each one
	for i in range(data_len):
		ax_polar_bg.barh(i, max_value_full_ring*1.5*np.pi/max_value_full_ring, 
						color='grey', 
						alpha=0.1)
	# Hide all axis items
	ax_polar_bg.axis('off')
		
	# # Add axis for radial chart for each entry in the dataframe
	ax_polar = fig.add_axes(rect, polar=True, frameon=False)
	ax_polar.set_theta_zero_location('N')
	ax_polar.set_theta_direction(1)
	ax_polar.set_rgrids(np.linspace(0,27,num=28), 
						labels=ring_labels, 
						angle=0, 
						fontsize=4, fontweight='bold',
						color='white', verticalalignment='center')

	# Loop through each entry in the dataframe and create a coloured 
	# ring for each entry
	for i in range(data_len):
		clr = int( (list(df['N_CROCs'])[i])/100) 
		ax_polar.barh(i, list(df['N_CROCs'])[i]*1.5*np.pi/max_value_full_ring, 
					color=ring_colours[clr] )


	# Hide all grid elements for the    
	ax_polar.grid(False)
	ax_polar.tick_params(axis='both', left=False, bottom=False, 
					labelbottom=False, labelleft=True)

	plt.show()
def countModules(pLayoutId = referenceLayout , modType = "PS10G") :
	cMap = getCablingMap(pLayoutId)
	df = cMap.loc[:, ['DTC CMSSW Id']]
	
	df['Module Count'] = np.zeros(len(cMap))
	df = df.loc[ cMap['DTC name'].str.contains(modType)].groupby(["DTC CMSSW Id"]).count().sort_values(by=['DTC CMSSW Id']) 
	return df;