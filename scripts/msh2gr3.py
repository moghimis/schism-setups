import pickle
#from pylab import *

class gr3():
  nodesxy={}
  depths={}
  lonlat={}
  elements={}
  openboundary_nodes=[]
  num_openboundary_nodes=0
  land_nodes=[]
  num_land_nodes=0
  island_nodes=[]
  num_island_nodes=0
  def set_nodes_and_elements(self,nodes={},elements=[],depth=10.0):
    self.nodesxy=nodes
    for id in self.nodesxy:
      self.depths[id] = depth
    for ielement,element in enumerate(elements):
      self.elements[ielement+1]=element

  def signed_area(self,nodelist):
    x1,y1 = self.nodesxy[nodelist[0]]
    x2,y2 = self.nodesxy[nodelist[1]]
    x3,y3 = self.nodesxy[nodelist[2]]
    return ((x1-x3)*(y2-y3)-(x2-x3)*(y1-y3))/2.0

  def import_mesh(self,mesh,depth=10.):
    self.nodesxy=mesh.nodes
    for id in self.nodesxy:
      self.depths[id] = depth
    for ielement,element in enumerate(mesh.elements):
      self.elements[ielement+1]=element

    id = mesh.labelids['landbdy']
    self.num_land_nodes=mesh.linelengths[id]
    self.land_nodes=mesh.lines[id]

    if 'openbdy' in mesh.labelids:
      id = mesh.labelids['openbdy']
      self.num_openboundary_nodes=mesh.linelengths[id]
      self.openboundary_nodes=mesh.lines[id]
    else:
      self.num_openboundary_nodes=0
      self.openboundary_nodes=[]

    if 'islandbdy' in mesh.labelids:
      id = mesh.labelids['islandbdy']
      self.num_island_nodes=mesh.linelengths[id]
      self.island_nodes=mesh.lines[id]
    else:
      self.num_island_nodes = 0
      self.island_nodes=[]

    # remove island boundaries with length=2
    island_nodes = self.island_nodes
    self.island_nodes=[]
    self.num_island_nodes=0
    for nlist in island_nodes:
      if len(nlist)>2:
        self.island_nodes.append(nlist)
        self.num_island_nodes+=len(nlist)
      else:
        for nidx in nlist:
          try:
            del self.nodesxy[nidx]
            del self.depths[nidx]
            print "remove hanging node %d"%nidx
          except:
            print "could not find node %d"%nidx
          
    # remove hanging nodes
    #nodesxy=dict(self.nodesxy)
    #for idx in nodesxy:
    #  found=False
    #  for elidx in self.elements:
    #    if idx in self.elements[elidx]:
    #      found=True
    #      break
    #  if not(found):
    #    print "remove hanging node %d"%idx
    #    try:
    #      del self.nodesxy[idx]
    #    except:
    #      pass

  def renumber_nodes(self):
    newids = {}
    for newid,oldid in enumerate(self.nodesxy):
      newids[oldid]=newid+1
    
    oldxy=dict(self.nodesxy)
    self.nodesxy={}
    for elid in oldxy:
      self.nodesxy[newids[elid]] = oldxy[elid]

    olddepths=dict(self.depths)
    self.depths={}
    for elid in olddepths:
      self.depths[newids[elid]] = olddepths[elid]

    for elid in self.elements:
      self.elements[elid] = [newids[oldid] for oldid in self.elements[elid][::-1]]
      # check for counter-clockwise sequence:
      area = self.signed_area(self.elements[elid]) 
      if area < 0.0:
        print('  negative area for element %d: %0.2f, reversing nodes'%(elid,area))
        self.elements[elid] = [ nid for nid in self.elements[elid][::-1]]
      else:
        print(' area for element %d: %0.2f'%(elid,area))
    for elid in range(len(self.land_nodes)):
      self.land_nodes[elid] = [newids[oldid] for oldid in self.land_nodes[elid]]
    for elid in range(len(self.openboundary_nodes)):
      self.openboundary_nodes[elid] = [newids[oldid] for oldid in self.openboundary_nodes[elid]]
    for elid in range(len(self.island_nodes)):
      self.island_nodes[elid] = [newids[oldid] for oldid in self.island_nodes[elid]]


  def dump(self,filename='hgrid.gr3'):
    f = open(filename,'w')
    f.write('%s\n'%filename)
    f.write('%d %d\n'%(len(self.elements),len(self.nodesxy)))
    #f.write('%d\n'%len(self.nodesxy))
    for node in self.nodesxy:
      f.write('%d %0.2f %0.2f %0.2f\n'%(node,self.nodesxy[node][0],self.nodesxy[node][1],self.depths[node]))
    #f.write('%d\n'%len(self.elements))
    for el in self.elements:
      i,j,k = self.elements[el]
      f.write('%d 3 %d %d %d\n'%(el,i,j,k))
    # open boundary nodes
    f.write('%d = Number of open boundaries\n'%(len(self.openboundary_nodes)))
    f.write('%d = Total number of open boundary nodes\n'%self.num_openboundary_nodes)
    for sublist in self.openboundary_nodes:
      f.write('%d\n'%len(sublist))
      for node in sublist:
        f.write('%d\n'%node)
    
    # land nodes
    f.write('%d = Number of land boundaries\n'%(len(self.land_nodes) + len(self.island_nodes)))
    f.write('%d = Total number of land boundary nodes\n'%(self.num_land_nodes+self.num_island_nodes))
    for i,sublist in enumerate(self.land_nodes):
      f.write('%d 0 = Number of nodes for land boundary %d\n'%(len(sublist),i+1))
      for node in sublist:
        f.write('%d\n'%node)

    # island nodes
    for i,sublist in enumerate(self.island_nodes):
      f.write('%d 1 = Number of nodes for island boundary %d\n'%(len(sublist),i+1))
      for node in sublist:
        f.write('%d\n'%node)

    f.close()

  def nodes_in_elements(self):
    nodes=[]
    for (i,j,k) in self.elements:
      nodes.append(i)
      nodes.append(j)
      nodes.append(k)
    return list(set(nodes))

    
class msh():
  nodes={}
  elements=[]
  lines={}
  linelengths={}
  tmplines={}
  linelabels={}
  labelids={}
  sublist={}
  def __init__(self,filename):
    f=open(filename)
    mode='none'
    read=True
    while read:
      line=f.readline()
      #print('-%s-'%line.strip())
      if line.strip()=='$PhysicalNames':
        line=f.readline()
        num=int(line)
        for inum in range(num):
          line=f.readline()
          dat=line.split()
          self.lines[int(dat[1])] = []
          self.linelabels[int(dat[1])] = dat[2][1:-1] # cut off quotes
          self.labelids[dat[2][1:-1]]=int(dat[1])
      if line.strip()=='$Nodes':
        num=int(f.readline())
        for inum in range(num):
          line=f.readline()
          dat=line.split()
          self.nodes[int(dat[0])] = (float(dat[1]),float(dat[2]))
      if line.strip()=='$Elements':
        num=int(f.readline())
        for inum in range(num):
          line=f.readline()
          dat=line.split()
          id = int(dat[0])
          if dat[1] == '2': # assume area element
            numlabels=int(dat[2])
            self.elements.append([int(ii) for ii in dat[(3+numlabels):]])
          elif dat[1] == '1': # assume line element
            numlabels=int(dat[2])
            labelid=tuple([int(ii) for ii in dat[3:3+numlabels]])
            if not(self.tmplines.has_key(labelid)):
              self.tmplines[labelid]=[]
              
            self.tmplines[labelid].append([int(ii) for ii in dat[(3+numlabels):]])
  
        read=False
    # reduce lines to lists of points
    subkeys={}
    # go through whole list and get number of subkeys
    for key in self.tmplines:
      labelid=key[0]
      subid=key[1]
      if not(subkeys.has_key(labelid)):
        subkeys[labelid]=[]
      subkeys[labelid].append(subid)
      for subline in self.tmplines[key]:
        p1=subline[0]
        p2=subline[1]
        if self.sublist.has_key(subid):
          if p1 not in self.sublist[subid]:
            self.sublist[subid].append(p1)
          if p2 not in self.sublist[subid]:
            self.sublist[subid].append(p2)
        else:
          self.sublist[subid] = [p1,p2]
    for labelid in subkeys:
      self.linelengths[labelid] = 0
      subkeys[labelid] = list(set(subkeys[labelid]))
      for subkey in subkeys[labelid]:
        if not(self.lines.has_key(labelid)):
          self.lines[labelid]=[]
        self.lines[labelid].append(self.sublist[subkey])
        self.linelengths[labelid] += len(self.sublist[subkey])
      
if __name__ == '__main__':
  import sys
  if False:
    # read projection:
    pf = open('coast_proj.pickle','rb')
    m, = pickle.load(f)
    pf.close()

  if len(sys.argv)>1:
    filename=sys.argv[1]
  else:
    filename='coast.msh'
  mesh=msh(filename)
  hgrid=gr3()
  hgrid.import_mesh(mesh)
  print '  renumber nodes'
  hgrid.renumber_nodes()
  hgrid.dump('hgrid.gr3')



