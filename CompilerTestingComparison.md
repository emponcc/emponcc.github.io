An Empirical Comparison of Compiler Testing Techniques---
*update:2015-08-31*  

[1.Intro](#1)  
[2.Measurement](#2)  
[3.Data](#3)  
[4.Contributors](#4) 
###<h2 id="1">Intro</h2>   
Modern compilers are usually using the stress testing, generally we produce many test programs on purpose and run compiler(s) compiling the programs under different configurations, thus we'll probe the reason once the compiler fails.The comparison we perfomed is on current compiler testing techniques,including RDT DOL and EMI, which are descripted as follows,   
    
+ *RDT*, randomized differential testing, assumes that assumes that several comparable compilers are implemented based on the same speciﬁcation and detects bugs by comparing the outputs of these compilers for the same test program.
>From W. M. McKeeman. Diﬀerential testing for software. Digital Technical Journal, 10(1):100–107, 1998.

+ *EMI*,  euivalence modulo inputs, generates a series of variants from an existing test program by guaranteeing the variants to be equivalent to the test program under a set of test inputs
>From V. Le, M. Afshari, and Z. Su. Compiler validation via equivalence modulo inputs. In Proceedings of the 35th ACM SIGPLAN Conference on Programming Language Design and Implementation, page 25. ACM, 2014.

+ *DOL*,  "diﬀerent optimization levels", is a simple testing technique is to compare the outputs of one compiler at diﬀerent optimization levels.
>DOL is from this work.

###<h2 id="2">Measurement</h2>  
Our study is based on the analyze of actual bugs each method may find, apperently we need the number of bugs to be more accurate. Former means are way not accurate enough, so we find out that we can use the "commit id“ to identify each bugs while there are many corresponding programs.   
> We use git repository here because it is a distributed revision control system thus we have almost all commits locally and avoid downloading when checkout a specific commit version.

The basic idea is easy to comprehend - if there is a program which is failed on a version but works on a latter version, here must be a version of compiler between these two versions that the change of source code fix this bug(s).   
>+ GCC provides a git mirror of its svn repository.You can access its repository here <https://gcc.gnu.org/wiki/GitMirror>.
>+ LLVM and Clang's git mirrors are at <http://llvm.org/docs/GettingStarted.html#git-mirror>

####Source Code :
[For LLVM](./file/check_compiler_llvm+clang.py): Because the LLVM repository and Clang repository are not together so we use Clang's commit id as result. Due to the splited repositories, here is a problem to find out which LLVM and which Clang works together, so we try to match  nearest commits between LLVM and Clang, if they're not woking, we'll try another pair.

###<h2 id="3"> Data </h2>

###<h2 id="4"> Contributors </h2>
Contributors to the implementation are:   
Junjie Chen   
Wenxiang Hu  