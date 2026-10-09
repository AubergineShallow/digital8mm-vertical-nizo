#include <cmath>
#include <algorithm>
extern "C" void raster(int n,const double* pts,const unsigned char* colors,int w,int h,unsigned char* image,double* depth){
for(int i=0;i<n;i++){
 const double* p=pts+9*i; double ax=p[0],ay=p[1],bx=p[3],by=p[4],cx=p[6],cy=p[7];
 double det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy); if(fabs(det)<1e-10)continue;
 int x0=std::max(0,(int)floor(std::min({ax,bx,cx}))),x1=std::min(w-1,(int)ceil(std::max({ax,bx,cx})));
 int y0=std::max(0,(int)floor(std::min({ay,by,cy}))),y1=std::min(h-1,(int)ceil(std::max({ay,by,cy})));
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){
 double u=((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/det;
 double v=((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/det;
 if(u< -1e-8||v< -1e-8||u+v>1.00000001)continue;
 double z=u*p[2]+v*p[5]+(1-u-v)*p[8];int k=y*w+x;
 if(z<depth[k]){depth[k]=z;for(int c=0;c<3;c++)image[3*k+c]=colors[3*i+c];}
 }
}}
