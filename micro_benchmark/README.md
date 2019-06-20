### Micro Benchmark Tester



##Require
1. crit-in-criu should call \*sender\_antonio
2. criu-het simplified should call \*semder
3. please use root to run test
4. please create ssh-keygen for test machine
- sudo su
- ssh-keygen
- paste ~/.ssh/id\_dsa.pub to your target machine ~/.ssh/authorized\_keys

## Env
1. mkdir -p /popcorn/brdw
2. cp $benchmark\* /popcorn/brdw
3. cp caller /popcorn/brdw

## Install
1. go to the directory has same archtecture name as your machine
2. sudo make

## Test
1. cd /popcorn/brdw/
2. ./caller $sender\_script $benchmark $targetmachine $args



#example popcorn-linpack
- mkdir -p /popcorn/brdw/
- cp popcorn-linpack\* /popcorn/brdw/
- cd ~/micro\_benchmark
- cp caller /popcorn/brdw/
- cd x86-64
- make
- ssh aarch64 machine
- do the same.....except: cd /aarch64 ; make


- cd popcorn/brdw/; ./caller x86\_arm\_sender popcorn-linpack sunsky 

#example popcorn-mm 
- cd popcorn/brdw/; ./caller x86\_arm\_sender\_antonio popcorn-mm sunsky 4096  


##BUG

1. pid=$(ps -C $process | tr -s ' '  | cut -d ' ' -f 2 | tail -n +2)  \ 
	some time will not work fine to get pid, depends on diffrent machine
	pleae change "cut -d ' ' -f 2" to "cut -d ' ' -f 1" or vice versa

2. new popcorn-compiler will not have flash quit problem, so *while [ -z "$pid" ]* loop 
	may delete, the purpose of this loop is to make sure benchmark run successfully


~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                                                    
~                                                                      
