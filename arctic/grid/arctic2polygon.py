from pylab import *
from mpl_toolkits.basemap import Basemap
from shapely import geometry as sg
import cPickle as pickle
    
def check_boundary(x,y,bdys, threshold=100.):
  xl,yl,xu,yu = bdys
  if (abs(x - xl)<threshold or abs(x - xu)<threshold or abs(y - yl)<threshold or abs(y - xu)<threshold):
    return True
  else:
    return False

# set surrounding points
xl=-50.0
xu=80.0
yu=89.0
yl=50.0

try:
  pf = open('coast_proj.pickle','rb')
  m, = pickle.load(pf)
  pf.close()
  write_pickle=False
except:
  write_pickle=True
  if True:
    m = Basemap(projection='npstere',boundinglat=55.,lon_0=0.0,resolution='i')
  else:
    m = Basemap(projection='lcc',
                       resolution='l',area_thresh=10.0,
                        llcrnrlon=xl,
                        llcrnrlat=yl,
                        urcrnrlon=xu,
                        urcrnrlat=yu,
                        lat_0=70.0,
                        lon_0=10.0)

  pf = open('coast_proj.pickle','wb')
  pickle.dump((m,),pf)
  pf.close()

mxu,myu=m(xu,yu)
mxl,myl=m(xl,yl)

# get coast polygon
polys = m.coastpolygons
land=[]
sland=[]
for (xp,yp),ctype in zip(polys,m.coastpolygontypes):
  if ctype<2:
    land.append(zip(xp,yp))
    sland.append(sg.Polygon(zip(xp,yp)))


ipynewland=[]
bdyp = []

uselines=False
usesplines=True
use_insurface=True

# define surrounding domain polygon
#surr_poly = [(xl,yl),(xl,yu),(xu,yu),(xu,yl)]

surr_poly = [(-40.,70.),(-130.,60.),(120.,50.),(50.,55.),(-10.,70.)]
surr_poly = [(-40.,70.),(-40.,85.),(88.,85.),(88,55.),(50.,55.),(-5.,68.)]

surr_poly = [(-40.,70.),(-40.,85.),(88.,85.),(67.88,76.43),(57.80,74.919),(53.539,71.758),(64.5519,68.018),(88,55.),(50.,55.),(-5.,68.)]

bdy_points = [[(-40.,85.),(88.,85.)],[(-5.,68.)]]

domain = sg.Polygon([ m(xx,yy) for xx,yy in surr_poly])
#domain = sg.Polygon([(mxl,myl),(mxl,myu),(mxu,myu),(mxu,myl)])

if False:
  f = figure()
  m.drawcoastlines()
  domain_points = [ m(xx,yy) for xx,yy in surr_poly]
  figure()
  for i,p in enumerate(land[:30]):
    x,y=zip(*p);x=list(x);y=list(y)
    plot(x,y,'-')
    plot(x[0],y[0],'ko'); text(x[0],y[0],str(i),size=10)
  #for x,y in domain_points:
  #  plot(x,y,'ro')

  show()

eissel_poly = [(5.39,53.1),(4.953,52.898),(4.84,52.07),(6.77,52.6)]
eissel = sg.Polygon([ m(xx,yy) for xx,yy in eissel_poly])

problems=[]
diffproblems=[]
# Shetland
#problems.append(sg.Polygon([(1798050,1605860),(1798200,1604500),(1800100,1605540),(1799640,1606520)]))

# Scotland
#problems.append(sg.Polygon([(1542200.,1147880),(1554980,1148680),(1553110,1161190),(1539810,1162520)]))

# Swine channel
#diffproblems.append(sg.Polygon([(2732320,872762),(2732820,871486),(2733060,871394),(2732540,872762)]))

# widely open Swine channel
#diffproblems.append(sg.Polygon([(2732880,871471),(2733790,867425),(2736680,867556)]))


water = domain
# take out the first land polygons
landnum=80
for i,p in enumerate(sland[:landnum]):
  #if i in [25,]: continue
  if domain.intersects(p):
    if domain.covers(p):
      print i,'skipped'
      continue
    water = water.difference(p)
    if not(water.geom_type == 'Polygon'):
      areas = asarray([g.area for g in water.geoms])
      idx = areas.argmax()
      water = water.geoms[idx]

# split the common polygon into land boundaries
landbdys=[]
open_boundary = water.boundary
for i,p in enumerate(sland[:landnum]):
  if water.intersects(p) and not(water.contains(p)):
    line = water.intersection(p)
    points=[]
    print i,p.geom_type
    open_boundary = open_boundary.difference(line)
    #if line.geom_type == 'Polygon':
    # points.append((g.boundary.xy[0][0],g.boundary.xy[1][0])) 
    if False:
      print 'we got a polygon'
    else: 
     for g in line.geoms:
      if g.geom_type == 'LineString' or g.geom_type == 'Point':
        points.append((g.xy[0][0],g.xy[1][0]))
      else:
        print(g.geom_type)
        points.append((g.boundary.xy[0][0],g.boundary.xy[1][0]))
    landbdys.append(points[::-1][1:])

splines=list(landbdys)
for l,p in zip(land[0:],sland[0:]):
  if water.contains(p):
    for problem in problems:
      if problem.intersects(p):
        p = p.union(problem)
        xx,yy = p.boundary.xy
        l = zip(xx,yy)
    for diffproblem in diffproblems:
      if diffproblem.intersects(p):
        p = p.difference(diffproblem)
        xx,yy = p.boundary.xy
        l = zip(xx,yy)
    splines.append(l)

if False:
  f = open('problem_areas.txt','w')
  f.write('# problems, to be joined with island splines\n')
  for problem in problems:
    xx,yy = problem.boundary.xy
    f.write('%s\n'%str(m(xx,yy,inverse=True)))
  f.write('# problems, to be removed (difference) from island splines\n')
  for diffproblem in diffproblems:
    xx,yy = diffproblem.boundary.xy
    f.write('%s\n'%str(m(xx,yy,inverse=True)))
  f.write('# lake eissel\n')
  f.write('%s\n'%str(eissel_poly))
  f.close()

if True:
  xw,yw = water.boundary.xy
  ratio = (m.ymax-m.ymin)/(m.xmax-m.xmin)
  dpi=200
  width=4.0
  #lonw,latw = m(xw,yw,inverse=True)
  #newland.append(zip(xw,yw))
  f = figure(figsize=(width,width*ratio),dpi=dpi)
  f.subplots_adjust(left=0.0,bottom=0.0,right=1.0,top=1.0)
  m.drawcoastlines()
  m.plot(xw,yw)
  savefig('map.png',dpi=dpi)
  f = open('oxy_dxy_nxy.pickle','wb')
  dx = (m.xmax-m.xmin)/(width*dpi)
  dy = (m.ymax-m.ymin)/(width*ratio*dpi)
  pickle.dump((m.xmin,m.ymin,dx,dy,int(width*dpi),int(width*ratio*dpi)),f)
  f.close()
  show()

if True:
  figure()
  for i,p in enumerate(splines):
    x,y=zip(*p);x=list(x);y=list(y)
    plot(x,y,'-')
    plot(x[0],y[0],'ko'); text(x[0],y[0],str(i),size=10)
  #plot(x[90:100],y[90:100],'o',color='k',ms=6.0)
  show()

class Points():
  i=1
  num=0
  xyres={}
  def __initialize__(self):
    self.i=1
    self.num=0
    self.xyres={}

  def add(self,x,y,res=1000.):
    if not(type(res)=='str'):
      resstr=str(res)
    else:
      resstr=res
    self.xyres[self.i]=(x,y,resstr)
    self.i+=1
    self.num+=1
    return self.i-1

  def dump(self,f):
    for id in self.xyres:
      x,y,res = self.xyres[id]
      f.write('Point(%d) = {%0.2f, %0.2f, %0.2f, %s};\n'%(id,x,y,0.0,res))

  def modify(self,id,res=None,x=None,y=None):
    xo,yo,reso = self.xyres[id]
    if not(res==None):
      reso=res
    self.xyres[id]=(xo,yo,reso)

class PointsItem(list):
  type=None
  id=-1
  closed=False
  last=None
  def __init__(self,id,type,closed=False,last=None):
    self.container=[]
    self.id=id
    self.closed=closed
    self.last=last
    if type=='spline':
      self.type='spline'
    elif type=='line':
      self.type='line'
    elif type=='lineloop':
      self.type='lineloop'
      self.closed=True

  def dump(self,f):
    if self.type=='spline':
      f.write('BSpline(%d)={'%self.id)
      points = self
      if self.closed:
        points.append(self[0])
      for item in points[:-1]:
        f.write('%d,'%item)
      f.write('%d };\n'%points[-1])
      f.write('Line Loop(%d)={%d};\n'%(self.id,self.id))
    elif self.type=='line':
      f.write('Line(%d) = '%self.id)
      f.write('{ %d, %d };\n'%(self[0],self[1]))
    elif self.type=='lineloop':
      f.write('Line Loop(%d) = {'%self.id)
      for item in self[:-1]:
        f.write('%d, '%item)
      f.write('%d };\n'%self[-1])

class PointsItems(list):
  num=0
  def __init__(self):
    self.num=0
    self.container=[]
  def add(self,itemtype,closed=False,last=None):
    self.num+=1
    s = PointsItem(id=self.num,type=itemtype,closed=closed,last=last)
    self.append(s)
    return s
  def getbyid(self,id):
    found = False
    for s in self:
      if s.id == id:
        found = True
        break
    if found:
      return s
    else:
      return None

insurface=[]
points = Points()

# hold lists of land, island, and open boundary
landbdy=[]
islandbdy=[]
openbdy=[]

# make lists of point indizes for lines and splines
items=PointsItems()
surface=[]
boundary=[]
s=None
landnum=len(landbdys)

# add openbdy splines
for g in open_boundary.geoms:
  l = items.add('spline')
  xx,yy = g.xy
  for x,y in zip(xx,yy):
    l.append(points.add(x,y,'bres'))
  openbdy.append(l.id)
  boundary.append(l.id)

for i,spline in enumerate(splines):
  s=items.add('spline',last=s)
  for p in spline:
    s.append(points.add(p[0],p[1],'cres'))

  if i>=landnum:
    # assume island
    s.closed=True
    surface.append(s)
    islandbdy.append(s.id)
  else:
    boundary.append(s.id)
    landbdy.append(s.id)

s=items.add('lineloop')
s.extend(boundary)
surface.append(s)

#dump data into .poly file:
f=open('coast.geo','w')
f.write("""
Mesh.CharacteristicLengthFromPoints = 1;
Mesh.CharacteristicLengthExtendFromBoundary = 0;
""")
f.write('bres = %0.2f;\n'%4000.)
f.write('cres = %0.2f;\n'%4000.)

# set resolution at boundaries
for itemid in openbdy:
  for item in items:
    if item.id == itemid:
      break
  for pointid in item:
    points.modify(pointid,res='bres')

points.dump(f)

for item in items:
  item.dump(f)

surfaceid = items.num+1
f.write('Plane Surface(%d) = {'%surfaceid)
for item in surface[:-1]:
   f.write('%d, '%(item.id))
f.write('%d };\n'%surface[-1].id)
f.write('Physical Surface("water") = {%d};\n'%surfaceid)

if use_insurface:
  for ip in insurface:
    f.write('Point {%d} In Surface {%d};\n'%(ip,surfaceid))

# write physical groups
f.write('Physical Line("islandbdy") = {')
for item in islandbdy[:-1]:
  f.write('%d, '%item)
f.write('%d };\n'%islandbdy[-1])

f.write('Physical Line("landbdy") = {')
for item in landbdy[:-1]:
  f.write('%d, '%item)
f.write('%d };\n'%landbdy[-1])

f.write('Physical Line("openbdy") = {')
for item in openbdy[:-1]:
  f.write('%d, '%item)
f.write('%d };\n'%openbdy[-1])

# write land bdy list for zooming
coast=landbdy
coast.extend(islandbdy)
coastlist = str(coast)[1:-1]

f.write("""
Field[1] = MathEval;
Field[1].F = "4000.";

Field[2] = Restrict;
Field[2].IField = 1;
Field[2].EdgesList = {%s};

Background Field = 1;
"""%(coastlist))

f.close()

#if write_pickle:
#  pf = open('coast_proj.pickle','wb')
#  pickle.dump((m,),pf,protocol=-1)
#  pf.close()
