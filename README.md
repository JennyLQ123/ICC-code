# ICC
## File List
1. command: initial flow table for dataplane
2. back: a copy for prior controller and P4 program
3. dataplane: start scripts for dataplane
4. controlplane: all controllers include 3 compared methods
5. model: reserved for ppo models
6. model\_flow\_1.0/1.1/1.2\_reset: saved ppo model, but the performance is not good.
7. reward: reserved for reward log
8. TrafficGenerator: traffic flow generator and background packet generator
9. util: the reward for different controllers under different traffic sending rates, only 5 epochs. the ppo model we used is ppo500 in folder model\_flow\_1.2\_reset
## Running commands
1. start dataplane:
	python run_demo.py -p satellite.p4 -m satellite-topo
2. send traffic:
	flow: 	bash changmtu 
		bash flowtest.sh
	packet: bash send.sh
	background traffic: bash send.sh
3. start controller:
	python ctl-ppo/ecmp/linear/sp.py
##Notes in running
1. when you are training again the experiment, remember to modify these points:
	ctl-ppo.py:EP_START, EP_START+1(in function controlMain), the positions of reward and models to put, ppo.load()
	TrafficGenerator:traffic rates in flowtest.py and saved file names in bin/result.py
