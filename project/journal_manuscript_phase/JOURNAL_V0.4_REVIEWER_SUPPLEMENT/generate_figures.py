"""Reproduce the four paper figures from distributed data. Offline; no experiments."""
from pathlib import Path
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent; DATA=HERE/'figure_source_data'; OUT=HERE/'figures'; OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':11,'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})
INK='#182838'; BLUE='#226D93'; ORANGE='#A65D16'; PALE='#EAF2F6'; GRAY='#5A6670'; LIGHT='#F3F5F6'
obs={x['case_id']:x for x in json.loads((DATA/'observations.json').read_text())}
def finish(fig,name):
    for ext in ['pdf','svg','png']:
        kw={'dpi':300} if ext=='png' else {}
        if ext=='pdf':kw['metadata']={'Title':name.replace('_',' '),'Author':'','CreationDate':None,'ModDate':None}
        fig.savefig(OUT/(name+'.'+ext),bbox_inches='tight',pad_inches=.12,**kw)
    plt.close(fig)
def box(ax,x,y,w,h,title,body='',fc=LIGHT,fs=10):
    ax.add_patch(Rectangle((x,y),w,h,edgecolor=GRAY,facecolor=fc,lw=.8))
    ax.text(x+w/2,y+h*.68,title,ha='center',va='center',fontsize=fs,fontweight='bold',color=INK)
    if body:ax.text(x+w/2,y+h*.32,body,ha='center',va='center',fontsize=fs-1,color=INK,linespacing=1.3)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,color=GRAY,lw=.9))

# Figure 1: definitions in mechanism panels; each numeric row is one root/snapshot.
with (DATA/'numeric_observations.csv').open() as f:numeric=list(csv.DictReader(f))
fig=plt.figure(figsize=(10.2,7.4)); gs=fig.add_gridspec(2,3,height_ratios=[1.05,1.7],hspace=.32,wspace=.27,bottom=.25,top=.97)
for j,(title,body) in enumerate([
('Compound\nSelective propagation','Value uses A and B\nReturned timestamp = tB'),
('Vetro\nOldest-required','Value uses A / B\nReturned timestamp = min(tA, tB)'),
('Asymmetry\nOldest-required','Value uses A × B\nReturned timestamp = min(tA, tB)')]):
    ax=fig.add_subplot(gs[0,j]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,.03,.35,.94,.59,title,body,PALE,9.5)
    ax.text(.5,.13,'Coverage rule; no adequacy judgment',ha='center',fontsize=8,color=GRAY,wrap=True)
for j,(protocol,label) in enumerate([('compound-finance','Compound'),('vetro','Vetro'),('asymmetry','Asymmetry')]):
    ax=fig.add_subplot(gs[1,j]);rs=sorted([r for r in numeric if r['protocol']==protocol],key=lambda r:r['snapshot'])
    for y,r in enumerate(rs):
        a=float(r['reported_age'])/3600;b=float(r['effective_age'])/3600
        marker={'PRIMARY_EXECUTION':'o','SECONDARY_INFRASTRUCTURE_RECOVERY':'s','ANALYSIS_CORRECTED_EXISTING_EVIDENCE':'D'}[r['evidence_tier']]
        ax.plot([a,b],[y,y],color=GRAY,lw=1,zorder=1)
        ax.scatter([b],[y],marker=marker,s=80,color=BLUE,zorder=2)
        ax.scatter([a],[y],marker=marker,s=27,facecolor='white',edgecolor=ORANGE,lw=1.5,zorder=3)
        ax.annotate('gap '+format(int(r['signed_gap']),',')+' s',(max(a,b),y),xytext=(-1,13),textcoords='offset points',ha='right' if b>10 else 'left',fontsize=8)
    ax.set(yticks=[0,1,2],yticklabels=['T0','T1','T2'],xlim=(-.8,25),ylim=(2.45,-.65),xlabel='Publication age (hours)',title=label)
    ax.set_xticks([0,6,12,18,24]);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.18)
handles=[Line2D([],[],marker='o',linestyle='',markerfacecolor='white',markeredgecolor=ORANGE,label='Reported age'),Line2D([],[],marker='o',linestyle='',color=BLUE,label='Effective required-input age'),Line2D([],[],marker='s',linestyle='',color=GRAY,label='Secondary recovery'),Line2D([],[],marker='D',linestyle='',color=GRAY,label='Analysis correction')]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.105),ncol=2,frameon=False,fontsize=9)
fig.text(.5,.045,'18 planned root–snapshots: 9 readable in 3 families; 9 Silo reverts remain nonnumeric (NA).\nEach row is a fixed observation, not a duration or frequency estimate. Circles denote primary execution.',ha='center',fontsize=9,color=GRAY)
finish(fig,'figure_1_temporal_coverage')

# Figure 2: independently specified expectation, not an arrow deriving Y from richer observations.
fig,ax=plt.subplots(figsize=(10.2,6.7));ax.set(xlim=(0,10),ylim=(0,7));ax.axis('off')
box(ax,.4,5.95,9.2,.75,'Prospectively specified conditions and bound deployment','Legal histories, source/configuration predicates and fixed comparison pairs',PALE)
box(ax,.4,3.35,3.35,1.55,'Reference Y','Input acceptance\nReturn source\nTransition',LIGHT)
ax.text(2.075,2.8,'Specified before observed outputs;\nnot a complete second simulator',ha='center',fontsize=9,color=GRAY)
arrow(ax,(2.1,5.95),(2.1,4.95))
box(ax,4.25,4.9,5.35,.65,'Designated deployed execution','',LIGHT)
arrow(ax,(7,5.95),(7,5.57))
ax.add_patch(Rectangle((4.25,.95),5.35,3.6,edgecolor=GRAY,facecolor='white',lw=1))
ax.text(4.45,4.27,'O3  =  O2 + collected opcode trace',fontsize=10,fontweight='bold',color=INK)
ax.add_patch(Rectangle((4.5,1.35),4.85,2.45,edgecolor=BLUE,facecolor=PALE,lw=1))
ax.text(4.7,3.5,'O2  =  O1 + actual public context',fontsize=10,fontweight='bold',color=INK)
ax.text(4.7,2.96,'Pre/post getters, source/status/validity fields\nand declared public events',fontsize=9,color=INK)
box(ax,4.8,1.65,4.25,.85,'O1  =  complete primary return tuple','Includes Boolean fields where the ABI returns them','white',10)
arrow(ax,(7,4.9),(7,4.56))
ax.text(2.075,1.62,'Compare predeclared pairs:\nsame or different Y versus\nsame or different observation',ha='center',fontsize=10,color=INK)
arrow(ax,(3.6,2.02),(4.2,2.02))
ax.text(.4,.33,'Nested observation sets, not a ranking of scientific value. Public fields are never withheld from O2.\nObserved matrix: 11 predeclared O1 collisions separated by O2; no additional O3 separation.',fontsize=10,color=INK)
finish(fig,'figure_2_observation_contract')

# Figure 3: exact local return shapes; no cross-implementation numeric comparison.
fig,ax=plt.subplots(figsize=(11.4,6.7));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
headers=['Path / pair','Same complete O1','Execution A: public context','Execution B: public context']
data=[['Vesta\nVA1 / VA2','(10¹⁸)','status: 0 → 0\ncurrent price × current index','status: 0 → 1\ncached price × current index'],['Aurigami\nAA1 / AA2','(10³⁰)','isFromMainFeed = true\nmain selected','isFromMainFeed = false\nbackup selected'],['Fathom\nFC0 / FC1','(P, true)','delayed.timestamp = 1789370640\nlatest.timestamp = 1789372440','delayed.timestamp = 1789372440\nlatest.timestamp = 1789373340'],['Fathom\nFC2 / FC3','(P)','isPriceFresh = true\nisPriceOk = true','isPriceFresh = false\nisPriceOk = false']]
t=ax.table(cellText=data,colLabels=headers,colWidths=[.17,.17,.33,.33],cellLoc='left',loc='center',bbox=[0,.2,1,.78]);t.auto_set_font_size(False);t.set_fontsize(9)
for (r,c),cell in t.get_celld().items():
    cell.set_edgecolor('#CBD3D9');cell.set_linewidth(.6);cell.PAD=.065
    if r==0:cell.set_facecolor(PALE);cell.set_text_props(weight='bold',color=INK)
    elif r%2==0:cell.set_facecolor(LIGHT)
ax.text(0,.125,'P = 27936237197953895. Integer values use the deployed scaling; they are not cross-path price comparisons.',fontsize=9,color=GRAY)
ax.text(0,.075,'Vesta provenance follows bound semantics plus cache/status witnesses. These are local contrasts, not one shared state machine.',fontsize=9,color=GRAY)
ax.text(0,.025,'Fathom evidence is limited to FC0–FC3; the six planned pairs involving its unavailable history/failure arms remain NC.',fontsize=9,color=GRAY)
finish(fig,'figure_3_equal_return_contrasts')

# Figure 4: pipeline stages remain separate; literal timestamps from the included observations.
fig,ax=plt.subplots(figsize=(10.4,6.3));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
ids=['AA2','AA3','AA4']; labels=['Backup at read','One qualifying report','Second qualifying report']
for j,(cid,title) in enumerate(zip(ids,labels)):
    x=.02+j*.33;post=obs[cid]['O2']['post']
    box(ax,x,.79,.30,.16,cid+'\n'+title,'',PALE,10)
    body='Reporter 1 timestamp\n'+post['raw1'][1]+'\n\nReporter 2 timestamp\n'+post['raw2'][1]
    ax.text(x+.025,.735,body,va='top',fontsize=10,linespacing=1.32,color=INK)
    box(ax,x,.30,.30,.17,'Aggregate timestamp',post['main'][2],LIGHT,10)
    flag='true' if post['rawUnderlying'][2] else 'false'
    ax.text(x+.025,.255,'isFromMainFeed = '+flag+'\nReturn = 10³⁰',va='top',fontsize=10,linespacing=1.7,color=INK)
    if j<2:arrow(ax,(x+.304,.866),(x+.327,.866))
ax.text(.02,.07,'AA3: reporter record accepted; aggregate unchanged; backup retained.\nAA4: second report accepted; aggregate refreshed; main selected.',fontsize=10,color=INK)
ax.text(.02,-.01,'Record updates occur in the authorized setup prefix. The subsequent getUnderlyingPrice call is a pure read.',fontsize=9,color=GRAY)
finish(fig,'figure_4_aurigami_stages')
print('Created four figures in PDF, SVG and 300-dpi PNG from the distributed data.')
