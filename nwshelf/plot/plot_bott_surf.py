import netCDF4
import sys
import matplotlib
matplotlib.use('Agg')
from mpl_toolkits.basemap import Basemap
from pylab import *
import pickle,os
from netcdftime import utime

if len(sys.argv)>2:
  varname = sys.argv[2]
else:
  print('  usage: plot_bott_surf.py file.nc variable')
  sys.exit(1)

if len(sys.argv)>3:
  tidx=int(sys.argv[3])
else:
  tidx=-1

nc = netCDF4.Dataset(sys.argv[1])
ncv = nc.variables

lon = ncv['SCHISM_hgrid_node_x'][:]
lat = ncv['SCHISM_hgrid_node_y'][:]
#sigma = ncv['sigma'][:]
#nsigma = len(sigma)
#bidx = ncv['node_bottom_index'][:]
nv = ncv['SCHISM_hgrid_face_nodes'][:,:3]-1
time = ncv['time'][:] # s
ut = utime(ncv['time'].units)
dates = ut.num2date(time)

lonb=[-18., 32.]
latb=[46., 67.]

if os.path.isfile('proj.pickle'):
    (proj,)=np.load('proj.pickle')
else:
    proj=Basemap(projection="merc", lat_ts=0.5*(latb[1]+latb[0]), resolution="h",llcrnrlon=lonb[0], urcrnrlon=lonb[1], llcrnrlat=latb[0], urcrnrlat=latb[1])
    f=open('proj.pickle','wb')
    pickle.dump((proj,),f)
    f.close()

x,y = proj(lon,lat)

var = ncv[varname]
#time = array([0.0])
cmap = cm.jet
#cmap.set_under(color='w')

def mask_triangles(masknodes,nv):
  idx = where(masknodes)[0]
  nvmask = []
  for nodes in nv:
    if any(in1d(nodes,idx)):
      nvmask.append(True)
    else:
      nvmask.append(False)
  return asarray(nvmask)

bidx = ncv['node_bottom_index'][:]
nbidx = len(bidx)

if tidx >= 0:
  dates = dates[tidx]
  tidx_offset=tidx
else:
  tidx_offset=0

os.system('mkdir -p jpgs')
for tidx,t in enumerate(dates):
  v = var[tidx+tidx_offset,:].squeeze()
  vb = v[bidx,arange(nbidx)]
  vs = v[-1,:].squeeze()
  #mask = v == -99.
  #mask = mask_triangles(mask,nv)
  if True:
    figure()
    tripcolor(x,y,nv,vs,cmap=cmap,rasterized=True)
    if varname=='salt':
      clim(5,35)
      cbtitle='surface salinity'
    elif varname=='temp':
      clim(1,6)
      cbtitle=u'surface temperature\n[\u00b0C]'
    proj.drawcoastlines()
    proj.fillcontinents((0.9,0.9,0.8))
    cb=colorbar()
    cb.ax.set_title('%s\n'%(ncv[varname].long_name),size=10.)
    tstring = t.strftime('%Y%m%d-%H%M')
    savefig('jpgs/%s_surface_%s.jpg'%(varname,tstring),dpi=200)
    close()
  
  figure()
  tripcolor(x,y,nv,vb,cmap=cmap,rasterized=True)
  if varname=='salt':
    clim(5,35)
    cbtitle='bottom salinity'
  elif varname=='temp':
    clim(1,6)
    cbtitle='bottom temperature\n[\u00b0C]'
  proj.drawcoastlines()
  proj.fillcontinents((0.9,0.9,0.8))
  cb=colorbar()
  cb.ax.set_title('%s\n'%(cbtitle),size=10.)
  tstring = t.strftime('%Y%m%d-%H%M')
  savefig('jpgs/%s_bottom_%s.jpg'%(varname,tstring),dpi=200)
  #show()
  close()

