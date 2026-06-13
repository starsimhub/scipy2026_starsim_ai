# Question 2: Sim behavior

## 2.1: SIS dynamics [52 marks]

##### 2.1.1. Implement three SIS models with `n_agents = [100, 1000, 10000]`, `pop_scale` set to keep the total population constant (i.e. `[100, 10, 1]`, and with `init_prev = 5/n_agents` (i.e., always 5 agents). Run in parallel and plot the SIS results only. How do the dynamics differ qualitatively? What is the impact of setting `init_prev` to a fixed number rather than fraction of agents? [10 marks]

##### 2.1.2. Take a single SIS model (`n_agents=1000`, `dur=100`, default parameters, random network). Run it 20 times with different random seeds, in parallel. Collect the prevalence trajectories and plot all 20 individual trajectories on a single axes, together with the mean trajectory. [8 marks]

##### 2.1.3. Using the 20 runs from 2.1.2: (a) plot the mean prevalence trajectory with a shaded band showing the 10th–90th percentile across runs; and (b) plot a histogram of the peak prevalence across the 20 runs, and report its mean and standard deviation. [8 marks]

##### 2.1.4. You want to quantify the effect of increasing `beta` from 0.06 to 0.08 on the peak prevalence of the SIS model. Compute the distribution of the *difference* in peak prevalence across 20 replicates, in an RNG-safe way (i.e., so that the difference reflects the change in `beta` rather than random noise). Plot the distribution of differences. Demonstrate the variance reduction compared to using independent random seeds for the two scenarios, and explain why using common random numbers reduces the variance of the estimated difference. [12 marks]

##### 2.1.5. At what value of `beta` does the "ringing" behavior of the SIS model disappear (i.e., the I compartment is monotonic) given `waning=0.3` and other parameters at their default values (`n_agents=10000, init_prev=0.01`)? Determine `beta` to within 0.005 and run five replicates in parallel, using the mean of the replicates to determine monotonicity. Allow ±5% when determining monotonicity to account for stochastic noise. [14 marks]

## 2.2: SIRS models [68 marks]

##### 2.2.1. Implement agent-based and compartmental SIRS modules, called `AgentSIRS` and `CompSIRS` respectively. Implement both in Starsim from base classes (i.e., you can inherit from `ss.Infection`, `ss.Disease`, or `ss.Module`, but do not inherit from `ss.SIR`) , and write as "production code" (e.g., include docstrings, a plotting method, and pay attention to code style). Use defaults of `start=0`, `dur=100` (days), `n_agents=1000`, `init_prev=0.01`, `beta=0.8` (per day), `gamma=0.3`, and `waning=0.02`. For the ABM, do not use a network; assume all-to-all connectivity. What is the average mismatch in the S compartment between the two simulations? What about for 10,000 agents? What about for `dt=0.1`? [50 marks]

##### 2.2.2. Consider the CompSIRS model you made in the previous question. Give three reasons why it might be useful to implement this in Starsim rather than implementing it from scratch using NumPy. [6 marks]

##### 2.2.3. Add vital dynamics to both the `AgentSIRS` and `CompSIRS` models from 2.2.1, using a crude birth rate of 30 and a crude death rate of 10 (both per 1000 per year). What changes are required for each model? Run both for 20 years and confirm the population changes consistently between them. Explain why the two models require different amounts of work. [12 marks] 