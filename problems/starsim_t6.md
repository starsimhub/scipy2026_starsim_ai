# starsim_t6

## starsim_t6.1

### Description
Compare baseline and vaccinated SIR simulations using Starsim's built-in vaccine product and routine vaccination intervention. Run two 50-year simulations with demographics — one without any intervention (baseline) and one with routine vaccination — and return the cumulative infections from each.

### Background
Starsim separates the concept of products (what is administered, e.g., a vaccine) from interventions (how it is delivered, e.g., routine or campaign). ss.simple_vx(efficacy) creates a basic vaccine product, and ss.routine_vx(start_year, prob, product) creates a routine delivery intervention that vaccinates a fraction of eligible agents each timestep. Demographics (births and deaths) are important here because new births create susceptible agents who benefit from ongoing vaccination.

### Dependencies
- starsim

### Function Header
```python
def compare_sir_vaccination(n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_efficacy: float = 0.5, vx_prob: float = 0.2, vx_start_year: int = 2015) -> dict[str, float]:
```

### Docstring
```
Compare cumulative infections between a baseline SIR simulation and one with routine vaccination.

Both simulations run from 2000 to 2050 with demographics (birth_rate=20, death_rate=15).
The vaccinated simulation uses ss.simple_vx to create a vaccine product and ss.routine_vx
to deliver it as a routine program.

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent in the random network.
    beta: Probability of transmission between contacts.
    dur_inf: Duration of infection in years.
    vx_efficacy: Efficacy of the vaccine (0 to 1).
    vx_prob: Probability of vaccination per eligible agent per timestep.
    vx_start_year: Year to begin routine vaccination.

Returns:
    Dictionary with keys:
        - 'baseline_infections': cumulative infections without vaccination
        - 'vaccinated_infections': cumulative infections with vaccination
```

### Test Cases

#### Result should contain both baseline and vaccinated infection counts
```python
result = compare_sir_vaccination()
assert 'baseline_infections' in result, 'Should have baseline_infections'
assert 'vaccinated_infections' in result, 'Should have vaccinated_infections'
```

#### Both infection counts should be positive
```python
result = compare_sir_vaccination()
assert result['baseline_infections'] > 0, 'Baseline should have infections'
assert result['vaccinated_infections'] > 0, 'Vaccinated scenario should still have some infections'
```

#### Vaccination should reduce cumulative infections compared to baseline
```python
result = compare_sir_vaccination()
assert result['vaccinated_infections'] < result['baseline_infections'], 'Vaccination should reduce infections'
```

#### Return values should be floats
```python
result = compare_sir_vaccination()
assert isinstance(result['baseline_infections'], float), 'baseline_infections should be a float'
assert isinstance(result['vaccinated_infections'], float), 'vaccinated_infections should be a float'
```

### Gold Solution
```python
def compare_sir_vaccination(n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_efficacy: float = 0.5, vx_prob: float = 0.2, vx_start_year: int = 2015) -> dict[str, float]:
    import starsim as ss
    pars = dict(
        n_agents=n_agents,
        birth_rate=20,
        death_rate=15,
        networks=dict(type='random', n_contacts=n_contacts),
        diseases=dict(type='sir', dur_inf=dur_inf, beta=beta),
        start=2000,
        stop=2050,
    )
    sim_base = ss.Sim(pars=pars)
    sim_base.run()
    my_vaccine = ss.simple_vx(efficacy=vx_efficacy)
    my_intv = ss.routine_vx(start_year=vx_start_year, prob=vx_prob, product=my_vaccine)
    sim_intv = ss.Sim(pars=pars, interventions=my_intv)
    sim_intv.run()
    return {
        'baseline_infections': float(sim_base.results.sir.cum_infections[-1]),
        'vaccinated_infections': float(sim_intv.results.sir.cum_infections[-1]),
    }
```
## starsim_t6.2

### Description
Create a custom vaccine product for an SIS disease by subclassing ss.Vx. The vaccine should reduce susceptibility (rel_sus) upon administration. Use it with ss.routine_vx to deliver vaccination in an SIS simulation with demographics. Return the completed simulation.

### Background
Starsim's built-in vaccine products (e.g., ss.simple_vx) work for standard SIR-type diseases, but custom diseases like SIS may require custom vaccine logic. By subclassing ss.Vx and overriding the administer(people, uids) method, you can define exactly how the vaccine affects agents. For an SIS vaccine, reducing rel_sus (relative susceptibility) makes vaccinated agents less likely to become infected. The vaccine product is then paired with a delivery mechanism like ss.routine_vx.

### Dependencies
- starsim

### Function Header
```python
def run_sis_vaccine_sim(n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_efficacy: float = 0.9, vx_prob: float = 1.0, vx_start_year: int = 2015) -> ss.Sim:
```

### Docstring
```
Run an SIS simulation with a custom vaccine product delivered via routine vaccination.

Define a custom vaccine class (sis_vaccine) that subclasses ss.Vx. The class should:
  - Accept an efficacy parameter via define_pars
  - Override the administer method to reduce rel_sus for vaccinated agents
    by multiplying rel_sus by (1 - efficacy)

Use this vaccine with ss.routine_vx. The simulation runs from 2000 to 2050
with demographics (birth_rate=20, death_rate=15).

Args:
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent.
    beta: Probability of transmission between contacts.
    dur_inf: Duration of infection in years.
    vx_efficacy: Efficacy of the custom vaccine (0 to 1).
    vx_prob: Probability of vaccination per eligible agent per timestep.
    vx_start_year: Year to begin routine vaccination.

Returns:
    A Starsim Sim object that has been run to completion.
```

### Test Cases

#### Simulation should have an SIS disease
```python
sim = run_sis_vaccine_sim()
assert hasattr(sim.diseases, 'sis'), 'Simulation should have an SIS disease'
```

#### Simulation should have at least one intervention
```python
sim = run_sis_vaccine_sim()
assert len(sim.interventions) > 0, 'Simulation should have at least one intervention'
```

#### Simulation should produce infections
```python
sim = run_sis_vaccine_sim()
assert sim.results.sis.cum_infections[-1] > 0, 'There should be at least some infections'
```

#### Population size should match n_agents parameter
```python
sim = run_sis_vaccine_sim(n_agents=1_000)
assert sim.pars.n_agents == 1_000, 'Population size should match n_agents'
```

### Gold Solution
```python
def run_sis_vaccine_sim(n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_efficacy: float = 0.9, vx_prob: float = 1.0, vx_start_year: int = 2015) -> ss.Sim:
    import starsim as ss

    class sis_vaccine(ss.Vx):
        def __init__(self, efficacy=1.0, **kwargs):
            super().__init__()
            self.define_pars(efficacy=efficacy)
            self.update_pars(**kwargs)

        def administer(self, people, uids):
            people.sis.rel_sus[uids] *= 1 - self.pars.efficacy

    my_vaccine = sis_vaccine(efficacy=vx_efficacy)
    my_intv = ss.routine_vx(start_year=vx_start_year, prob=vx_prob, product=my_vaccine)
    pars = dict(
        n_agents=n_agents,
        birth_rate=20,
        death_rate=15,
        networks=dict(type='random', n_contacts=n_contacts),
        diseases=dict(type='sis', dur_inf=dur_inf, beta=beta),
        start=2000,
        stop=2050,
    )
    sim = ss.Sim(pars=pars, interventions=my_intv)
    sim.run()
    return sim
```
## starsim_t6.3

### Description
Sweep across different vaccine efficacy values to determine the minimum efficacy required to eradicate an SIS disease by 2050. For each efficacy, run a simulation with a custom SIS vaccine at 100% routine coverage and check whether the disease has been eradicated (no new infections in the final timestep). Return results for each efficacy value.

### Background
Finding the minimum vaccine efficacy needed to eliminate a disease is a key question in public health. For an SIS model (where recovered agents become susceptible again), ongoing vaccination must reduce transmission enough that the disease cannot sustain itself. This is related to the concept of the basic reproduction number R0 — the vaccine must reduce the effective reproduction number below 1. By sweeping across efficacy values with 100% coverage, you can identify the approximate threshold. With beta=0.1, n_contacts=4, and dur_inf=10, R0 is approximately 4, so the minimum efficacy threshold is around 0.5.

### Dependencies
- starsim

### Function Header
```python
def sweep_sis_vaccine_efficacy(efficacies: list[float], n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_start_year: int = 2015) -> dict[float, dict]:
```

### Docstring
```
Sweep vaccine efficacy values and check for SIS disease eradication.

For each efficacy value, define a custom sis_vaccine class (subclassing ss.Vx)
that reduces rel_sus, deliver it via ss.routine_vx with 100% coverage, and run
an SIS simulation from 2000 to 2050 with demographics. Check whether the disease
is eradicated by examining whether there are zero new infections in the final
timestep.

Args:
    efficacies: List of vaccine efficacy values to test (0 to 1).
    n_agents: Number of agents to simulate.
    n_contacts: Average number of contacts per agent.
    beta: Probability of transmission between contacts.
    dur_inf: Duration of infection in years.
    vx_start_year: Year to begin routine vaccination.

Returns:
    Dictionary mapping each efficacy value to a dict containing:
        - 'cum_infections': cumulative infections at end of simulation
        - 'eradicated': True if new infections in the final timestep is zero
```

### Test Cases

#### Results should contain an entry for each efficacy value
```python
results = sweep_sis_vaccine_efficacy([0.1, 0.5, 0.9])
assert set(results.keys()) == {0.1, 0.5, 0.9}, 'Should have results for all efficacy values'
```

#### Each result should contain cum_infections and eradicated
```python
results = sweep_sis_vaccine_efficacy([0.5])
assert 'cum_infections' in results[0.5], 'Should contain cum_infections'
assert 'eradicated' in results[0.5], 'Should contain eradicated'
```

#### High efficacy (0.9) with 100% coverage should eradicate the disease
```python
results = sweep_sis_vaccine_efficacy([0.9])
assert results[0.9]['eradicated'] is True, 'Efficacy of 0.9 should eradicate the disease'
```

#### Higher efficacy should result in fewer or equal cumulative infections
```python
results = sweep_sis_vaccine_efficacy([0.1, 0.9])
assert results[0.9]['cum_infections'] <= results[0.1]['cum_infections'], 'Higher efficacy should produce fewer infections'
```

### Gold Solution
```python
def sweep_sis_vaccine_efficacy(efficacies: list[float], n_agents: int = 5_000, n_contacts: int = 4, beta: float = 0.1, dur_inf: float = 10, vx_start_year: int = 2015) -> dict[float, dict]:
    import starsim as ss

    class sis_vaccine(ss.Vx):
        def __init__(self, efficacy=1.0, **kwargs):
            super().__init__()
            self.define_pars(efficacy=efficacy)
            self.update_pars(**kwargs)

        def administer(self, people, uids):
            people.sis.rel_sus[uids] *= 1 - self.pars.efficacy

    results = {}
    for eff in efficacies:
        my_vaccine = sis_vaccine(efficacy=eff)
        my_intv = ss.routine_vx(start_year=vx_start_year, prob=1.0, product=my_vaccine)
        pars = dict(
            n_agents=n_agents,
            birth_rate=20,
            death_rate=15,
            networks=dict(type='random', n_contacts=n_contacts),
            diseases=dict(type='sis', dur_inf=dur_inf, beta=beta),
            start=2000,
            stop=2050,
        )
        sim = ss.Sim(pars=pars, interventions=my_intv)
        sim.run()
        results[eff] = {
            'cum_infections': float(sim.results.sis.cum_infections[-1]),
            'eradicated': float(sim.results.sis.new_infections[-1]) == 0,
        }
    return results
```
