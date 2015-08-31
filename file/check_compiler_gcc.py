##coding:UTF-8

import os
import os.path
import subprocess as subp
import sys
import thread
import os
import time
import multiprocessing

# Config ##############################################
CCCACHE='/SEIDISK/huwx/cache'
CCGIT='/home/huwx/workspace/bugpercommit/multi-proc-ver/CC.git.pool/CC.git.'
CCBUILD='/home/huwx/workspace/bugpercommit/multi-proc-ver/CC.build.pool/CC.build.'
TMPDIR='/tmp'
CFILES='/SEIDISK/chenjj/compiler/study/data/filtering/CC_all_fault_files'
CCBRANCHES=['']
CCCONFIGARG='--enable-languages=c --disable-multilib --disable-shared LIBS=\'-ldl\' LDFLAGS=\'-ldl\' --with-gmp=/usr/local/gmp/ --disable-bootstrap'
CCFLAG='CC=/home/huwx/bin/CC454d CXX=/home/huwx/bin/g++454d'
CURRENTCOMMIT="none"
CONF='/home/huwx/workspace/llvmcommitcheck/git.pool/llvm.git.' #path to configure
INFOLEVEL=0
BINPATH='/usr/bin'
SYSCC='/usr/local/bin/clang'
OPTARGS=['O0','O1','O2','O3','Os']
SAVEFILE="saveddata.csv"
TASKPRE=-1
TASKBASE=0
TASKMAX=7

CURRENTBRANCH='origin/master'
#SEARCHL='1d7b6409e16a5f9925f536d6555be7781a77e19c' #before 4.8.0
#SEARCHL='963aee263572d7e10e1a762de6e8f1725ee393ee'
#SEARCHL='29928c8fee76feb1c82fe9bb3c71b90f99ab5600' #before 4.7
SEARCHL='e19b015b3704b257a924a632fea2b7e85799052b' #before 4.5
#SEARCHR='2fdc28c460f5a49317962c85fe09f0a3794a8faa' #before 4.6
SEARCHR='d85e75d718353f08643c815b76dfbb8d1a3d4530' #before 4.4

#branch of 4.4
# CURRENTBRANCH="origin/CC-4_4-branch"
# SEARCHL='caec3e6702a2de35f632d0f1bd39af02182df0f2'
# SEARCHR='51a24d9c5dbd1c57edd1e424e9e3d2ff7d51c69b'

#branch of 4.6
#CURRENTBRANCH="origin/CC-4_6-branch"
#SEARCHL='632cb4d5f22f598d1395fbae90a10fb679e06054'
#SEARCHR='2fdc28c460f5a49317962c85fe09f0a3794a8faa'

# global
BDCC=multiprocessing.Manager().list([])
CCBLACKLIST=multiprocessing.Manager().list([])
BDCCLOCK=multiprocessing.Lock()
SEQCACHE=set() # for quick cache

def printd(*output):
	global TASKPRE
	out=''
	for e in output:
		if out!='':
			out+='\t'
		out+=str(e)
	print TASKPRE,out

def checkPerCfile(pathtocfile,begin,end,cmtlist,first=False,ml=True,mr=True):
	global SEQCACHE,BDCCLOCK,CACHEWINDOW
	resl=ml
	resr=mr

	if first and (begin != end-1):
		for (b,e) in SEQCACHE:
			res=checkPerCfile(pathtocfile,b,e,cmtlist,first=True)
			if not res.startswith('u'):
				printd('result hit in cache!')
				return res

	mid=int((begin+end)/2)
	if first:
		CCl=getCC(begin,cmtlist)
		CCr=getCC(end,cmtlist)
		resl=compare(CCl,pathtocfile)
		resr=compare(CCr,pathtocfile)
		if resl and resr:
			return "uncertain-fixed(b:%d-e%d)"%(begin,end)
		else:
			if not resl and not resr:
				return "uncertain-persist(b:%d-e:%d)"%(begin,end)

	if begin == end-1:
		#first fixed commit
		SEQCACHE=set()
		SEQCACHE.add((begin,end))

		if resl and not resr:
			return 'f'+cmtlist[begin]+' '
		if not resl and resr:
			return 'i'+cmtlist[begin]+' '
		return 'uncertain(b:%d-e%d)'%(begin,end)

	CCm=getCC(mid,cmtlist)

	# this block code for skipping Built-failed CC version
	if CCm==False:
		r=checkPerCfile(pathtocfile,begin,int(begin+mid)/2,cmtlist,first=True)
		if r.startswith('u'):
			r1=checkPerCfile(pathtocfile,int(end+mid)/2,end,cmtlist,irst=True)
			if r1.startswith('u'):
				return 'b'+cmtlist[mid] # broken CC
			else:
			 return r1
		else:
			return r

	resm=compare(CCm,pathtocfile)

	printd(pathtocfile.strip().split('/')[-1],str(begin)+':'+str(resl),str(mid)+':'+str(resm),str(end)+':'+str(resr))

	r=""
	if ((not resl) and resm) or (resl and (not resm)):
		r+= checkPerCfile(pathtocfile,begin,mid,cmtlist,ml=resl,mr=resm)

	if ((not resm) and resr) or (resm and (not resr)):
		r+= checkPerCfile(pathtocfile,mid,end,cmtlist,ml=resm,mr=resr)
	return r

def getCC(no,cmtlist):
	global CCCACHE,BDCC,BDCCLOCK,TASKPRE,CCBLACKLIST
	pathtoCC=CCCACHE+'/'+cmtlist[no]+'/usr/local/bin/CC'
	if os.path.exists(pathtoCC):
		printd('CC in Cache Hit!')
		return pathtoCC
	else:
		BDCCLOCK.acquire()
		buildingflag=False
		if cmtlist[no] not in BDCC:
			BDCC.append(cmtlist[no])
			buildingflag=True
		else:
			buildingflag=False
		BDCCLOCK.release()

		if buildingflag:
			start = time.time()
			checkoutCommit(cmtlist[no])
			compileCC(no,cmtlist)

			BDCCLOCK.acquire()
			BDCC.remove(cmtlist[no])
			BDCCLOCK.release()

			end = time.time()
			printd('Build CC for',end-start)
			if os.path.exists(pathtoCC):
				printd('Build OK',cmtlist[no])
				return pathtoCC
			else:
				CCBLACKLIST.append(cmtlist[no])
				return False
		else:
			printd('Wait for buiding ',cmtlist[no])
			while not os.path.exists(pathtoCC) and cmtlist[no] not in CCBLACKLIST:
				time.sleep(30)
			time.sleep(10)
			if cmtlist[no] in CCBLACKLIST:
				return False
			return pathtoCC


def compare(pathtoCC,pathtocfile):
	global TMPDIR,OPTARGS,TASKPRE,SYSCC
	exccmd("rm `find %s 2>/dev/null | grep [%s]O[0-9][.]ccout`"%(TMPDIR,TASKPRE))
	CCcmd="export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && timeout 300 %s %s -I/home/huwx/tool/csmith-2.2.0/runtime -O0 -o %s/%sO9.ccout 2>&1  1>/dev/null && timeout 300 %s/%sO9.ccout > %s/%sO9.ccout.txt "%(SYSCC,pathtocfile,TMPDIR,str(TASKPRE),TMPDIR,str(TASKPRE),TMPDIR,str(TASKPRE))
	r=exccmd(CCcmd)
	for opt in OPTARGS:
		CCcmd="export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && timeout 300 %s %s -I/home/huwx/tool/csmith-2.2.0/runtime -%s -o %s/%s.ccout 2>&1  1>/dev/null && timeout 300 %s/%s.ccout > %s/%s.ccout.txt "%(pathtoCC,pathtocfile,opt,TMPDIR,str(TASKPRE)+opt,TMPDIR,str(TASKPRE)+opt,TMPDIR,str(TASKPRE)+opt)
		r=exccmd(CCcmd)
		r=exccmd("diff %s/%sO9.ccout.txt %s/%s%s.ccout.txt 2>&1"%(TMPDIR,TASKPRE,TMPDIR,TASKPRE,opt))
		if len(r)>0:
			printd(r)
		if len(r)!=0:
			return False
	return True

def compileCC(no,cmtlist):
	#warning! Should think about the dir path.
	global CCCACHE,CCGIT,CCBUILD,CCCONFIGARG,CURRENTBRANCH,INFOLEVEL,TASKPRE,CCBLACKLIST
	commit=cmtlist[no]
	last_commit=cmtlist[no+1]

	if commit in CCBLACKLIST:
		printd(commit,'in blacklist')
		return False

	CURRENTCOMMIT=commit
	if INFOLEVEL==0:
		r=exccmd('cd %s && git log | grep ^commit  2>/dev/null'%(CCGIT))
		if r[0].split(' ')[0]!=last_commit:
			printd('Warning! Commit version not right')
	else:
		r=[]
		r.append(CURRENTCOMMIT)
	printd('configuring CC:',commit)

	r=exccmd('cd %s && rm -rf * 2>/dev/null && %s/configure %s 2>/dev/null && rm ./config.cache 2>/dev/null'%(CCBUILD,llvmGIT,FLAG))
	printd('buiding CC.')
	r=exccmd('export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && export PATH=%s:$PATH && cd %s && make -j 16 2>/dev/null'%(BINPATH,CCBUILD),10000)
	printd('build complete:',commit)

	printd('installing to: %s/%s'%(CCCACHE,CURRENTCOMMIT))
	r=exccmd('cd %s && make install DESTDIR=%s/%s  2>/dev/null'%(CCBUILD,CCCACHE,CURRENTCOMMIT))
	if os.path.exists('%s/%s/usr/local/bin/CC'%(CCCACHE,CURRENTCOMMIT)):
		printd('install done:',commit)
		return True
	else:
		printd(TASKPRE,"install failed")
		return False

def checkoutCommit(commit):
	global CCGIT,CURRENT_BRANCH
	r=exccmd('rm %s/.git/index.lock 2>/dev/null'%(CCGIT))
	printd('checkout commit:',commit)
	r=exccmd('cd %s && git checkout %s -f 2>/dev/null'%(CCGIT,commit))

	for e in r:
		if e.find('done')>-1:
			printd('checkout done')
			return True
	printd('checkout failed')
	return False

def dumpBranchList():
	global CCGIT
	printd('dump all branches names from',CCGIT)
	r=exccmd('cd %s && git branch -a 2>/dev/null'%(CCGIT))
	return r
	
def dumpBranchCommit(branch):
	global CCGIT
	r=exccmd('rm %s/.git/index.lock 2>/dev/null'%(CCGIT))
	printd('checking out branch:',branch)
	r=exccmd('cd %s && git checkout %s -f 2>/dev/null'%(CCGIT,branch))
	printd('command return lines:',len(r))
	r=exccmd('cd %s && git status  2>/dev/null'%(CCGIT))

	BRANCH_EXIST=False
	for e in r:
		if e.find(branch)>=0 :
			printd('checkout done with branch:',branch)
			BRANCH_EXIST=True
			break

	if not BRANCH_EXIST:
		printd('checkout error:',branch)
		return []

	r=exccmd('cd %s && git log | grep ^commit  2>/dev/null'%(CCGIT))
	rr=[]
	for e in r:
		rr.append(e.split(' ')[1])
	printd('branch total commit:',len(rr))
	del r
	return rr

def exccmd(cmd, limit=-1):
		p=os.popen(cmd,"r")
		rs=[]
		line=""
		while True:
			line=p.readline()
			if not line:
				break
			#print line
			if(limit==-1 or len(rs)<limit):
				rs.append(line.strip())
			else:
				rs.pop(0)
				rs.append(line.strip())
		return rs

def branchTurnPoint():
	a=dumpBranchCommit('origin/master')
	b=dumpBranchCommit('origin/CC-4_2-branch')
	i=-1
	while a[i]==b[i]:
		i-=1
	print i

def task(procID,files,bdCCl,bdCClock,blacklist,cache):
	global CCGIT,CURRENTBRANCH,SAVEFILE,SEARCHL,SEARCHR,CCBUILD,TASKPRE,BDCC,BDCCLOCK,CCBLACKLIST,SEQCACHE
	#set config
	CCGIT=CCGIT+str(procID)
	CCBUILD=CCBUILD+str(procID)
	TASKPRE=str(procID)
	SAVEFILE=SAVEFILE+TASKPRE
	BDCC=bdCCl
	BDCCLOCK=bdCClock
	CCBLACKLIST=blacklist
	SEQCACHE=cache

	if len(files)==0:
		return

	printd('task begin.')

	commitlist=dumpBranchCommit(CURRENTBRANCH)
	if len(commitlist)==0:
		printd("load commit failed")
		return

	l=r=-1
	for i in range(0,len(commitlist)):
		if commitlist[i]==SEARCHL:
			l=i
		if commitlist[i]==SEARCHR:
			r=i
	if l<0:
		l=0

	if l>=r or l<0 or r<0:
		printd('commit range not legal!!!',l,r)
		return
		
	commitlist=commitlist[l:r+1]
	fcnt=0

	for f in files:
		printd('%s,%f\n'%(f.split('/')[-1],(fcnt*1.0/len(files))))
		cmt=checkPerCfile(f,0,len(commitlist)-1,commitlist,True)
		fcnt+=1
		printd('%s,%s,%f\n'%(f.split('/')[-1],cmt,(fcnt*1.0/len(files))))
		datafile=open(SAVEFILE,'a')
		datafile.write('%s,%s\n'%(f,cmt))
		datafile.close()

	printd('task end.')

def fixcommit(GIT,commit):
	global CCGIT
	CCGIT=GIT
	checkoutCommit(commit)

def main():
	global CURRENTBRANCH,CFILES,SAVEFILE,SEARCHL,SEARCHR,TASKMAX,BDCC,BDCCLOCK,CCBLACKLIST,SEQCACHE,TASKBASE

	print 'ZZ_CHECK_COMPILER_SYSTEM - START 2015'
	print '########## STEP 1: Loading data ############'
	print 'loading files.'
	files=exccmd('find %s | grep ".c$"'%(CFILES))
	pfiles=[[] for i in range(0,TASKMAX)]

	labledfile=set()
	for i in range(0,10):
		if not os.path.exists(SAVEFILE+str(i)):
			continue
		datafile=open(SAVEFILE+str(i),"r")
		data=datafile.readlines()
		datafile.close()
		for d in data:
			labledfile.add(d.split(',')[0].strip())

	print 'Source file total:',len(files)
	print 'Checked file total:',len(labledfile)
	j=0
	for f in files:
		if f in labledfile:
			continue
		pfiles[j].append(f)
		j+=1
		j%=TASKMAX
		
	print '########## STEP 2: Mission Start ############'
	proc=[]	
	for i in range(0+TASKBASE,TASKMAX+TASKBASE):
		print 'Task:',i,'Files:',len(pfiles[i-TASKBASE])
		p=multiprocessing.Process(target=task,args=(i,pfiles[i-TASKBASE],BDCC,BDCCLOCK,CCBLACKLIST,SEQCACHE))
		proc.append(p)
		p.start()
		time.sleep(5)

	for p in proc:
		if p.is_alive():
			p.join()

	print '########## FINISHED ############'
	print 'Total:',len(files),'Found:',exccmd('cat %s | wc -l'%(SAVEFILE)),'Classes:',len(SEQCACHE)

if __name__=="__main__":
	main()
