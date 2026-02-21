# starsim_t5

## starsim_t5.1

### Description
Create and run an SIR simulation using an explicit RandomNet network object. Unlike passing a string or dict for the network, this approach instantiates the network directly, giving more control over network parameters. After running the simulation, extract basic network statistics: the number of edges in the network and the number of unique contacts for agent 0.

### Background
Starsim supports several ways to specify contact networks. The most explicit is to create a network object directly (e.g., ss.RandomNet(n_contacts=10)) and pass it to the simulation. After running, the network is accessible via sim.networks.randomnet. The find_contacts() method returns an array of UIDs that a given agent is connected to. The network's to_df() method converts edges to a pandas DataFrame with columns p1, p2, and beta.

### Dependencies
- starsim

### Function Header
```python
def create_random_net_sim(n_agents: int = 5_000, n_contacts: int = 10, beta: float = 0.05, init_prev: float = 0.01) -> dict:
```

### Docstring
```
Create and run an SIR simulation with an explicit RandomNet, then extract network info.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent in the random network.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    Dictionary containing:
        - 'sim': The completed Starsim Sim object.
        - 'n_edges': Total number of edges in the random network (int).
        - 'contacts_agent_0': Number of unique contacts of agent 0 (int).
```

### Test Cases

#### Simulation should have a randomnet network
```python
result = create_random_net_sim()
assert hasattr(result['sim'].networks, 'randomnet'), 'Simulation should have a randomnet network'
```

#### Network should have edges
```python
result = create_random_net_sim()
assert result['n_edges'] > 0, 'Network should have edges'
```

#### Agent 0 should have contacts
```python
result = create_random_net_sim()
assert result['contacts_agent_0'] > 0, 'Agent 0 should have at least one contact'
```

#### Simulation should produce infections
```python
result = create_random_net_sim()
assert result['sim'].results.sir.cum_infections[-1] > 0, 'There should be at least some infections'
```

### Gold Solution
```python
def create_random_net_sim(n_agents: int = 5_000, n_contacts: int = 10, beta: float = 0.05, init_prev: float = 0.01) -> dict:
    import starsim as ss
    net = ss.RandomNet(n_contacts=n_contacts)
    sir = ss.SIR(beta=beta, init_prev=init_prev)
    sim = ss.Sim(n_agents=n_agents, diseases=sir, networks=net)
    sim.run()
    network = sim.networks.randomnet
    contacts = network.find_contacts([0])
    return {
        'sim': sim,
        'n_edges': len(network.to_df()),
        'contacts_agent_0': len(contacts),
    }
```
## starsim_t5.2

### Description
Investigate how network density (average number of contacts per agent) affects SIR epidemic dynamics. Run simulations with different n_contacts values using explicit RandomNet objects. Higher contact density means each infected agent can transmit to more neighbors, leading to faster and larger epidemics.

### Background
In network epidemiology, the average number of contacts (node degree) is a key determinant of epidemic dynamics. Higher contact density increases the effective reproduction number, making it easier for the disease to spread. In Starsim, this is controlled via the n_contacts parameter of ss.RandomNet. With low density, epidemics may fail to take off or remain small. With high density, epidemics spread rapidly through the population.

### Dependencies
- starsim
- numpy

### Function Header
```python
def compare_network_density(n_contacts_list: list[int], n_agents: int = 5_000, beta: float = 0.05, init_prev: float = 0.01) -> dict[int, dict]:
```

### Docstring
```
Run SIR simulations with different network densities and compare outcomes.

Args:
    n_contacts_list: List of average contact counts to compare (e.g., [4, 10, 20]).
    n_agents: Number of agents to simulate.
    beta: Probability of transmission between contacts.
    init_prev: Initial proportion of the population that is infected.

Returns:
    Dictionary mapping each n_contacts value to a dict containing:
        - 'cum_infections': cumulative infections at end of simulation
        - 'peak_prevalence': maximum prevalence observed during the simulation
```

### Test Cases

#### Results should contain an entry for each n_contacts value
```python
results = compare_network_density([4, 10, 20])
assert set(results.keys()) == {4, 10, 20}, 'Should have results for all n_contacts values'
```

#### Each result should contain cum_infections and peak_prevalence
```python
results = compare_network_density([10])
assert 'cum_infections' in results[10], 'Should contain cum_infections'
assert 'peak_prevalence' in results[10], 'Should contain peak_prevalence'
```

#### Higher network density should produce more cumulative infections
```python
results = compare_network_density([4, 20], n_agents=5_000)
assert results[20]['cum_infections'] > results[4]['cum_infections'], 'Denser network should produce more infections'
```

#### Peak prevalence should be between 0 and 1
```python
results = compare_network_density([10])
assert 0 < results[10]['peak_prevalence'] <= 1.0, 'Peak prevalence should be a valid proportion'
```

### Gold Solution
```python
def compare_network_density(n_contacts_list: list[int], n_agents: int = 5_000, beta: float = 0.05, init_prev: float = 0.01) -> dict[int, dict]:
    import starsim as ss
    import numpy as np
    results = {}
    for nc in n_contacts_list:
        net = ss.RandomNet(n_contacts=nc)
        sir = ss.SIR(beta=beta, init_prev=init_prev)
        sim = ss.Sim(n_agents=n_agents, diseases=sir, networks=net)
        sim.run()
        results[nc] = {
            'cum_infections': float(sim.results.sir.cum_infections[-1]),
            'peak_prevalence': float(np.max(sim.results.sir.prevalence)),
        }
    return results
```
## starsim_t5.3

### Description
Create an STI (sexually transmitted infection) model using Starsim's MFNet, a sexual network that forms partnerships between male and female agents. MFNet models heterosexual pair formation with configurable relationship duration and coital act frequency. Use an SIS disease (appropriate for bacterial STIs where reinfection is possible) transmitted over this network.

### Background
Starsim provides specialized network types for modeling sexually transmitted infections. ss.MFNet creates a heterosexual (male-female) partnership network where agents form and dissolve relationships over time. Key parameters include 'duration' (average relationship length) and 'acts' (coital acts per year). For STI modeling, SIS dynamics are often appropriate since many bacterial STIs (e.g., gonorrhea, chlamydia) do not confer lasting immunity. The simulation requires sub-annual timesteps (e.g., dt=1/12 for monthly) to capture partnership dynamics.

### Dependencies
- starsim

### Function Header
```python
def create_mfnet_sim(n_agents: int = 2_000, beta: float = 0.5, init_prev: float = 0.1, dur: int = 20) -> ss.Sim:
```

### Docstring
```
Create and run an SIS simulation over an MFNet sexual network.

Args:
    n_agents: Number of agents to simulate.
    beta: Probability of transmission per contact.
    init_prev: Initial proportion of the population that is infected.
    dur: Duration of the simulation in years.

Returns:
    A Starsim Sim object that has been run to completion with an SIS disease
    transmitted over an MFNet network.
```

### Test Cases

#### Simulation should have an MFNet network
```python
sim = create_mfnet_sim()
assert hasattr(sim.networks, 'mfnet'), 'Simulation should have an mfnet network'
```

#### Simulation should have an SIS disease
```python
sim = create_mfnet_sim()
assert hasattr(sim.diseases, 'sis'), 'Simulation should have an SIS disease'
```

#### Simulation should produce infections
```python
sim = create_mfnet_sim()
assert sim.results.sis.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Network should have partnership edges
```python
sim = create_mfnet_sim()
df = sim.networks.mfnet.to_df()
assert len(df) > 0, 'MFNet should have active partnerships'
```

### Gold Solution
```python
def create_mfnet_sim(n_agents: int = 2_000, beta: float = 0.5, init_prev: float = 0.1, dur: int = 20) -> ss.Sim:
    import starsim as ss
    mf = ss.MFNet()
    sis = ss.SIS(beta=beta, init_prev=init_prev)
    sim = ss.Sim(n_agents=n_agents, diseases=sis, networks=mf, start=2000, dur=dur, dt=1/12)
    sim.run()
    return sim
```
## starsim_t5.4

### Description
Compare two approaches to modeling disease transmission in Starsim: contact networks (RandomNet) and mixing pools (MixingPool). Contact networks track individual edges between agents, while mixing pools use a well-mixed approximation where transmission depends on the average level of infection in the pool. Run an SIR simulation with each approach and compare their epidemic outcomes.

### Background
Starsim provides two fundamentally different approaches for modeling contacts. ss.RandomNet creates explicit person-to-person edges and transmits disease along those edges using the disease's beta parameter. ss.MixingPool instead computes transmission based on the average infectious fraction in the pool — it does not track individual contacts. MixingPool takes its own beta parameter (separate from the disease beta) controlling the force of infection. The two approaches can produce similar epidemic dynamics with appropriate parameterization, but MixingPool is computationally cheaper for large populations. Use ss.poisson(lam=n) to set the number of contacts as a Poisson-distributed random variable.

### Dependencies
- starsim
- numpy

### Function Header
```python
def compare_network_types(n_agents: int = 5_000, n_contacts: int = 4, init_prev: float = 0.01) -> dict[str, dict]:
```

### Docstring
```
Compare SIR epidemic outcomes using a RandomNet vs a MixingPool.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts (used for both network types).
    init_prev: Initial proportion of the population that is infected.

Returns:
    Dictionary with two keys:
        - 'mixing_pool': dict with 'cum_infections' and 'peak_prevalence'
        - 'random_net': dict with 'cum_infections' and 'peak_prevalence'
```

### Test Cases

#### Results should contain mixing_pool and random_net keys
```python
results = compare_network_types()
assert 'mixing_pool' in results, 'Should have mixing_pool results'
assert 'random_net' in results, 'Should have random_net results'
```

#### Each result should contain cum_infections and peak_prevalence
```python
results = compare_network_types()
for key in ['mixing_pool', 'random_net']:
    assert 'cum_infections' in results[key], f'{key} should contain cum_infections'
    assert 'peak_prevalence' in results[key], f'{key} should contain peak_prevalence'
```

#### Both approaches should produce infections
```python
results = compare_network_types()
assert results['mixing_pool']['cum_infections'] > 0, 'MixingPool should produce infections'
assert results['random_net']['cum_infections'] > 0, 'RandomNet should produce infections'
```

#### Peak prevalence should be valid proportions
```python
results = compare_network_types()
for key in ['mixing_pool', 'random_net']:
    assert 0 < results[key]['peak_prevalence'] <= 1.0, f'{key} peak prevalence should be a valid proportion'
```

### Gold Solution
```python
def compare_network_types(n_agents: int = 5_000, n_contacts: int = 4, init_prev: float = 0.01) -> dict[str, dict]:
    import starsim as ss
    import numpy as np

    # Mixing pool approach
    mp = ss.MixingPool(n_contacts=ss.poisson(lam=n_contacts))
    sir_mp = ss.SIR(init_prev=init_prev)
    sim_mp = ss.Sim(n_agents=n_agents, diseases=sir_mp, networks=mp)
    sim_mp.run()

    # Contact network approach
    net = ss.RandomNet(n_contacts=n_contacts)
    sir_net = ss.SIR(beta=0.05, init_prev=init_prev)
    sim_net = ss.Sim(n_agents=n_agents, diseases=sir_net, networks=net)
    sim_net.run()

    return {
        'mixing_pool': {
            'cum_infections': float(sim_mp.results.sir.cum_infections[-1]),
            'peak_prevalence': float(np.max(sim_mp.results.sir.prevalence)),
        },
        'random_net': {
            'cum_infections': float(sim_net.results.sir.cum_infections[-1]),
            'peak_prevalence': float(np.max(sim_net.results.sir.prevalence)),
        },
    }
```
