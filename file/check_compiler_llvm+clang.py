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
# configuration changed in argsforllvm() function at line 45.
CCCACHE='/tmp/cache'
CCGIT=''
CCBUILD=''
TMPDIR='/tmp'
CFILES=''
CCBRANCHES=['']
CCCONFIGARG=''
CCFLAG=''
CURRENTCOMMIT="none"
CONF=''
INFOLEVEL=0
BINPATH='/usr/bin'
SYSCC='/usr/local/bin/clang'
OPTARGS=['O0','O1','O2','O3','Os']
SAVEFILE="saveddata.csv"
TASKPRE=-1
TASKBASE=0
TASKMAX=9

llvmcommitlst=[]
clangcmttime=[]
llvmcmttime=[]

CURRENTBRANCH=''

# global
BDCC=multiprocessing.Manager().list([])
CCBLACKLIST=multiprocessing.Manager().list([])
BDCCLOCK=multiprocessing.Lock()
SEQCACHE=set()

def argsforllvm():
	global CCCACHE,llvmGIT,clangGIT,CCBUILD,TMPDIR,CFILES,CCCONFIGARG,CONF,BINPATH,SAVEFILE,CURRENTBRANCH,CCGIT,SEARCHL,SEARCHR,CCFLAG
	global SEARCHLllvm,SEARCHRllvm
	global CCBLACKLIST
	print 'configuring for llvm'
	LLVMCMT={'26':'895a55e66d107aa96a1e763a62a97e8ad62284a0','27':'9a1ac4c107489b65d92c541acf182000818a900a','28':'bbfc31012bad41d1eda6d65c0081760e8fdbc323','29':'591432136c78ab61ac1233cb813077e4c7c2f25e','32':'08e9cb46feb0c8e08e3d309a0f9fd75a04ca54fb','33':'d2e0f7ee15e3df5317f804d9355c2b714e30b5c9','34':'36c7806f4eacd676932ba630246f88e0e37b1cd4','35':'434f0e3548ef346ddce6214eb7aba6f363bcc704'}
	CLANGCMT={'26':'e7925a075f110ab21afeae084670a155dea568e3','27':'da7914950fe4bab215f40265e3aaba9c489b1938','28':'26fc28d88e6ff0279e37074cc304e0cfe3e31714','29':'db93fdee6c5a24e86ee5ed8c1d3b597e17d5893b','32':'538fb98685522bb7234c693f12e82b8893e290ff','33':'c2fc4ab28c13ebc1da5828e12e638514d4d777dc','34':'a5131ab23d77936eecc793a1b7096b9383c0f792','35':'c61a708c63ab7b89a5b6c80bc37dd32824b2f2d8'}
	cmt={'llvm':LLVMCMT,'clang':CLANGCMT}

	CCCACHE='/home/huwx/workspace/llvmcommitcheck/cache'
	llvmGIT='/home/huwx/workspace/llvmcommitcheck/git.pool/llvm.git.'
	clangGIT='/home/huwx/workspace/llvmcommitcheck/git.pool/clang.git.'
	CCBUILD='/home/huwx/workspace/llvmcommitcheck/build.pool/build.'
	TMPDIR='/tmp'
	#CFILES='/SEIDISK/chenjj/compiler/study/data/filtering/llvm_all_fault_files'
	#CFILES='/SEIDISK/chenjj/compiler/clusterspeedup/time/llvmdiffversion/faultfiles'
	CFILES='/SEIDISK/chenjj/compiler/study/data/new/llvm'
	CCCONFIGARG='--enable-languages=c --disable-libffi --disable-shared --disable-expensive-checks --enable-optimized'
	CONF='/home/huwx/workspace/llvmcommitcheck/git.pool/llvm.git.'
	BINPATH='/home/chenjj/compiler/gcc/gcc-4.2.0/bin'
	SAVEFILE='llvm.csv'
	CURRENTBRANCH='origin/master'
	CCFLAG=''

	fix='llvm'
	change='clang'
	rver='29'
	lver='32'
	fver='28'
	FIXGIT=''
	tCCGIT=''
	if fix.startswith('llvm'):
		tCCGIT=clangGIT
		FIXGIT=llvmGIT
	else:
		tCCGIT=llvmGIT
		FIXGIT=clangGIT
	print tCCGIT

	for i in range(0,10):
		print 'fix commit:',FIXGIT+str(i),CURRENTBRANCH
		checkoutRepoCommit(FIXGIT+str(i),CURRENTBRANCH)

	CCGIT=tCCGIT
	CURRENTBRANCH='origin/master'
	SEARCHL=cmt[change][lver]
	SEARCHR=cmt[change][rver]
	#SAVEFILE='./output/f%s%sc%sl%sr%s.csv.'%(fix,fver,change,rver,lver)
	SAVEFILE='./output/llvm-clang-l%sr%s.csv.'%(rver,lver)
	SEARCHLllvm=cmt[fix][lver]
	SEARCHRllvm=cmt[fix][rver]

	black=open('blacklist.csv','r')
	for e in black.readlines():
		CCBLACKLIST.append(e)

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

	if begin>end:
		return 'uncertain-range_error'

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
		r=checkPerCfile(pathtocfile,begin,mid-1,cmtlist,first=True)
		if r.startswith('u'):
			r1=checkPerCfile(pathtocfile,mid+1,end,cmtlist,first=True)
			if r1.startswith('u'):
				if r1==r:
					return 'b'+cmtlist[mid] # broken CC
				if r1!=r:
					CCl=getCC(mid-1,cmtlist)
					CCr=getCC(mid+1,cmtlist)
					resl=compare(CCl,pathtocfile)
					resr=compare(CCr,pathtocfile)
					return 'c'+cmtlist[mid]+"-%d%s-%d%s"%(mid-1,str(resl),mid+1,str(resr))
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

def getNearstTime(cmt):
	global llvmcmttime,clangcmttime
	timemark=-1
	for e in clangcmttime:
		if e[0]==cmt:
			timemark=e[1]
			break

	leastlap=leastlapr=100000
	leastcmt=leastcmtr=''
	for e in llvmcmttime:
		if e[1]-timemark<0 and abs(e[1]-timemark)<leastlap:
			leastcmt=e[0]
			leastlap=abs(e[1]-timemark)

		if e[1]-timemark>0 and e[1]-timemark<leastlapr:
			leastcmtr=e[0]
			leastlapr=abs(e[1]-timemark)

	return [leastcmt,leastcmtr]

def getCC(no,cmtlist):
	global CCCACHE,BDCC,BDCCLOCK,TASKPRE,CCBLACKLIST,llvmcommitlst,llvmGIT
	if cmtlist[no] in CCBLACKLIST:
		printd('cc %s in blacklist'%(cmtlist[no]))
		return False
	pathtoCC=CCCACHE+'/'+cmtlist[no]+'/usr/local/bin/clang'
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

			#noo=int(no*(len(llvmcommitlst)*1.0/(len(cmtlist)*1.0)))
			noocmt=getNearstTime(cmtlist[no])
			for cmt in noocmt:
				printd('llvm checkout:',cmt)
				checkoutRepoCommit(llvmGIT,cmt)
				r=compileCC(no,cmtlist)
				if r :
					break

			# trytimes=1
			# for i in range(0,trytimes):
			# 	r=compileCC(no,cmtlist)
			# 	if r :
			# 		break;
			# 	#noo-=20
			# 	checkoutRepoCommit(llvmGIT,noocmt)

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
				datafile=open('blacklist.csv','a')
				datafile.write('%s\n'%(cmtlist[no]))
				datafile.close()
				return False
		else:
			printd('Wait for building ',cmtlist[no])
			while not os.path.exists(pathtoCC) and cmtlist[no] not in CCBLACKLIST:
				time.sleep(30)
			time.sleep(10)
			if cmtlist[no] in CCBLACKLIST:
				return False
			return pathtoCC


def compare(pathtoCC,pathtocfile):
	global TMPDIR,OPTARGS,TASKPRE,SYSCC
	exccmd("rm `find %s 2>/dev/null | grep [%s]O[0-9][.]ccout`"%(TMPDIR,TASKPRE))
	CCcmd="export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && timeout 500 %s %s -I/home/huwx/tool/csmith-2.2.0/runtime -O0 -o %s/%sO9.ccout 2>&1  1>/dev/null && timeout 500 %s/%sO9.ccout > %s/%sO9.ccout.txt "%(SYSCC,pathtocfile,TMPDIR,str(TASKPRE),TMPDIR,str(TASKPRE),TMPDIR,str(TASKPRE))
	r=exccmd(CCcmd)
	for e in r:
		if e.find('clang: error:')>-1:
			printd(pathtocfile.split('/')[-1],'compiled error')
			printd(e)
			return False
	for opt in OPTARGS:
		CCcmd="export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && timeout 500 %s %s -I/home/huwx/tool/csmith-2.2.0/runtime -%s -o %s/%s.ccout 2>&1  1>/dev/null && timeout 500 %s/%s.ccout > %s/%s.ccout.txt "%(pathtoCC,pathtocfile,opt,TMPDIR,str(TASKPRE)+opt,TMPDIR,str(TASKPRE)+opt,TMPDIR,str(TASKPRE)+opt)
		r=exccmd(CCcmd)
		for e in r:
			if e.find('clang: error:')>-1:
				printd(pathtocfile.split('/')[-1],'compiled error')
				printd(e)
				return False
		r=exccmd("diff %s/%sO9.ccout.txt %s/%s%s.ccout.txt 2>&1"%(TMPDIR,TASKPRE,TMPDIR,TASKPRE,opt))
		if len(r)>0:
			printd(r)
		if len(r)!=0:
			return False
	return True

def compileCC(no,cmtlist):
	#warning! Should think about the dir path.
	global CCCACHE,CCGIT,CCBUILD,CCCONFIGARG,CURRENTBRANCH,INFOLEVEL,TASKPRE,CCBLACKLIST,llvmGIT,clangGIT
	commit=cmtlist[no]
	printd('compiling..',no,commit)
	if no+1!=len(cmtlist):
		last_commit=cmtlist[no+1]
	else:
		last_commit='last'
		print 'total commit',no+1

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

## this statement for llvm 2>/dev/null
	#FLAG=CCCONFIGARG+' ' '--with-clang-srcdir='+clangGIT+' '+CCFLAG
	#if not os.path.exists('%s/tools/clang'%(llvmGIT)):
	#	r=exccmd('ln -s %s %s/tools/clang 2>/dev/null'%(clangGIT,llvmGIT))
	FLAG=CCCONFIGARG+' '+CCFLAG
	r=exccmd('cd %s && rm -rf * 2>/dev/null && %s/configure %s 2>&1 && rm ./config.cache 2>/dev/null'%(CCBUILD,llvmGIT,FLAG))
	printd('buiding CC.')
	r=exccmd('export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/ && export PATH=%s:$PATH && cd %s && make -j 32 2>/dev/null'%(BINPATH,CCBUILD),10000)
	printd('build complete:',commit)

	printd('installing to: %s/%s'%(CCCACHE,CURRENTCOMMIT))
	r=exccmd('cd %s && make install DESTDIR=%s/%s  2>/dev/null'%(CCBUILD,CCCACHE,CURRENTCOMMIT))
	if os.path.exists('%s/%s/usr/local/bin/clang'%(CCCACHE,CURRENTCOMMIT)):
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
		if e.find('HEAD')>-1:
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
	printd('checking out %s branch:'%(CCGIT.split('/')[-1]),branch)
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
	printd('%s branch total commit:'%(CCGIT.split('/')[-1]),len(rr))
	del r
	return rr

def dumpRepoBranchCommit(GIT,branch):
	global CCGIT
	t=CCGIT
	CCGIT=GIT
	r=dumpBranchCommit(branch)
	CCGIT=t
	return r

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

def task(procID,files,bdCCl,bdCClock,blacklist,cache):
	global CCGIT,CURRENTBRANCH,SAVEFILE,SEARCHL,SEARCHR,CCBUILD,TASKPRE,BDCC,BDCCLOCK,CCBLACKLIST,SEQCACHE,clangGIT,llvmGIT
	global llvmcommitlst,SEARCHLllvm,SEARCHRllvm
	global clangcmttime,llvmcmttime
	#set config
	clangGIT+=str(procID)
	llvmGIT+=str(procID)
	CCGIT=CCGIT+str(procID)
	CCBUILD=CCBUILD+str(procID)
	TASKPRE=str(procID)
	SAVEFILE=SAVEFILE+TASKPRE
	BDCC=bdCCl
	BDCCLOCK=bdCClock
	CCBLACKLIST=blacklist
	SEQCACHE=cache

	printd('llvm git:',llvmGIT)
	printd('clang git:',clangGIT)
	printd('build git:',CCBUILD)
	printd('GIT UNFIXED:',CCGIT)

	if len(files)==0:
		return

	printd('task begin.')

	commitlist=dumpBranchCommit(CURRENTBRANCH)
	llvmcommitlst=dumpRepoBranchCommit(llvmGIT,CURRENTBRANCH)

	clangcmttime=gettimelog(clangGIT)
	llvmcmttime=gettimelog(llvmGIT)

	if len(commitlist)==0:
		printd("load commit failed")
		return

	l=r=-1
	for i in range(0,len(commitlist)):
		if commitlist[i]==SEARCHL:
			l=i
		if commitlist[i]==SEARCHR:
			r=i

	ll=rl=-1
	for i in range(0,len(llvmcommitlst)):
		if llvmcommitlst[i]==SEARCHLllvm:
			ll=i
		if llvmcommitlst[i]==SEARCHRllvm:
			rl=i

	if l<0:
		l=0

	if l==r:
		getCC(l,commitlist)

	if l>=r or l<0 or r<0:
		printd('commit range not legal!!!',l,r)
		return
		
	commitlist=commitlist[l:r+1]
	llvmcommitlst=llvmcommitlst[ll:rl+1]

	clangcmttime=clangcmttime[l:r+1]
	llvmcmttime=llvmcmttime[ll:rl+1]

	if commitlist[0]!=clangcmttime[0][0] or commitlist[-1]!=clangcmttime[-1][0]:
		printd('time log error')
		return 

	if llvmcommitlst[0]!=llvmcmttime[0][0] or llvmcommitlst[-1]!=llvmcmttime[-1][0]:
		printd('time log error')
		return

	if len(llvmcommitlst)!=len(commitlist):
		printd('range not equal!','llvm:',len(llvmcommitlst),'clang',len(commitlist))
		#return
	else:
		printd('range equal!','llvm:',len(llvmcommitlst),'clang',len(commitlist))
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

def checkoutRepoCommit(GIT,commit):
	global CCGIT
	t=CCGIT
	CCGIT=GIT
	r=checkoutCommit(commit)
	CCGIT=t
	return r

def gettimelog(GIT):
	r=exccmd('cd %s && git log --pretty=format:\"%%H %%at\"'%(GIT))
	m=[]
	for e in r:
		m.append([e.split(' ')[0],int(e.split(' ')[-1])])
	return m

def main():
	# dump_branch_commit test
	#dumpBranchCommit('origin/master')
	# dumpBrancheList_test
	#dumpBranchList()
	#checkoutCommit('31500ecb8bbec82c062c6f948d9b8da115ebdcf6')
	#compileCC()
	global CURRENTBRANCH,CFILES,SAVEFILE,SEARCHL,SEARCHR,TASKMAX,BDCC,BDCCLOCK,CCBLACKLIST,SEQCACHE,TASKBASE
	# print 'preload...'
	# master=dumpBranchCommit('origin/master')
	print 'ZZ_CHECK_COMPILER_LLVM+CLANG - START 2015'
	print '########## STEP 1: Loading data ############'
	print 'loading files.'
	files=exccmd('find %s | grep ".c$"'%(CFILES))
	pfiles=[[] for i in range(0,TASKMAX)]

	# saved status
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
	argsforllvm()
	main()
