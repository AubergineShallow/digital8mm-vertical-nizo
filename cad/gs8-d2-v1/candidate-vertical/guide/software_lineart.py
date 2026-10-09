"""CPU triangle Z-buffer adapter for inherited image-space line-art style. No display server."""
import ctypes,subprocess
from pathlib import Path
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy
P=Path(__file__).parent
libpath=P/'raster.so'
if not libpath.exists() or libpath.stat().st_mtime<(P/'raster.cpp').stat().st_mtime:subprocess.run(['g++','-O3','-shared','-fPIC',str(P/'raster.cpp'),'-o',str(libpath)],check=True)
lib=ctypes.CDLL(str(libpath));ptr=ctypes.c_void_p
lib.raster.argtypes=[ctypes.c_int,ptr,ptr,ctypes.c_int,ctypes.c_int,ptr,ptr]
def render(polys,cam,W,H,zbuf=False):
    img=np.full((H,W,3),255,dtype=np.uint8);z=np.full((H,W),1e9,dtype=np.float64)
    for poly,off in polys:
        v=vtk_to_numpy(poly.GetPoints().GetData()).astype(float)+np.asarray(off)
        faces=vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1,4)[:,1:]
        xy=cam.project(v);depth=2000-cam.depth(v)
        p=np.ascontiguousarray(np.column_stack((xy,depth))[faces],dtype=np.float64)
        colors=np.ascontiguousarray(vtk_to_numpy(poly.GetCellData().GetScalars()),dtype=np.uint8)
        lib.raster(len(faces),p.ctypes.data,colors.ctypes.data,W,H,img.ctypes.data,z.ctypes.data)
    return img,z if zbuf else None
