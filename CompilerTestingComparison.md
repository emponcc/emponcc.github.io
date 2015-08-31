An Empirical Comparison of Compiler Testing Techniques---
*update:2015-08-31 under_construction*  

[1.Intro](#1) [2.Measurement Detail](#2) [2.Download](#3)  
###<h2 id="1">Intro</h2>   
Modern compilers are usually using the stress testing. Generally we produce many test programs on purpose and run compiler(s) compiling the programs under different configurations, thus we'll probe the reason once the compiler fails.   
The comparison we perfomed is on current compiler testing techniques,including RDT DOL and EMI, which are descripted as follows,   
    
+ *RDT*, randomized differential testing, assumes that assumes that several comparable compilers are implemented based on the same speciﬁcation and detects bugs by comparing the outputs of these compilers for the same test program.
>From W. M. McKeeman. Diﬀerential testing for software. Digital Technical Journal, 10(1):100–107, 1998.

+ *EMI*,  euivalence modulo inputs, generates a series of variants from an existing test program by guaranteeing the variants to be equivalent to the test program under a set of test inputs
>From V. Le, M. Afshari, and Z. Su. Compiler validation via equivalence modulo inputs. In Proceedings of the 35th ACM SIGPLAN Conference on Programming Language Design and Implementation, page 25. ACM, 2014.

+ *DOL*,  "diﬀerent optimization levels", is a simple testing technique is to compare the outputs of one compiler at diﬀerent optimization levels.
>DOL is from this work.

###<h2 id="1">Measurement Detail</h2>  
Our study is based on the analyze of actual bugs each method may find. So the number of bugs is more accurate the better. Formal ways are accurate enough.