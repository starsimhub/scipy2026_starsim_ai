# Question 1: Basics

## 1.1: What is Starsim? [14 marks]

##### 1.1.1. In a few sentences, describe what Starsim is and does. [2 marks]

##### 1.1.2. Briefly describe (1-2 sentences) the concepts of a Sim, People, and Modules. [3 marks]

##### 1.1.3. Briefly describe (1-2 sentences) each of the different types of module. [5 marks]

##### 1.1.4. In a few sentences, describe how disease transmission occurs in a Starsim simulation. What roles do the contact network, the number of contacts, and the transmissibility parameter (`beta`) play? [4 marks]

## 1.2: Simple simulations [32 marks]

##### 1.2.1. Using `ss.Sim()`, write the code that replicates the behavior of `ss.demo()`, i.e. a simulation with an SIR disease, random network, and default parameters. Run the sim and plot the results of the SIR module. Describe the dynamics shown in the plot. [5 marks]

##### 1.2.2. Write a `pars` dict in a declarative format (i.e., using only dicts, strings, ints, and floats; no instantiated objects) that specifies a random network with 8 contacts, and an SIR disease with initial prevalence of 0.02 and transmissibility (beta) of 0.08. Provide the parameters to a simulation, run it, and plot the results of the SIR module. How does it compare to the previous simulation (1.2.1)? [12 marks]

##### 1.2.3. Implement the same simulation as 1.2.2, but instead of a `pars` dict, use component-based format (i.e., instantiated Starsim objects) and supply them as kwargs to the sim. Verify that the sim runs and produces identical results to 1.2.2 (use `sim.summary`). [10 marks]

##### 1.2.4. Run a simulation with no network or disease but with 1000 agents and demographics enabled. Export the sim's people to a dataframe. At the end of the simulation, who is the oldest female? [5 marks]

## 1.3: Exploring outputs [18 marks]

##### 1.3.1. Run an SIR simulation with a random network of 8 contacts and 1000 agents. Access the contact network, report the total number of edges, and plot a histogram of the contact degree distribution (the number of contacts per agent). What is the mean degree, and how does it relate to `n_contacts`? [6 marks]

##### 1.3.2. Using the same simulation, directly plot the number of new infections per timestep (the epidemic incidence curve) and the cumulative number of infections, using `matplotlib` rather than the built-in `.plot()` method. [5 marks]

##### 1.3.3. Run an SIR simulation with demographics enabled and a partial attack rate (e.g. `beta=0.07`, `n_contacts=4`, 2000 agents, `dur=100`) so that not everyone becomes infected. Using the agents' ages and their disease state at the end of the simulation, plot the age distribution of agents who were ever infected versus those who escaped infection. Is there a correlation between agent age and their probability of having ever been infected in this model? Explain why or why not. [7 marks]

